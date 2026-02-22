"""数据分析 API 模块。

提供智能查询和统计分析接口：
- POST /api/v1/analysis/query: RAG 智能查询
- GET /api/v1/analysis/statistics: 统计数据
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.models.talent import TalentInfo
from src.schemas.common import APIResponse
from src.storage.chroma_client import chroma_client

router = APIRouter(prefix="/analysis", tags=["数据分析"])


class QueryRequest(BaseModel):
    """RAG 查询请求模型。

    Attributes:
        query: 查询文本
        top_k: 返回结果数量
        filters: 元数据过滤条件
    """

    query: str = Field(..., min_length=1, max_length=500, description="查询文本")
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数量")
    filters: dict[str, Any] | None = Field(default=None, description="元数据过滤条件")


class QueryResult(BaseModel):
    """查询结果模型。

    Attributes:
        id: 文档 ID
        content: 文档内容
        metadata: 元数据
        distance: 相似度距离
    """

    id: str = Field(..., description="文档 ID")
    content: str = Field(..., description="文档内容")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")
    distance: float | None = Field(default=None, description="相似度距离")


class StatisticsResponse(BaseModel):
    """统计数据响应模型。

    Attributes:
        total_talents: 人才总数
        by_screening_status: 按筛选状态统计
        by_workflow_status: 按工作流状态统计
        recent_7_days: 近 7 天新增数量
    """

    total_talents: int = Field(..., description="人才总数")
    by_screening_status: dict[str, int] = Field(
        default_factory=dict,
        description="按筛选状态统计",
    )
    by_workflow_status: dict[str, int] = Field(
        default_factory=dict,
        description="按工作流状态统计",
    )
    recent_7_days: int = Field(default=0, description="近 7 天新增数量")


@router.post(
    "/query",
    response_model=APIResponse[list[QueryResult]],
    summary="RAG 智能查询",
    description="基于向量相似度的人才简历智能查询",
)
async def rag_query(request: QueryRequest) -> APIResponse[list[QueryResult]]:
    """执行 RAG 智能查询。

    使用 ChromaDB 向量检索，返回与查询最相似的简历内容。

    Args:
        request: 查询请求参数

    Returns:
        APIResponse[list[QueryResult]]: 查询结果列表

    Raises:
        HTTPException: 查询失败时抛出
    """
    logger.info(f"执行 RAG 查询: query={request.query[:50]}..., top_k={request.top_k}")

    try:
        # 执行向量查询
        results = chroma_client.query(
            query_texts=[request.query],
            n_results=request.top_k,
            where=request.filters,
        )

        # 解析结果
        query_results: list[QueryResult] = []

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc_id in enumerate(ids):
            query_results.append(
                QueryResult(
                    id=doc_id,
                    content=documents[i] if i < len(documents) else "",
                    metadata=metadatas[i] if i < len(metadatas) else {},
                    distance=distances[i] if i < len(distances) else None,
                )
            )

        logger.success(f"RAG 查询完成: 返回 {len(query_results)} 条结果")

        return APIResponse(
            success=True,
            message="查询成功",
            data=query_results,
        )

    except Exception as e:
        logger.exception(f"RAG 查询失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {e}",
        ) from None


@router.get(
    "/statistics",
    response_model=APIResponse[StatisticsResponse],
    summary="获取统计数据",
    description="获取人才库统计数据，包括总数、状态分布等",
)
async def get_statistics(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> APIResponse[StatisticsResponse]:
    """获取人才库统计数据。

    统计人才总数、各状态数量、近 7 天新增等数据。

    Args:
        session: 数据库会话

    Returns:
        APIResponse[StatisticsResponse]: 统计数据响应

    Raises:
        HTTPException: 查询失败时抛出
    """
    logger.info("获取统计数据")

    try:
        # 获取总数
        total_result = await session.execute(select(func.count()).select_from(TalentInfo))
        total_talents = total_result.scalar() or 0

        # 按筛选状态统计
        screening_stats = await session.execute(
            select(
                TalentInfo.screening_status,
                func.count().label("count"),
            ).group_by(TalentInfo.screening_status)
        )
        by_screening_status: dict[str, int] = {}
        for row in screening_stats:
            key = row.screening_status.value if row.screening_status else "unknown"
            count_val = getattr(row, "count", 0)
            by_screening_status[key] = int(count_val)

        # 按工作流状态统计
        workflow_stats = await session.execute(
            select(
                TalentInfo.workflow_status,
                func.count().label("count"),
            ).group_by(TalentInfo.workflow_status)
        )
        by_workflow_status: dict[str, int] = {}
        for row in workflow_stats:
            key = row.workflow_status.value if row.workflow_status else "unknown"
            count_val = getattr(row, "count", 0)
            by_workflow_status[key] = int(count_val)

        # 近 7 天新增
        from datetime import datetime, timedelta

        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_result = await session.execute(
            select(func.count().label("count")).where(TalentInfo.created_at >= seven_days_ago)
        )
        recent_7_days = recent_result.scalar() or 0

        # 构建响应
        statistics = StatisticsResponse(
            total_talents=total_talents,
            by_screening_status=by_screening_status,
            by_workflow_status=by_workflow_status,
            recent_7_days=recent_7_days,
        )

        logger.success(f"统计数据获取成功: total={total_talents}")

        return APIResponse(
            success=True,
            message="获取成功",
            data=statistics,
        )

    except Exception as e:
        logger.exception(f"获取统计数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计数据失败: {e}",
        ) from None


__all__ = ["router"]
