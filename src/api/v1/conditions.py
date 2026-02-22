"""筛选条件 CRUD API 模块。

提供筛选条件的增删改查接口：
- POST /api/v1/conditions: 新增筛选条件
- PUT /api/v1/conditions/{id}: 修改筛选条件
- DELETE /api/v1/conditions/{id}: 逻辑删除
- GET /api/v1/conditions: 分页查询
"""

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.models.condition import ScreeningCondition, StatusEnum
from src.schemas.common import APIResponse, PaginatedResponse
from src.schemas.condition import (
    ConditionConfig,
    ConditionCreate,
    ConditionResponse,
    ConditionUpdate,
    NLParseRequest,
    NLParseResponse,
)
from src.services.nlp_parser import nlp_parser

router = APIRouter(prefix="/conditions", tags=["筛选条件管理"])


def _map_to_response(condition: ScreeningCondition) -> ConditionResponse:
    """将数据库模型映射为响应模型。

    Args:
        condition: 数据库模型实例

    Returns:
        ConditionResponse: 响应模型实例
    """
    return ConditionResponse(
        id=condition.id,
        name=condition.name,
        description=condition.description or "",
        config=ConditionConfig(**condition.conditions),
        is_active=(condition.status == StatusEnum.ACTIVE),
        created_at=condition.created_at,
        updated_at=condition.updated_at,
    )


