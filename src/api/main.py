"""FastAPI 应用入口模块。

提供 FastAPI 应用实例和生命周期管理：
- CORS 中间件配置
- 路由注册（conditions, talents, analysis）
- 全局异常处理器
- 启动/关闭事件处理
- 健康检查端点
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy import text

from src.api.v1.analysis import router as analysis_router
from src.api.v1.conditions import router as conditions_router
from src.api.v1.talents import router as talents_router
from src.api.v1.websocket import router as websocket_router
from src.core.config import get_settings
from src.core.exceptions import BaseAppException
from src.core.logger import setup_logger
from src.models import close_db, init_db
from src.storage.chroma_client import chroma_client
from src.storage.minio_client import minio_client
from src.storage.redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。

    负责应用启动时的初始化和关闭时的资源清理。

    Args:
        app: FastAPI 应用实例

    Yields:
        None
    """
    # 启动时初始化
    settings = get_settings()
    setup_logger()
    logger.info("应用启动中...")

    # 初始化数据库连接
    init_db(settings.mysql.dsn)
    logger.success("数据库连接初始化完成")

    yield

    # 关闭时清理资源
    logger.info("应用关闭中...")
    await close_db()
    await redis_client.close()
    logger.success("应用资源已释放")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例。

    配置中间件、路由和异常处理器。

    Returns:
        FastAPI: 配置完成的 FastAPI 应用实例
    """
    settings = get_settings()

    app = FastAPI(
        title="简历筛选系统 API",
        description="基于 LLM 的智能简历筛选系统",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # 配置 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(conditions_router, prefix="/api/v1")
    app.include_router(talents_router, prefix="/api/v1")
    app.include_router(analysis_router, prefix="/api/v1")
    app.include_router(websocket_router)

    # 注册全局异常处理器
    register_exception_handlers(app)

    # 注册健康检查端点
    register_health_endpoint(app)

    logger.info("FastAPI 应用实例创建完成")
    return app


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器。

    Args:
        app: FastAPI 应用实例
    """

    @app.exception_handler(BaseAppException)
    async def app_exception_handler(
        request: Request,
        exc: BaseAppException,
    ) -> JSONResponse:
        """处理业务异常。

        Args:
            request: 请求对象
            exc: 业务异常实例

        Returns:
            JSONResponse: 统一格式的错误响应
        """
        logger.warning(f"业务异常: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": exc.message,
                "data": exc.to_dict(),
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """处理未捕获的异常。

        Args:
            request: 请求对象
            exc: 异常实例

        Returns:
            JSONResponse: 统一格式的错误响应
        """
        logger.exception(f"未处理的异常: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "服务器内部错误",
                "data": None,
            },
        )


def register_health_endpoint(app: FastAPI) -> None:
    """注册健康检查端点。

    Args:
        app: FastAPI 应用实例
    """

    @app.get(
        "/health",
        tags=["系统监控"],
        summary="健康检查",
        description="检查各服务连接状态",
    )
    async def health_check() -> dict[str, Any]:
        """健康检查端点。

        检查 MySQL、Redis、MinIO、ChromaDB 连接状态。

        Returns:
            dict: 各服务的健康状态
        """
        logger.debug("执行健康检查")

        # 检查各服务状态
        services: dict[str, Any] = {
            "mysql": await check_mysql_health(),
            "redis": await check_redis_health(),
            "minio": await check_minio_health(),
            "chromadb": await check_chroma_health(),
        }

        # 计算整体状态
        all_healthy = all(s.get("status") == "healthy" for s in services.values())

        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": services,
        }


async def check_mysql_health() -> dict[str, Any]:
    """检查 MySQL 连接状态。

    Returns:
        dict: MySQL 健康状态
    """
    try:
        from src.models import async_session_factory

        if async_session_factory is None:
            return {"status": "unhealthy", "message": "数据库未初始化"}

        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"MySQL 健康检查失败: {e}")
        return {"status": "unhealthy", "message": str(e)}


async def check_redis_health() -> dict[str, Any]:
    """检查 Redis 连接状态。

    Returns:
        dict: Redis 健康状态
    """
    try:
        is_healthy = await redis_client.test_connection()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
        }
    except Exception as e:
        logger.error(f"Redis 健康检查失败: {e}")
        return {"status": "unhealthy", "message": str(e)}


async def check_minio_health() -> dict[str, Any]:
    """检查 MinIO 连接状态。

    Returns:
        dict: MinIO 健康状态
    """
    try:
        import asyncio

        is_healthy = await asyncio.to_thread(minio_client.test_connection)
        return {
            "status": "healthy" if is_healthy else "unhealthy",
        }
    except Exception as e:
        logger.error(f"MinIO 健康检查失败: {e}")
        return {"status": "unhealthy", "message": str(e)}


async def check_chroma_health() -> dict[str, Any]:
    """检查 ChromaDB 连接状态。

    Returns:
        dict: ChromaDB 健康状态
    """
    try:
        import asyncio

        is_healthy = await asyncio.to_thread(chroma_client.test_connection)
        return {
            "status": "healthy" if is_healthy else "unhealthy",
        }
    except Exception as e:
        logger.error(f"ChromaDB 健康检查失败: {e}")
        return {"status": "unhealthy", "message": str(e)}


# 创建应用实例
app = create_app()

__all__ = ["app", "create_app"]
