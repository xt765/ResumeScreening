"""数据分析 API 模块。

提供智能查询和统计分析接口：
- POST /api/v1/analysis/query: RAG 智能查询
- GET /api/v1/analysis/statistics: 统计数据
"""

from datetime import datetime, timedelta
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.core.exceptions import LLMException
from src.models.talent import TalentInfo
from src.schemas.common import APIResponse
from src.utils.rag_service import get_rag_service

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
        similarity_score: 相似度分数（0-1）
    """

    id: str = Field(..., description="文档 ID")
    content: str = Field(..., description="文档内容")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")
    distance: float | None = Field(default=None, description="相似度距离")
    similarity_score: float | None = Field(default=None, description="相似度分数（0-1）")


class RAGQueryResponse(BaseModel):
    """RAG 查询响应模型。

    Attributes:
        answer: LLM 生成的分析结论
        sources: 检索来源列表
        elapsed_time_ms: 查询耗时（毫秒）
        query_id: 查询 ID
    """

    answer: str = Field(..., description="LLM 生成的分析结论")
    sources: list[QueryResult] = Field(default_factory=list, description="检索来源")
    elapsed_time_ms: int = Field(..., description="查询耗时（毫秒）")
    query_id: str = Field(..., description="查询 ID")


class StatisticsResponse(BaseModel):
    """统计数据响应模型。

    Attributes:
        total_talents: 人才总数
        by_screening_status: 按筛选状态统计
        by_workflow_status: 按工作流状态统计
        recent_7_days: 近 7 天新增数量
        pass_rate: 通过率
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
    pass_rate: float = Field(default=0.0, description="通过率")


class SkillStat(BaseModel):
    """技能统计模型。

    Attributes:
        name: 技能名称
        count: 出现次数
    """

    name: str = Field(..., description="技能名称")
    count: int = Field(..., description="出现次数")


class SchoolStat(BaseModel):
    """学校统计模型。

    Attributes:
        name: 学校名称
        count: 出现次数
    """

    name: str = Field(..., description="学校名称")
    count: int = Field(..., description="出现次数")


class SimilarityBin(BaseModel):
    """相似度分布区间模型。

    Attributes:
        range: 区间范围
        count: 数量
    """

    range: str = Field(..., description="区间范围")
    count: int = Field(..., description="数量")


class QueryResultAnalytics(BaseModel):
    """查询结果分析统计模型。

    Attributes:
        total_count: 匹配总数
        avg_similarity: 平均相似度
        by_education: 按学历统计
        by_work_years_range: 按工作年限区间统计
        top_skills: 热门技能 Top10
        top_schools: 热门学校 Top5
        similarity_distribution: 相似度分布
    """

    total_count: int = Field(..., description="匹配总数")
    avg_similarity: float = Field(default=0.0, description="平均相似度")
    by_education: dict[str, int] = Field(default_factory=dict, description="按学历统计")
    by_work_years_range: dict[str, int] = Field(
        default_factory=dict, description="按工作年限区间统计"
    )
    top_skills: list[SkillStat] = Field(default_factory=list, description="热门技能 Top10")
    top_schools: list[SchoolStat] = Field(default_factory=list, description="热门学校 Top5")
    similarity_distribution: list[SimilarityBin] = Field(
        default_factory=list, description="相似度分布"
    )


class RAGAnalyticsResponse(BaseModel):
    """RAG 查询分析响应模型。

    Attributes:
        answer: LLM 生成的分析结论
        sources: 检索来源列表
        analytics: 查询结果分析统计
        elapsed_time_ms: 查询耗时（毫秒）
        query_id: 查询 ID
    """

    answer: str = Field(..., description="LLM 生成的分析结论")
    sources: list[QueryResult] = Field(default_factory=list, description="检索来源")
    analytics: QueryResultAnalytics = Field(..., description="查询结果分析统计")
    elapsed_time_ms: int = Field(..., description="查询耗时（毫秒）")
    query_id: str = Field(..., description="查询 ID")


def _calculate_similarity(distance: float | None) -> float | None:
    """计算相似度分数（0-1）。

    将距离转换为相似度，使用余弦相似度公式。

    Args:
        distance: 向量距离

    Returns:
        相似度分数（0-1），如果距离为 None 则返回 None
    """
    if distance is None:
        return None
    return max(0.0, min(1.0, 1 - distance))


