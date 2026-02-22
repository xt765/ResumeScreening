"""入库节点模块。

负责将筛选结果存储到多个数据存储：
- MySQL: 人才基本信息存储
- MinIO: 简历图片存储
- ChromaDB: 简历向量存储（用于相似度检索）
"""

from datetime import datetime
import time
from typing import Any
from uuid import uuid4

from loguru import logger
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import DatabaseException, StorageException, WorkflowException
from src.core.security import encrypt_data
from src.models import ScreeningStatusEnum, TalentInfo, WorkflowStatusEnum
from src import models
from src.storage.chroma_client import chroma_client
from src.storage.minio_client import minio_client
from src.workflows.state import ResumeState


def _upload_images_to_minio(
    images: list[bytes],
    talent_id: str,
) -> list[str]:
    """上传图片到 MinIO。

    Args:
        images: 图片字节列表
        talent_id: 人才 ID

    Returns:
        list[str]: 图片 URL 列表

    Raises:
        StorageException: 上传失败
    """
    if not images:
        return []

    photo_urls: list[str] = []

    for idx, image_data in enumerate(images):
        try:
            # 生成对象名称
            object_name = f"talents/{talent_id}/photo_{idx + 1}.png"

            # 上传图片
            url = minio_client.upload_image(
                object_name=object_name,
                data=image_data,
                content_type="image/png",
            )
            photo_urls.append(url)

            logger.debug(f"图片上传成功: {object_name}")

        except Exception as e:
            logger.warning(f"图片上传失败，跳过: index={idx}, error={e}")
            continue

    logger.info(f"图片上传完成: total={len(images)}, success={len(photo_urls)}")
    return photo_urls


def _store_to_chromadb(
    talent_id: str,
    resume_text: str,
    candidate_info: dict[str, Any],
) -> bool:
    """存储简历向量到 ChromaDB。

    Args:
        talent_id: 人才 ID
        resume_text: 简历文本
        candidate_info: 候选人信息

    Returns:
        bool: 存储成功返回 True

    Raises:
        StorageException: 存储失败
    """
    if not resume_text:
        logger.warning("简历文本为空，跳过向量存储")
        return False

    try:
        is_qualified = candidate_info.get("is_qualified", False)
        metadata = {
            "name": candidate_info.get("name", ""),
            "school": candidate_info.get("school", ""),
            "major": candidate_info.get("major", ""),
            "education_level": candidate_info.get("education_level", ""),
            "work_years": candidate_info.get("work_years", 0),
            "skills": ",".join(candidate_info.get("skills", [])),
            "created_at": datetime.now().isoformat(),
            "is_deleted": False,
            "screening_status": "qualified" if is_qualified else "unqualified",
        }

        # 添加到 ChromaDB
        chroma_client.add_documents(
            ids=[talent_id],
            documents=[resume_text],
            metadatas=[metadata],
        )

        logger.info(f"向量存储成功: talent_id={talent_id}")
        return True

    except Exception as e:
        logger.exception(f"向量存储失败: {e}")
        raise StorageException(
            message=f"向量存储失败: {e}",
            storage_type="chromadb",
            details={"talent_id": talent_id, "error": str(e)},
        ) from e


