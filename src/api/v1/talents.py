"""人才管理 API 模块。

提供人才信息的上传、查询、向量化等接口：
- POST /api/v1/talents/upload-screen: 上传简历并执行智能筛选
- GET /api/v1/talents: 分页查询人才列表
- GET /api/v1/talents/{id}: 获取人才详情
- POST /api/v1/talents/{id}/vectorize: 向量化指定人才
- POST /api/v1/talents/batch-vectorize: 批量向量化
"""

from datetime import date, datetime
import math
import os
from pathlib import Path
import tempfile
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.core.security import decrypt_data
from src.models.talent import ScreeningStatusEnum, TalentInfo, WorkflowStatusEnum
from src.schemas.common import APIResponse, PaginatedResponse
from src.storage.chroma_client import chroma_client
from src.workflows.resume_workflow import run_resume_workflow

router = APIRouter(prefix="/talents", tags=["人才管理"])

# 允许的文件类型
ALLOWED_FILE_TYPES = {"pdf", "docx", "doc"}
# 最大文件大小（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024


class TalentDetailResponse(BaseModel):
    """人才详情响应模型。

    用于返回人才信息，敏感信息解密后返回。

    Attributes:
        id: 人才记录ID（UUID字符串）。
        name: 候选人姓名。
        phone: 联系电话（已解密）。
        email: 电子邮箱（已解密）。
        education_level: 学历层次。
        school: 毕业院校。
        major: 专业。
        graduation_date: 毕业日期。
        skills: 技能列表。
        work_years: 工作年限。
        photo_url: 照片URL。
        condition_id: 筛选条件ID。
        workflow_status: 工作流状态。
        screening_status: 筛选状态。
        screening_date: 筛选日期。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    id: str = Field(..., description="人才记录ID")
    name: str = Field(..., description="候选人姓名")
    phone: str = Field(default="", description="联系电话（已解密）")
    email: str = Field(default="", description="电子邮箱（已解密）")
    education_level: str = Field(default="", description="学历层次")
    school: str = Field(default="", description="毕业院校")
    major: str = Field(default="", description="专业")
    graduation_date: date | None = Field(default=None, description="毕业日期")
    skills: list[str] = Field(default_factory=list, description="技能列表")
    work_years: int = Field(default=0, description="工作年限")
    photo_url: str = Field(default="", description="照片URL")
    condition_id: str | None = Field(default=None, description="筛选条件ID")
    workflow_status: str = Field(default="", description="工作流状态")
    screening_status: str | None = Field(default=None, description="筛选状态")
    screening_date: datetime | None = Field(default=None, description="筛选日期")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


def _decrypt_sensitive_fields(talent: TalentInfo) -> dict[str, Any]:
    """解密人才敏感信息并转换为字典。

    Args:
        talent: 人才信息模型实例

    Returns:
        dict[str, Any]: 包含解密后敏感信息的字典
    """
    data = talent.to_dict(include_sensitive=False)
    # 解密敏感信息
    if talent.phone:
        try:
            data["phone"] = decrypt_data(talent.phone)
        except ValueError:
            data["phone"] = talent.phone  # 解密失败保留原值
    if talent.email:
        try:
            data["email"] = decrypt_data(talent.email)
        except ValueError:
            data["email"] = talent.email
    return data


def _map_to_response(talent: TalentInfo) -> TalentDetailResponse:
    """将数据库模型映射为响应模型。

    Args:
        talent: 数据库模型实例

    Returns:
        TalentDetailResponse: 响应模型实例
    """
    data = _decrypt_sensitive_fields(talent)
    return TalentDetailResponse(
        id=talent.id,
        name=talent.name,
        phone=data.get("phone", ""),
        email=data.get("email", ""),
        education_level=talent.education_level or "",
        school=talent.school or "",
        major=talent.major or "",
        graduation_date=talent.graduation_date,
        skills=talent.skills or [],
        work_years=talent.work_years or 0,
        photo_url=talent.photo_url or "",
        condition_id=talent.condition_id,
        workflow_status=talent.workflow_status.value,
        screening_status=talent.screening_status.value if talent.screening_status else None,
        screening_date=talent.screening_date,
        created_at=talent.created_at,
        updated_at=talent.updated_at,
    )


def _build_condition_filters(config: dict[str, Any]) -> list:
    """根据筛选条件配置构建 SQLAlchemy 过滤条件。

    Args:
        config: 筛选条件配置字典

    Returns:
        list: SQLAlchemy 过滤条件列表
    """
    filters = []

    education_order = {"doctor": 5, "master": 4, "bachelor": 3, "college": 2, "high_school": 1}
    education_cn_map = {
        "doctor": "博士",
        "master": "硕士",
        "bachelor": "本科",
        "college": "大专",
        "high_school": "高中及以下",
    }

    education_level = config.get("education_level")
    if education_level:
        min_level = education_order.get(education_level, 0)
        valid_levels_en = [k for k, v in education_order.items() if v >= min_level]
        valid_levels_cn = [education_cn_map.get(k, k) for k in valid_levels_en]
        valid_levels = valid_levels_en + valid_levels_cn
        filters.append(TalentInfo.education_level.in_(valid_levels))

    experience_years = config.get("experience_years")
    if experience_years is not None:
        filters.append(TalentInfo.work_years >= experience_years)

    experience_years_max = config.get("experience_years_max")
    if experience_years_max is not None:
        filters.append(TalentInfo.work_years <= experience_years_max)

    skills = config.get("skills", [])
    if skills:
        for skill in skills:
            filters.append(TalentInfo.skills.contains([skill]))

    major = config.get("major", [])
    if major:
        major_conditions = [TalentInfo.major.ilike(f"%{m}%") for m in major]
        if major_conditions:
            filters.append(or_(*major_conditions))

    school_tier = config.get("school_tier")
    if school_tier:
        tier_schools = {
            "top": ["985", "C9", "清华", "北大", "复旦", "上交", "浙大", "中科大", "南大", "西交", "哈工大"],
            "key": ["211", "重点"],
            "overseas": ["大学", "University", "学院", "College"],
        }
        tier_keywords = tier_schools.get(school_tier, [])
        if tier_keywords:
            school_conditions = [TalentInfo.school.ilike(f"%{kw}%") for kw in tier_keywords]
            if school_conditions:
                filters.append(or_(*school_conditions))

    return filters


@router.post(
    "/upload-screen",
    response_model=APIResponse[dict[str, Any]],
    status_code=status.HTTP_201_CREATED,
    summary="上传简历并执行智能筛选",
    description="上传简历文件，执行 LangGraph 工作流进行智能筛选",
)
async def upload_and_screen(
    file: Annotated[UploadFile, File(description="简历文件（PDF/DOCX）")],
    condition_id: Annotated[str | None, Query(description="筛选条件ID")] = None,
) -> APIResponse[dict[str, Any]]:
    """上传简历并执行智能筛选。

    Args:
        file: 上传的简历文件
        condition_id: 筛选条件 ID

    Returns:
        APIResponse[dict[str, Any]]: 包含筛选结果的响应

    Raises:
        HTTPException: 文件验证失败或工作流执行失败
    """
    logger.info(f"收到简历上传请求: filename={file.filename}, condition_id={condition_id}")

    # 验证文件类型
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空",
        )

    file_ext = file.filename.rsplit(".", 1)[-1].lower()
    if file_ext not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file_ext}，仅支持 PDF 和 DOCX",
        )

    # 读取文件内容
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制（最大 10MB），当前: {len(content) / 1024 / 1024:.2f}MB",
        )

    # 计算内容哈希用于去重
    import hashlib

    content_hash = hashlib.sha256(content).hexdigest()
    logger.info(f"简历内容哈希: {content_hash[:16]}...")

    # 检查是否已存在相同内容的简历
    from src.models import async_session_factory

    async with async_session_factory() as session:
        existing_talent = await session.execute(
            select(TalentInfo).where(TalentInfo.content_hash == content_hash)
        )
        existing = existing_talent.scalar_one_or_none()
        if existing:
            logger.warning(f"检测到重复简历: talent_id={existing.id}, name={existing.name}")
            return APIResponse(
                success=False,
                message="该简历已存在，跳过重复上传",
                data={
                    "talent_id": existing.id,
                    "name": existing.name,
                    "is_duplicate": True,
                    "existing_screening_status": existing.screening_status.value
                    if existing.screening_status
                    else None,
                },
            )

    # 保存临时文件
    temp_fd, temp_path = tempfile.mkstemp(suffix=f".{file_ext}")
    os.close(temp_fd)  # 关闭文件描述符
    try:
        Path(temp_path).write_bytes(content)

        # 执行工作流
        result = await run_resume_workflow(
            file_path=temp_path,
            condition_id=condition_id,
            content_hash=content_hash,
        )

        if result.get("error_message"):
            logger.error(f"工作流执行失败: {result['error_message']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"简历处理失败: {result['error_message']}",
            )

        logger.success(f"简历处理成功: talent_id={result.get('talent_id')}")

        return APIResponse(
            success=True,
            message="简历处理完成",
            data={
                "talent_id": result.get("talent_id"),
                "is_qualified": result.get("is_qualified"),
                "qualification_reason": result.get("qualification_reason"),
                "workflow_status": result.get("workflow_status"),
                "processing_time": result.get("total_processing_time"),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"简历处理异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"简历处理异常: {e}",
        ) from None
    finally:
        # 清理临时文件
        Path(temp_path).unlink(missing_ok=True)


@router.post(
    "/batch-upload",
    response_model=APIResponse[dict[str, Any]],
    status_code=status.HTTP_201_CREATED,
    summary="批量上传简历",
    description="批量上传多个简历文件，后台处理并返回任务 ID",
)
async def batch_upload(
    files: Annotated[list[UploadFile], File(description="简历文件列表")],
    condition_id: Annotated[str | None, Query(description="筛选条件ID")] = None,
) -> APIResponse[dict[str, Any]]:
    """批量上传简历。

    Args:
        files: 上传的简历文件列表
        condition_id: 筛选条件 ID

    Returns:
        APIResponse[dict[str, Any]]: 包含任务 ID 的响应

    Raises:
        HTTPException: 文件验证失败
    """
    from src.core.tasks import task_manager
    from src.workflows.resume_workflow import run_resume_workflow

    logger.info(f"收到批量上传请求: file_count={len(files)}, condition_id={condition_id}")

    # 验证文件数量
    if len(files) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="最多支持同时上传 50 个文件",
        )

    # 验证每个文件并读取内容到内存
    file_data_list: list[dict[str, Any]] = []
    for file in files:
        if not file.filename:
            continue
        file_ext = file.filename.rsplit(".", 1)[-1].lower()
        if file_ext not in ALLOWED_FILE_TYPES:
            continue

        # 读取文件内容到内存
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            continue

        file_data_list.append(
            {
                "filename": file.filename,
                "content": content,
                "ext": file_ext,
            }
        )

    if not file_data_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有有效的简历文件",
        )

    # 创建任务
    task = task_manager.create_task(
        name=f"批量上传简历 ({len(file_data_list)} 个文件)",
        metadata={"condition_id": condition_id, "file_count": len(file_data_list)},
    )

    # 定义批量处理函数
    async def process_batch() -> dict[str, Any]:
        """批量处理简历。"""
        from src.models import async_session_factory

        results = []
        success_count = 0
        failed_count = 0
        duplicate_count = 0

        for idx, file_data in enumerate(file_data_list):
            filename = file_data["filename"]
            content = file_data["content"]
            file_ext = file_data["ext"]

            try:
                # 计算内容哈希
                import hashlib

                content_hash = hashlib.sha256(content).hexdigest()

                # 检查重复
                async with async_session_factory() as session:
                    existing_talent = await session.execute(
                        select(TalentInfo).where(TalentInfo.content_hash == content_hash)
                    )
                    existing = existing_talent.scalar_one_or_none()
                    if existing:
                        results.append(
                            {
                                "filename": filename,
                                "success": False,
                                "error": "简历已存在",
                                "is_duplicate": True,
                                "talent_id": existing.id,
                            }
                        )
                        duplicate_count += 1
                        continue

                # 保存临时文件
                temp_fd, temp_path = tempfile.mkstemp(suffix=f".{file_ext}")
                os.close(temp_fd)
                try:
                    Path(temp_path).write_bytes(content)

                    # 执行工作流
                    result = await run_resume_workflow(
                        file_path=temp_path,
                        condition_id=condition_id,
                        content_hash=content_hash,
                    )

                    if result.get("error_message"):
                        results.append(
                            {
                                "filename": filename,
                                "success": False,
                                "error": result["error_message"],
                            }
                        )
                        failed_count += 1
                    else:
                        results.append(
                            {
                                "filename": filename,
                                "success": True,
                                "talent_id": result.get("talent_id"),
                                "is_qualified": result.get("is_qualified"),
                            }
                        )
                        success_count += 1

                finally:
                    Path(temp_path).unlink(missing_ok=True)

            except Exception as e:
                logger.exception(f"处理文件失败: {filename}, {e}")
                results.append(
                    {
                        "filename": filename,
                        "success": False,
                        "error": str(e),
                    }
                )
                failed_count += 1

            # 更新进度
            await task_manager.update_progress(
                task.id,
                idx + 1,
                len(file_data_list),
                f"正在处理: {filename}",
            )

        return {
            "total": len(file_data_list),
            "success": success_count,
            "failed": failed_count,
            "duplicate": duplicate_count,
            "results": results,
        }

    # 启动后台任务
    await task_manager.start_task(task.id, process_batch)

    return APIResponse(
        success=True,
        message="批量上传任务已创建",
        data={
            "task_id": task.id,
            "file_count": len(file_data_list),
        },
    )


@router.get(
    "/tasks",
    response_model=APIResponse[list[dict[str, Any]]],
    summary="获取任务列表",
    description="获取后台任务列表",
)
async def list_tasks(
    status: Annotated[str | None, Query(description="过滤状态")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="返回数量限制")] = 20,
) -> APIResponse[list[dict[str, Any]]]:
    """获取任务列表。

    Args:
        status: 过滤状态
        limit: 返回数量限制

    Returns:
        APIResponse[list[dict[str, Any]]]: 任务列表响应
    """
    from src.core.tasks import TaskStatusEnum, task_manager

    status_enum = None
    if status:
        try:
            status_enum = TaskStatusEnum(status)
        except ValueError:
            pass

    tasks = task_manager.list_tasks(status=status_enum, limit=limit)
    return APIResponse(
        success=True,
        message="获取成功",
        data=[t.to_dict() for t in tasks],
    )


@router.get(
    "/tasks/{task_id}",
    response_model=APIResponse[dict[str, Any]],
    summary="获取任务状态",
    description="获取后台任务的状态和进度",
)
async def get_task_status(task_id: str) -> APIResponse[dict[str, Any]]:
    """获取任务状态。

    Args:
        task_id: 任务 ID

    Returns:
        APIResponse[dict[str, Any]]: 任务状态响应

    Raises:
        HTTPException: 任务不存在
    """
    from src.core.tasks import task_manager

    task = task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )

    return APIResponse(
        success=True,
        message="获取成功",
        data=task.to_dict(),
    )


@router.post(
    "/tasks/{task_id}/cancel",
    response_model=APIResponse[dict[str, Any]],
    summary="取消任务",
    description="取消正在执行的后台任务",
)
async def cancel_task(task_id: str) -> APIResponse[dict[str, Any]]:
    """取消任务。

    Args:
        task_id: 任务 ID

    Returns:
        APIResponse[dict[str, Any]]: 取消结果响应

    Raises:
        HTTPException: 任务不存在或无法取消
    """
    from src.core.tasks import task_manager

    task = task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )

    if task_manager.cancel_task(task_id):
        return APIResponse(
            success=True,
            message="任务已取消",
            data={"task_id": task_id},
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法取消任务（可能已完成或已取消）",
        )


@router.get(
    "",
    response_model=APIResponse[PaginatedResponse[TalentDetailResponse]],
    summary="分页查询人才列表",
    description="支持按姓名、专业、院校、选拔日期、筛选条件等条件筛选",
)
async def list_talents(
    session: Annotated[AsyncSession, Depends(get_session)],
    name: Annotated[str | None, Query(description="姓名（模糊匹配）")] = None,
    major: Annotated[str | None, Query(description="专业（模糊匹配）")] = None,
    school: Annotated[str | None, Query(description="院校（模糊匹配）")] = None,
    screening_date_start: Annotated[
        str | None, Query(description="选拔日期起始（YYYY-MM-DD）")
    ] = None,
    screening_date_end: Annotated[
        str | None, Query(description="选拔日期截止（YYYY-MM-DD）")
    ] = None,
    screening_status: Annotated[ScreeningStatusEnum | None, Query(description="筛选状态")] = None,
    condition_id: Annotated[str | None, Query(description="筛选条件ID")] = None,
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 10,
) -> APIResponse[PaginatedResponse[TalentDetailResponse]]:
    """分页查询人才列表。

    Args:
        session: 数据库会话
        name: 姓名（模糊匹配）
        major: 专业（模糊匹配）
        school: 院校（模糊匹配）
        screening_date_start: 选拔日期起始
        screening_date_end: 选拔日期截止
        screening_status: 筛选状态
        condition_id: 筛选条件ID（按条件过滤人才）
        page: 页码（从 1 开始）
        page_size: 每页数量

    Returns:
        APIResponse[PaginatedResponse[TalentDetailResponse]]: 分页数据响应
    """
    logger.info(
        f"查询人才列表: name={name}, major={major}, school={school}, screening_status={screening_status}, condition_id={condition_id}, page={page}"
    )

    try:
        from src.models.condition import ScreeningCondition

        condition_config = None
        if condition_id:
            cond_result = await session.execute(
                select(ScreeningCondition).where(ScreeningCondition.id == condition_id)
            )
            condition_record = cond_result.scalar_one_or_none()
            if condition_record and condition_record.conditions:
                condition_config = condition_record.conditions

        conditions = [
            TalentInfo.workflow_status.in_(
                [WorkflowStatusEnum.COMPLETED, WorkflowStatusEnum.STORING]
            )
        ]

        if name:
            conditions.append(TalentInfo.name.ilike(f"%{name}%"))
        if major:
            conditions.append(TalentInfo.major.ilike(f"%{major}%"))
        if school:
            conditions.append(TalentInfo.school.ilike(f"%{school}%"))
        if screening_status:
            conditions.append(TalentInfo.screening_status == screening_status)
        if screening_date_start:
            conditions.append(TalentInfo.screening_date >= screening_date_start)
        if screening_date_end:
            conditions.append(TalentInfo.screening_date <= screening_date_end)

        if condition_config:
            cond_conditions = _build_condition_filters(condition_config)
            conditions.extend(cond_conditions)

        # 查询总数
        count_query = select(func.count()).select_from(TalentInfo).where(and_(*conditions))
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # 计算总页数
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        # 分页查询
        offset = (page - 1) * page_size
        query = (
            select(TalentInfo)
            .where(and_(*conditions))
            .order_by(TalentInfo.screening_date.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(query)
        talents = result.scalars().all()

        # 转换为响应模型
        items = [_map_to_response(t) for t in talents]

        logger.success(f"查询人才列表成功: total={total}, page={page}")

        return APIResponse(
            success=True,
            message="查询成功",
            data=PaginatedResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            ),
        )

    except Exception as e:
        logger.exception(f"查询人才列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询人才列表失败: {e}",
        ) from None


@router.get(
    "/{talent_id}",
    response_model=APIResponse[TalentDetailResponse],
    summary="获取人才详情",
    description="根据 ID 获取人才详细信息，敏感信息解密后返回",
)
async def get_talent(
    talent_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> APIResponse[TalentDetailResponse]:
    """获取人才详情。

    Args:
        talent_id: 人才 ID
        session: 数据库会话

    Returns:
        APIResponse[TalentDetailResponse]: 人才详情响应

    Raises:
        HTTPException: 人才不存在时抛出
    """
    logger.info(f"查询人才详情: id={talent_id}")

    try:
        result = await session.execute(select(TalentInfo).where(TalentInfo.id == talent_id))
        talent = result.scalar_one_or_none()

        if talent is None:
            logger.warning(f"人才不存在: id={talent_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="人才不存在",
            )

        logger.success(f"查询人才详情成功: id={talent_id}")

        return APIResponse(
            success=True,
            message="查询成功",
            data=_map_to_response(talent),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"查询人才详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询人才详情失败: {e}",
        ) from None


@router.get(
    "/{talent_id}/photo",
    summary="获取人才头像",
    description="从 MinIO 获取人才头像图片",
    responses={
        200: {"content": {"image/png": {}}},
        404: {"description": "头像不存在"},
    },
)
async def get_talent_photo(
    talent_id: str,
) -> StreamingResponse:
    """获取人才头像图片。

    Args:
        talent_id: 人才 ID

    Returns:
        StreamingResponse: 图片流响应

    Raises:
        HTTPException: 头像不存在时抛出
    """
    from io import BytesIO

    from src.storage.minio_client import MinIOClient

    logger.info(f"获取人才头像: talent_id={talent_id}")

    try:
        minio_client = MinIOClient()
        object_name = f"talents/{talent_id}/photo_1.png"
        image_data = minio_client.get_image(object_name)

        if image_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="头像不存在",
            )

        return StreamingResponse(
            BytesIO(image_data),
            media_type="image/png",
            headers={"Cache-Control": "max-age=86400"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取人才头像失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取人才头像失败: {e}",
        ) from None


@router.post(
    "/{talent_id}/vectorize",
    response_model=APIResponse[dict[str, Any]],
    summary="向量化指定人才",
    description="将指定人才的简历文本向量化存入 ChromaDB",
)
async def vectorize_talent(
    talent_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> APIResponse[dict[str, Any]]:
    """向量化指定人才。

    Args:
        talent_id: 人才 ID
        session: 数据库会话

    Returns:
        APIResponse[dict[str, Any]]: 向量化结果响应

    Raises:
        HTTPException: 人才不存在或向量化失败时抛出
    """
    logger.info(f"向量化人才: id={talent_id}")

    try:
        # 查询人才
        result = await session.execute(select(TalentInfo).where(TalentInfo.id == talent_id))
        talent = result.scalar_one_or_none()

        if talent is None:
            logger.warning(f"人才不存在: id={talent_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="人才不存在",
            )

        if not talent.resume_text:
            logger.warning(f"人才简历文本为空: id={talent_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="人才简历文本为空，无法向量化",
            )

        # 向量化存入 ChromaDB
        metadata = {
            "talent_id": talent.id,
            "name": talent.name,
            "school": talent.school or "",
            "major": talent.major or "",
            "education_level": talent.education_level or "",
            "work_years": talent.work_years or 0,
        }

        chroma_client.add_documents(
            ids=[talent.id],
            documents=[talent.resume_text],
            metadatas=[metadata],
        )

        logger.success(f"向量化人才成功: id={talent_id}")

        return APIResponse(
            success=True,
            message="向量化成功",
            data={
                "talent_id": talent_id,
                "vectorized": True,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"向量化人才失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"向量化人才失败: {e}",
        ) from None


@router.post(
    "/batch-vectorize",
    response_model=APIResponse[dict[str, Any]],
    summary="批量向量化人才",
    description="批量将符合条件的人才简历向量化存入 ChromaDB",
)
async def batch_vectorize(
    session: Annotated[AsyncSession, Depends(get_session)],
    screening_status: Annotated[
        ScreeningStatusEnum | None, Query(description="筛选状态（默认为 qualified）")
    ] = ScreeningStatusEnum.QUALIFIED,
    limit: Annotated[int, Query(ge=1, le=1000, description="批量处理数量上限")] = 100,
) -> APIResponse[dict[str, Any]]:
    """批量向量化人才。

    Args:
        session: 数据库会话
        screening_status: 筛选状态（默认为 qualified）
        limit: 批量处理数量上限

    Returns:
        APIResponse[dict[str, Any]]: 批量向量化结果响应
    """
    logger.info(f"批量向量化人才: screening_status={screening_status}, limit={limit}")

    try:
        # 查询符合条件的人才
        query = (
            select(TalentInfo)
            .where(
                TalentInfo.screening_status == screening_status,
                TalentInfo.resume_text != "",
                TalentInfo.resume_text.isnot(None),
            )
            .limit(limit)
        )

        result = await session.execute(query)
        talents = result.scalars().all()

        if not talents:
            logger.info("没有需要向量化的人才")
            return APIResponse(
                success=True,
                message="没有需要向量化的人才",
                data={"total": 0, "success": 0, "failed": 0},
            )

        # 批量向量化
        ids = []
        documents = []
        metadatas = []

        for talent in talents:
            if talent.resume_text:
                ids.append(talent.id)
                documents.append(talent.resume_text)
                metadatas.append(
                    {
                        "talent_id": talent.id,
                        "name": talent.name,
                        "school": talent.school or "",
                        "major": talent.major or "",
                        "education_level": talent.education_level or "",
                        "work_years": talent.work_years or 0,
                    }
                )

        if ids:
            chroma_client.add_documents(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )

        logger.success(f"批量向量化成功: total={len(ids)}")

        return APIResponse(
            success=True,
            message="批量向量化成功",
            data={
                "total": len(talents),
                "success": len(ids),
                "failed": len(talents) - len(ids),
            },
        )

    except Exception as e:
        logger.exception(f"批量向量化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量向量化失败: {e}",
        ) from None


__all__ = ["router"]