def _analyze_query_results(sources: list[QueryResult]) -> QueryResultAnalytics:
    """分析查询结果，生成统计数据。

    Args:
        sources: 查询结果列表

    Returns:
        QueryResultAnalytics: 分析统计数据
    """
    if not sources:
        return QueryResultAnalytics(total_count=0)

    total_count = len(sources)

    similarity_scores = [s.similarity_score for s in sources if s.similarity_score is not None]
    avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0

    by_education: dict[str, int] = {}
    for source in sources:
        edu = source.metadata.get("education_level", "unknown")
        edu_label = _get_education_label(edu)
        by_education[edu_label] = by_education.get(edu_label, 0) + 1

    by_work_years_range: dict[str, int] = {"0-3年": 0, "3-5年": 0, "5-10年": 0, "10年以上": 0}
    for source in sources:
        work_years = source.metadata.get("work_years", 0)
        try:
            years = int(work_years) if work_years else 0
        except (ValueError, TypeError):
            years = 0
        if years < 3:
            by_work_years_range["0-3年"] += 1
        elif years < 5:
            by_work_years_range["3-5年"] += 1
        elif years < 10:
            by_work_years_range["5-10年"] += 1
        else:
            by_work_years_range["10年以上"] += 1

    skill_counts: dict[str, int] = {}
    for source in sources:
        skills_str = source.metadata.get("skills", "")
        if skills_str:
            skills = [s.strip() for s in skills_str.split(",") if s.strip()]
            for skill in skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1

    top_skills = [
        SkillStat(name=k, count=v)
        for k, v in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    school_counts: dict[str, int] = {}
    for source in sources:
        school = source.metadata.get("school", "")
        if school and school != "unknown":
            school_counts[school] = school_counts.get(school, 0) + 1

    top_schools = [
        SchoolStat(name=k, count=v)
        for k, v in sorted(school_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    similarity_bins = [
        SimilarityBin(range="0-0.5", count=0),
        SimilarityBin(range="0.5-0.7", count=0),
        SimilarityBin(range="0.7-0.85", count=0),
        SimilarityBin(range="0.85-1.0", count=0),
    ]
    for score in similarity_scores:
        if score < 0.5:
            similarity_bins[0].count += 1
        elif score < 0.7:
            similarity_bins[1].count += 1
        elif score < 0.85:
            similarity_bins[2].count += 1
        else:
            similarity_bins[3].count += 1

    return QueryResultAnalytics(
        total_count=total_count,
        avg_similarity=round(avg_similarity, 3),
        by_education=by_education,
        by_work_years_range=by_work_years_range,
        top_skills=top_skills,
        top_schools=top_schools,
        similarity_distribution=similarity_bins,
    )


def _get_education_label(level: str) -> str:
    """获取学历中文标签。

    Args:
        level: 学历英文标识

    Returns:
        学历中文标签
    """
    labels = {
        "doctor": "博士",
        "master": "硕士",
        "bachelor": "本科",
        "college": "大专",
        "high_school": "高中及以下",
        "unknown": "未知",
    }
    return labels.get(level, level if level else "未知")


@router.post(
    "/query",
    response_model=APIResponse[RAGQueryResponse],
    summary="RAG 智能查询",
    description="基于向量检索和 LLM 生成的人才简历智能问答",
)
async def rag_query(request: QueryRequest) -> APIResponse[RAGQueryResponse]:
    """执行 RAG 智能查询。

    结合向量检索和 LLM 生成，返回分析结论和来源。

    Args:
        request: 查询请求参数

    Returns:
        APIResponse[RAGQueryResponse]: 包含分析结论和来源的响应

    Raises:
        HTTPException: 查询失败时抛出
    """
    logger.info(f"执行 RAG 查询: query={request.query[:50]}..., top_k={request.top_k}")

    try:
        filters = request.filters or {}
        filters["is_deleted"] = False

        rag_service = get_rag_service()
        result = await rag_service.query(
            question=request.query,
            top_k=request.top_k,
            filters=filters,
        )

        sources = [
            QueryResult(
                id=doc["id"],
                content=doc["content"],
                metadata=doc["metadata"],
                distance=doc.get("distance"),
                similarity_score=_calculate_similarity(doc.get("distance")),
            )
            for doc in result["sources"]
        ]

        response = RAGQueryResponse(
            answer=result["answer"],
            sources=sources,
            elapsed_time_ms=result["elapsed_time_ms"],
            query_id=str(uuid4()),
        )

        logger.success(
            f"RAG 查询完成: sources={len(sources)}, elapsed={result['elapsed_time_ms']}ms"
        )

        return APIResponse(
            success=True,
            message="查询成功",
            data=response,
        )

    except LLMException as e:
        logger.error(f"LLM 调用失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM 服务暂不可用: {e}",
        ) from None
    except Exception as e:
        logger.exception(f"RAG 查询失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {e}",
        ) from None


@router.post(
    "/query-with-analytics",
    response_model=APIResponse[RAGAnalyticsResponse],
    summary="RAG 智能查询（含分析统计）",
    description="基于向量检索和 LLM 生成的人才简历智能问答，返回分析结论、来源和统计数据",
)
async def rag_query_with_analytics(
    request: QueryRequest,
) -> APIResponse[RAGAnalyticsResponse]:
    """执行 RAG 智能查询并返回分析统计数据。

    结合向量检索和 LLM 生成，返回分析结论、来源和统计数据。

    Args:
        request: 查询请求参数

    Returns:
        APIResponse[RAGAnalyticsResponse]: 包含分析结论、来源和统计数据的响应

    Raises:
        HTTPException: 查询失败时抛出
    """
    logger.info(f"执行 RAG 查询（含分析）: query={request.query[:50]}..., top_k={request.top_k}")

    try:
        filters = request.filters or {}
        filters["is_deleted"] = False

        rag_service = get_rag_service()
        result = await rag_service.query(
            question=request.query,
            top_k=request.top_k,
            filters=filters,
        )

        sources = [
            QueryResult(
                id=doc["id"],
                content=doc["content"],
                metadata=doc["metadata"],
                distance=doc.get("distance"),
                similarity_score=_calculate_similarity(doc.get("distance")),
            )
            for doc in result["sources"]
        ]

        analytics = _analyze_query_results(sources)

        response = RAGAnalyticsResponse(
            answer=result["answer"],
            sources=sources,
            analytics=analytics,
            elapsed_time_ms=result["elapsed_time_ms"],
            query_id=str(uuid4()),
        )

        logger.success(
            f"RAG 查询（含分析）完成: sources={len(sources)}, "
            f"avg_similarity={analytics.avg_similarity:.3f}, "
            f"elapsed={result['elapsed_time_ms']}ms"
        )

        return APIResponse(
            success=True,
            message="查询成功",
            data=response,
        )

    except LLMException as e:
        logger.error(f"LLM 调用失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM 服务暂不可用: {e}",
        ) from None
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
        total_result = await session.execute(
            select(func.count().label("count"))
            .select_from(TalentInfo)
            .where(TalentInfo.is_deleted.is_(False))
        )
        total_talents = total_result.scalar() or 0

        screening_stats = await session.execute(
            select(
                TalentInfo.screening_status,
                func.count().label("count"),
            )
            .where(TalentInfo.is_deleted.is_(False))
            .group_by(TalentInfo.screening_status)
        )
        by_screening_status: dict[str, int] = {}
        for row in screening_stats:
            key = row.screening_status.value if row.screening_status else "unknown"
            count_val = getattr(row, "count", 0)
            by_screening_status[key] = int(count_val)

        workflow_stats = await session.execute(
            select(
                TalentInfo.workflow_status,
                func.count().label("count"),
            )
            .where(TalentInfo.is_deleted.is_(False))
            .group_by(TalentInfo.workflow_status)
        )
        by_workflow_status: dict[str, int] = {}
        for row in workflow_stats:
            key = row.workflow_status.value if row.workflow_status else "unknown"
            count_val = getattr(row, "count", 0)
            by_workflow_status[key] = int(count_val)

        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_result = await session.execute(
            select(func.count().label("count"))
            .select_from(TalentInfo)
            .where(TalentInfo.is_deleted.is_(False), TalentInfo.created_at >= seven_days_ago)
        )
        recent_7_days = recent_result.scalar() or 0

        qualified_count = by_screening_status.get("qualified", 0)
        unqualified_count = by_screening_status.get("unqualified", 0)
        total_screened = qualified_count + unqualified_count
        pass_rate = (qualified_count / total_screened * 100) if total_screened > 0 else 0.0

        statistics = StatisticsResponse(
            total_talents=total_talents,
            by_screening_status=by_screening_status,
            by_workflow_status=by_workflow_status,
            recent_7_days=recent_7_days,
            pass_rate=round(pass_rate, 1),
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