@router.post(
    "",
    response_model=APIResponse[ConditionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="新增筛选条件",
    description="创建一个新的筛选条件配置",
)
async def create_condition(
    data: ConditionCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> APIResponse[ConditionResponse]:
    """新增筛选条件。

    Args:
        data: 创建请求数据
        session: 数据库会话

    Returns:
        APIResponse[ConditionResponse]: 包含创建结果的响应

    Raises:
        HTTPException: 数据库操作失败时抛出
    """
    logger.info(f"创建筛选条件: name={data.name}")

    try:
        # 构建数据库模型
        condition = ScreeningCondition(
            name=data.name,
            description=data.description or "",
            conditions=data.config.model_dump(),
            status=StatusEnum.ACTIVE if data.is_active else StatusEnum.INACTIVE,
        )

        session.add(condition)
        await session.flush()
        await session.refresh(condition)

        logger.success(f"筛选条件创建成功: id={condition.id}")

        return APIResponse(
            success=True,
            message="筛选条件创建成功",
            data=_map_to_response(condition),
        )

    except Exception as e:
        logger.exception(f"创建筛选条件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建筛选条件失败: {e}",
        ) from None


@router.put(
    "/{condition_id}",
    response_model=APIResponse[ConditionResponse],
    summary="修改筛选条件",
    description="更新指定 ID 的筛选条件配置",
)
async def update_condition(
    condition_id: str,
    data: ConditionUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> APIResponse[ConditionResponse]:
    """修改筛选条件。

    Args:
        condition_id: 条件 ID
        data: 更新请求数据
        session: 数据库会话

    Returns:
        APIResponse[ConditionResponse]: 包含更新结果的响应

    Raises:
        HTTPException: 条件不存在或操作失败时抛出
    """
    logger.info(f"更新筛选条件: id={condition_id}")

    try:
        # 查询条件
        result = await session.execute(
            select(ScreeningCondition).where(
                ScreeningCondition.id == condition_id,
                ScreeningCondition.status != StatusEnum.DELETED,
            )
        )
        condition = result.scalar_one_or_none()

        if condition is None:
            logger.warning(f"筛选条件不存在: id={condition_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="筛选条件不存在",
            )

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data:
            condition.name = update_data["name"]
        if "description" in update_data:
            condition.description = update_data["description"] or ""
        if "config" in update_data:
            # update_data["config"] 已经是字典格式
            condition.conditions = update_data["config"]
        if "is_active" in update_data:
            condition.status = (
                StatusEnum.ACTIVE if update_data["is_active"] else StatusEnum.INACTIVE
            )

        await session.flush()
        await session.refresh(condition)

        logger.success(f"筛选条件更新成功: id={condition_id}")

        return APIResponse(
            success=True,
            message="筛选条件更新成功",
            data=_map_to_response(condition),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"更新筛选条件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新筛选条件失败: {e}",
        ) from None


@router.delete(
    "/{condition_id}",
    response_model=APIResponse[None],
    summary="逻辑删除筛选条件",
    description="将指定 ID 的筛选条件标记为已删除状态",
)
async def delete_condition(
    condition_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> APIResponse[None]:
    """逻辑删除筛选条件。

    Args:
        condition_id: 条件 ID
        session: 数据库会话

    Returns:
        APIResponse[None]: 操作结果响应

    Raises:
        HTTPException: 条件不存在或操作失败时抛出
    """
    logger.info(f"删除筛选条件: id={condition_id}")

    try:
        # 查询条件
        result = await session.execute(
            select(ScreeningCondition).where(
                ScreeningCondition.id == condition_id,
                ScreeningCondition.status != StatusEnum.DELETED,
            )
        )
        condition = result.scalar_one_or_none()

        if condition is None:
            logger.warning(f"筛选条件不存在: id={condition_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="筛选条件不存在",
            )

        # 逻辑删除
        condition.status = StatusEnum.DELETED
        await session.flush()

        logger.success(f"筛选条件删除成功: id={condition_id}")

        return APIResponse(
            success=True,
            message="筛选条件删除成功",
            data=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"删除筛选条件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除筛选条件失败: {e}",
        ) from None


@router.get(
    "",
    response_model=APIResponse[PaginatedResponse[ConditionResponse]],
    summary="分页查询筛选条件",
    description="支持按名称模糊搜索、状态筛选的分页查询",
)
async def list_conditions(
    session: Annotated[AsyncSession, Depends(get_session)],
    name: Annotated[str | None, Query(description="条件名称（模糊匹配）")] = None,
    statuses: Annotated[
        list[StatusEnum] | None,
        Query(description="状态列表（可多选）"),
    ] = None,
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 10,
) -> APIResponse[PaginatedResponse[ConditionResponse]]:
    """分页查询筛选条件。

    支持按名称模糊匹配和状态筛选，默认排除已删除状态。

    Args:
        session: 数据库会话
        name: 条件名称（模糊匹配）
        statuses: 状态列表（可多选）
        page: 页码（从 1 开始）
        page_size: 每页数量

    Returns:
        APIResponse[PaginatedResponse[ConditionResponse]]: 分页数据响应
    """
    logger.info(
        f"查询筛选条件: name={name}, statuses={statuses}, page={page}, page_size={page_size}"
    )

    try:
        # 构建基础查询条件
        base_conditions = [ScreeningCondition.status != StatusEnum.DELETED]

        # 名称模糊匹配
        if name:
            base_conditions.append(ScreeningCondition.name.ilike(f"%{name}%"))

        # 状态筛选
        if statuses:
            base_conditions.append(ScreeningCondition.status.in_(statuses))

        # 查询总数
        count_query = select(func.count()).select_from(ScreeningCondition).where(*base_conditions)
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # 计算总页数
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        # 分页查询
        offset = (page - 1) * page_size
        query = (
            select(ScreeningCondition)
            .where(*base_conditions)
            .order_by(ScreeningCondition.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(query)
        conditions = result.scalars().all()

        # 转换为响应模型
        items = [_map_to_response(c) for c in conditions]

        logger.success(f"查询筛选条件成功: total={total}, page={page}")

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
        logger.exception(f"查询筛选条件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询筛选条件失败: {e}",
        ) from None


@router.post(
    "/parse-natural-language",
    response_model=APIResponse[NLParseResponse],
    summary="自然语言解析",
    description="将自然语言描述转换为结构化筛选条件",
)
async def parse_natural_language(
    data: NLParseRequest,
) -> APIResponse[NLParseResponse]:
    """解析自然语言描述。

    使用 LLM 将用户的自然语言描述转换为结构化的筛选条件配置。

    Args:
        data: 解析请求数据

    Returns:
        APIResponse[NLParseResponse]: 包含解析结果的响应

    Raises:
        HTTPException: 解析失败时抛出
    """
    logger.info(f"解析自然语言: text={data.text[:50]}...")

    try:
        result = await nlp_parser.parse(data.text)

        logger.success(f"自然语言解析成功: name={result.name}")

        return APIResponse(
            success=True,
            message="解析成功",
            data=result,
        )

    except ValueError as e:
        logger.warning(f"自然语言解析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        logger.exception(f"自然语言解析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解析失败: {e}",
        ) from None


__all__ = ["router"]