async def _save_to_mysql(
    state: ResumeState,
    photo_urls: list[str],
    session: AsyncSession,
) -> str:
    """保存人才信息到 MySQL。

    Args:
        state: 工作流状态
        photo_urls: 照片 URL 列表
        session: 数据库会话

    Returns:
        str: 人才 ID

    Raises:
        DatabaseException: 数据库操作失败
    """
    try:
        candidate_info = state.candidate_info or {}

        # 加密敏感信息（使用统一的加密方法）
        encrypted_phone = encrypt_data(candidate_info.get("phone", ""))
        encrypted_email = encrypt_data(candidate_info.get("email", ""))

        # 解析毕业日期
        graduation_date = None
        if candidate_info.get("graduation_date"):
            date_str = candidate_info["graduation_date"]
            date_formats = ["%Y-%m-%d", "%Y-%m", "%Y/%m/%d", "%Y/%m", "%Y年%m月%d日", "%Y年%m月"]
            for fmt in date_formats:
                try:
                    graduation_date = datetime.strptime(date_str, fmt).date()
                    break
                except ValueError:
                    continue
            if graduation_date is None:
                logger.warning(f"毕业日期格式无法解析: {date_str}")

        # 创建人才记录
        talent = TalentInfo(
            id=str(uuid4()),
            name=candidate_info.get("name", "未知"),
            phone=encrypted_phone,
            email=encrypted_email,
            education_level=candidate_info.get("education_level", ""),
            school=candidate_info.get("school", ""),
            major=candidate_info.get("major", ""),
            graduation_date=graduation_date,
            skills=candidate_info.get("skills", []),
            work_years=candidate_info.get("work_years", 0),
            photo_url=photo_urls[0] if photo_urls else "",
            resume_text=state.text_content or "",
            content_hash=state.content_hash,
            condition_id=state.condition_id,
            workflow_status=WorkflowStatusEnum.STORING,
            screening_status=(
                ScreeningStatusEnum.QUALIFIED
                if state.is_qualified
                else ScreeningStatusEnum.DISQUALIFIED
            ),
            screening_date=datetime.now(),
        )

        session.add(talent)
        await session.flush()  # 获取 ID

        talent_id = talent.id
        logger.info(f"MySQL 存储成功: talent_id={talent_id}")

        return talent_id

    except Exception as e:
        logger.exception(f"MySQL 存储失败: {e}")
        raise DatabaseException(
            message=f"人才信息存储失败: {e}",
            operation="insert",
            table="talent_info",
            details={"error": str(e)},
        ) from e


async def store_node(state: ResumeState) -> dict[str, Any]:
    """入库节点。

    将筛选结果存储到多个数据存储：
    1. 保存人才信息到 MySQL（获取真实 ID）
    2. 上传图片到 MinIO（使用真实 ID）
    3. 更新 photo_url
    4. 存储向量到 ChromaDB

    Args:
        state: 当前工作流状态

    Returns:
        dict[str, Any]: 状态更新字典

    Raises:
        WorkflowException: 工作流执行失败
        DatabaseException: 数据库操作失败
        StorageException: 存储操作失败
    """
    start_time = time.time()
    logger.info("开始入库节点")

    try:
        # 验证必要数据
        if not state.candidate_info:
            raise WorkflowException(
                message="候选人信息为空，无法入库",
                node="store_node",
                state=state.workflow_status,
            )

        # 获取数据库会话
        if models.async_session_factory is None:
            raise WorkflowException(
                message="数据库未初始化",
                node="store_node",
                state=state.workflow_status,
            )

        async with models.async_session_factory() as session:
            # 1. 先保存到 MySQL（获取真实 ID）
            talent_id = await _save_to_mysql(state, [], session)

            # 2. 上传图片到 MinIO（使用真实 ID）
            photo_urls: list[str] = []
            if state.images:
                photo_urls = _upload_images_to_minio(state.images, talent_id)

            # 3. 更新 photo_url
            if photo_urls:
                await session.execute(
                    update(TalentInfo)
                    .where(TalentInfo.id == talent_id)
                    .values(photo_url=photo_urls[0])
                )

            # 4. 存储向量到 ChromaDB
            if state.text_content:
                _store_to_chromadb(
                    talent_id,
                    state.text_content,
                    state.candidate_info,
                )

            # 提交事务
            await session.commit()

        elapsed_time = int((time.time() - start_time) * 1000)
        logger.info(f"入库节点完成: talent_id={talent_id}, elapsed_time={elapsed_time}ms")

        return {
            "talent_id": talent_id,
            "photo_urls": photo_urls,
            "workflow_status": "stored",
        }

    except (WorkflowException, DatabaseException, StorageException):
        raise
    except Exception as e:
        logger.exception(f"入库节点执行失败: {e}")
        raise WorkflowException(
            message=f"入库节点执行失败: {e}",
            node="store_node",
            state=state.workflow_status,
            details={"error": str(e)},
        ) from e
