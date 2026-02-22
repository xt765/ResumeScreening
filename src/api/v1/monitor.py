"""系统监控 API 端点模块。

提供系统监控相关的 REST API：
- 日志查询和导出
- 系统健康状态
- 资源指标采集
"""

from datetime import datetime, timezone, timedelta
import math

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from loguru import logger
from sqlalchemy import text

from src.api.deps import CurrentUser
from src.schemas.common import APIResponse, PaginatedResponse
from src.schemas.monitor import (
    LogEntry,
    MetricPoint,
    ResourceUsage,
    ServiceStatus,
    SystemHealth,
)
from src.services.log_service import log_service
from src.services.metrics_service import metrics_service
from src.storage.chroma_client import chroma_client
from src.storage.minio_client import minio_client
from src.storage.redis_client import redis_client

router = APIRouter(prefix="/monitor", tags=["系统监控"])

# 本地时区偏移（UTC+8）
LOCAL_TZ_OFFSET = timezone(timedelta(hours=8))


def parse_local_datetime(dt: datetime | None) -> datetime | None:
    """将不带时区的 datetime 转换为本地时区时间。

    Args:
        dt: 输入的 datetime 对象。

    Returns:
        带时区的 datetime 对象。
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # 不带时区的时间，视为本地时间（UTC+8）
        return dt.replace(tzinfo=LOCAL_TZ_OFFSET)
    return dt


@router.get("/logs", response_model=APIResponse[PaginatedResponse[LogEntry]])
async def get_logs(
    current_user: CurrentUser,
    start_time: datetime | None = Query(None, description="开始时间"),
    end_time: datetime | None = Query(None, description="结束时间"),
    level: list[str] | None = Query(None, description="日志级别"),
    keyword: str | None = Query(None, description="搜索关键词"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="排序方式"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页记录数"),
) -> APIResponse[PaginatedResponse[LogEntry]]:
    """查询系统日志。

    支持按时间范围、级别、关键词筛选，分页返回结果。

    Args:
        current_user: 当前登录用户
        start_time: 开始时间。
        end_time: 结束时间。
        level: 日志级别列表。
        keyword: 搜索关键词。
        order: 排序方式（asc=正序，desc=逆序）。
        page: 页码（从 1 开始）。
        page_size: 每页记录数。

    Returns:
        APIResponse[PaginatedResponse[LogEntry]]: 分页日志列表。
    """
    # 转换时间参数
    start_time = parse_local_datetime(start_time)
    end_time = parse_local_datetime(end_time)

    logger.debug(
        f"查询日志: start_time={start_time}, end_time={end_time}, "
        f"level={level}, keyword={keyword}, order={order}, "
        f"page={page}, page_size={page_size}"
    )

    logs, total = await log_service.query_logs(
        start_time=start_time,
        end_time=end_time,
        levels=level,
        keyword=keyword,
        page=page,
        page_size=page_size,
        order=order,
    )

    entries = []
    for log in logs:
        timestamp = log.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        entries.append(
            LogEntry(
                timestamp=timestamp or datetime.now(),
                level=log.get("level", "INFO"),
                message=log.get("message", ""),
                module=log.get("module", ""),
                function=log.get("function", ""),
                line=log.get("line", 0),
                process_id=log.get("process_id", 0),
                thread_id=log.get("thread_id", 0),
                extra=log.get("extra"),
                exception=log.get("exception"),
            )
        )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return APIResponse(
        success=True,
        message="查询成功",
        data=PaginatedResponse(
            items=entries,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get("/logs/export")
async def export_logs(
    start_time: datetime | None = Query(None, description="开始时间"),
    end_time: datetime | None = Query(None, description="结束时间"),
    level: list[str] | None = Query(None, description="日志级别"),
    keyword: str | None = Query(None, description="搜索关键词"),
    format: str = Query("json", pattern="^(json|csv)$", description="导出格式"),
) -> PlainTextResponse:
    """导出日志文件。

    支持导出为 JSON 或 CSV 格式。

    Args:
        start_time: 开始时间。
        end_time: 结束时间。
        level: 日志级别列表。
        keyword: 搜索关键词。
        format: 导出格式（json/csv）。

    Returns:
        PlainTextResponse: 日志文件内容。
    """
    logger.info(f"导出日志: format={format}")

    content = await log_service.export_logs(
        start_time=start_time,
        end_time=end_time,
        levels=level,
        keyword=keyword,
        format=format,
    )

    media_type = "application/json" if format == "json" else "text/csv"
    filename = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"

    return PlainTextResponse(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/health", response_model=APIResponse[SystemHealth])
async def get_system_health() -> APIResponse[SystemHealth]:
    """获取系统健康状态。

    检查各服务连接状态和系统资源使用情况。

    Returns:
        APIResponse[SystemHealth]: 系统健康状态。
    """
    import asyncio

    logger.debug("执行系统健康检查")

    async def safe_check(check_func, timeout: float) -> ServiceStatus:
        try:
            return await asyncio.wait_for(check_func(), timeout=timeout)
        except asyncio.TimeoutError:
            return ServiceStatus(
                name=check_func.__name__.replace("check_", "").replace("_status", "").title(),
                status="unhealthy",
                message="检查超时",
            )
        except Exception as e:
            return ServiceStatus(
                name=check_func.__name__.replace("check_", "").replace("_status", "").title(),
                status="unhealthy",
                message=str(e)[:100],
            )

    services = await asyncio.gather(
        safe_check(check_mysql_status, 5),
        safe_check(check_redis_status, 3),
        safe_check(check_minio_status, 5),
        safe_check(check_chroma_status, 3),
    )

    all_healthy = all(s.status == "healthy" for s in services)
    any_degraded = any(s.status == "degraded" for s in services)

    if all_healthy:
        overall_status = "healthy"
    elif any_degraded:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    resources = await metrics_service.collect_metrics()

    return APIResponse(
        success=True,
        message="健康检查完成",
        data=SystemHealth(
            status=overall_status,
            services=services,
            resources=resources,
            uptime_seconds=metrics_service.get_uptime_seconds(),
            last_check=datetime.now(),
        ),
    )


async def check_mysql_status() -> ServiceStatus:
    """检查 MySQL 连接状态。

    Returns:
        ServiceStatus: MySQL 服务状态。
    """
    import time

    from src.models import async_session_factory

    start = time.time()
    try:
        if async_session_factory is None:
            return ServiceStatus(
                name="MySQL",
                status="unhealthy",
                message="数据库未初始化",
            )

        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))

        latency = (time.time() - start) * 1000
        return ServiceStatus(
            name="MySQL",
            status="healthy",
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        return ServiceStatus(
            name="MySQL",
            status="unhealthy",
            message=str(e)[:100],
        )


async def check_redis_status() -> ServiceStatus:
    """检查 Redis 连接状态。

    Returns:
        ServiceStatus: Redis 服务状态。
    """
    import time

    start = time.time()
    try:
        is_healthy = await redis_client.test_connection()
        latency = (time.time() - start) * 1000
        return ServiceStatus(
            name="Redis",
            status="healthy" if is_healthy else "unhealthy",
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        return ServiceStatus(
            name="Redis",
            status="unhealthy",
            message=str(e)[:100],
        )


async def check_minio_status() -> ServiceStatus:
    """检查 MinIO 连接状态。

    Returns:
        ServiceStatus: MinIO 服务状态。
    """
    import asyncio
    import time

    start = time.time()
    try:
        is_healthy = await asyncio.to_thread(minio_client.test_connection)
        latency = (time.time() - start) * 1000
        return ServiceStatus(
            name="MinIO",
            status="healthy" if is_healthy else "unhealthy",
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        return ServiceStatus(
            name="MinIO",
            status="unhealthy",
            message=str(e)[:100],
        )


async def check_chroma_status() -> ServiceStatus:
    """检查 ChromaDB 连接状态。

    Returns:
        ServiceStatus: ChromaDB 服务状态。
    """
    import asyncio
    import time

    start = time.time()
    try:
        is_healthy = await asyncio.to_thread(chroma_client.test_connection)
        latency = (time.time() - start) * 1000
        return ServiceStatus(
            name="ChromaDB",
            status="healthy" if is_healthy else "unhealthy",
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        return ServiceStatus(
            name="ChromaDB",
            status="unhealthy",
            message=str(e)[:100],
        )


@router.get("/metrics", response_model=APIResponse[ResourceUsage])
async def get_system_metrics() -> APIResponse[ResourceUsage]:
    """获取当前系统资源指标。

    Returns:
        APIResponse[ResourceUsage]: 资源使用情况。
    """
    metrics = await metrics_service.collect_metrics()
    return APIResponse(
        success=True,
        message="获取成功",
        data=metrics,
    )


@router.get("/metrics/history", response_model=APIResponse[list[MetricPoint]])
async def get_metrics_history(
    duration: int = Query(3600, ge=60, le=86400, description="时间范围（秒）"),
) -> APIResponse[list[MetricPoint]]:
    """获取历史资源指标。

    Args:
        duration: 时间范围（秒），默认 1 小时。

    Returns:
        APIResponse[list[MetricPoint]]: 指标数据点列表。
    """
    points = await metrics_service.get_metrics_history(duration=duration)
    return APIResponse(
        success=True,
        message="获取成功",
        data=points,
    )


__all__ = ["router"]
