"""FastAPI 应用入口模块测试。

测试 FastAPI 应用实例和生命周期管理：
- create_app 函数
- lifespan 上下文管理器
- 健康检查端点 /health
- 异常处理器
- CORS 中间件
"""

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from src.api.main import (
    app,
    check_chroma_health,
    check_minio_health,
    check_mysql_health,
    check_redis_health,
    create_app,
    lifespan,
    register_exception_handlers,
    register_health_endpoint,
)
from src.core.exceptions import (
    BaseAppException,
    CacheException,
    DatabaseException,
    LLMException,
    ParseException,
    StorageException,
    ValidationException,
    WorkflowException,
)


# ==================== create_app 测试 ====================


class TestCreateApp:
    """create_app 函数测试类。"""

    def test_create_app_returns_fastapi_instance(self) -> None:
        """测试 create_app 返回 FastAPI 实例。"""
        with patch("src.api.main.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.app.debug = True
            mock_settings.mysql.dsn = "mysql+aiomysql://test:test@localhost/test"
            mock_get_settings.return_value = mock_settings

            test_app = create_app()

            assert isinstance(test_app, FastAPI)
            assert test_app.title == "简历筛选系统 API"

    def test_create_app_with_debug_enabled(self) -> None:
        """测试 debug 模式下启用文档端点。"""
        with patch("src.api.main.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.app.debug = True
            mock_settings.mysql.dsn = "mysql+aiomysql://test:test@localhost/test"
            mock_get_settings.return_value = mock_settings

            test_app = create_app()

            assert test_app.docs_url == "/docs"
            assert test_app.redoc_url == "/redoc"

    def test_create_app_with_debug_disabled(self) -> None:
        """测试非 debug 模式下禁用文档端点。"""
        with patch("src.api.main.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.app.debug = False
            mock_settings.mysql.dsn = "mysql+aiomysql://test:test@localhost/test"
            mock_get_settings.return_value = mock_settings

            test_app = create_app()

            assert test_app.docs_url is None
            assert test_app.redoc_url is None

    def test_create_app_includes_routers(self) -> None:
        """测试 create_app 包含所有路由。"""
        with patch("src.api.main.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.app.debug = True
            mock_settings.mysql.dsn = "mysql+aiomysql://test:test@localhost/test"
            mock_get_settings.return_value = mock_settings

            test_app = create_app()

            # 获取所有路由路径
            routes = []
            for route in test_app.routes:
                if hasattr(route, "path"):
                    routes.append(route.path)

            # 检查 API 路由前缀存在
            api_routes = [r for r in routes if r.startswith("/api/v1")]
            assert len(api_routes) > 0

    def test_create_app_has_cors_middleware(self) -> None:
        """测试 create_app 配置 CORS 中间件。"""
        with patch("src.api.main.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.app.debug = True
            mock_settings.mysql.dsn = "mysql+aiomysql://test:test@localhost/test"
            mock_get_settings.return_value = mock_settings

            test_app = create_app()

            # 检查是否有中间件
            assert len(test_app.user_middleware) > 0

    def test_create_app_has_health_endpoint(self) -> None:
        """测试 create_app 包含健康检查端点。"""
        with patch("src.api.main.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.app.debug = True
            mock_settings.mysql.dsn = "mysql+aiomysql://test:test@localhost/test"
            mock_get_settings.return_value = mock_settings

            test_app = create_app()

            routes = []
            for route in test_app.routes:
                if hasattr(route, "path"):
                    routes.append(route.path)

            assert "/health" in routes


# ==================== lifespan 测试 ====================


class TestLifespan:
    """lifespan 上下文管理器测试类。"""

    @pytest.mark.asyncio
    async def test_lifespan_initializes_resources(self) -> None:
        """测试 lifespan 正确初始化资源。"""
        mock_app = MagicMock(spec=FastAPI)

        with (
            patch("src.api.main.get_settings") as mock_get_settings,
            patch("src.api.main.setup_logger") as mock_setup_logger,
            patch("src.api.main.init_db") as mock_init_db,
            patch("src.api.main.close_db") as mock_close_db,
            patch("src.api.main.redis_client") as mock_redis_client,
        ):
            mock_settings = MagicMock()
            mock_settings.mysql.dsn = "mysql+aiomysql://test:test@localhost/test"
            mock_get_settings.return_value = mock_settings
            mock_redis_client.close = AsyncMock()

            async with lifespan(mock_app):
                pass

            mock_setup_logger.assert_called_once()
            mock_init_db.assert_called_once_with(mock_settings.mysql.dsn)
            mock_close_db.assert_called_once()
            mock_redis_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_yields_control(self) -> None:
        """测试 lifespan 正确 yield 控制权。"""
        mock_app = MagicMock(spec=FastAPI)
        yielded = False

        with (
            patch("src.api.main.get_settings") as mock_get_settings,
            patch("src.api.main.setup_logger"),
            patch("src.api.main.init_db"),
            patch("src.api.main.close_db"),
            patch("src.api.main.redis_client") as mock_redis_client,
        ):
            mock_settings = MagicMock()
            mock_settings.mysql.dsn = "mysql+aiomysql://test:test@localhost/test"
            mock_get_settings.return_value = mock_settings
            mock_redis_client.close = AsyncMock()

            async with lifespan(mock_app):
                yielded = True

            assert yielded


# ==================== 异常处理器测试 ====================


class TestExceptionHandlers:
    """异常处理器测试类。"""

    def test_app_exception_handler_returns_400(self) -> None:
        """测试业务异常处理器返回 400 状态码。"""
        test_app = FastAPI()
        register_exception_handlers(test_app)

        @test_app.get("/test")
        async def test_route():
            raise ValidationException("测试验证错误", field="name")

        client = TestClient(test_app, raise_server_exceptions=False)

        response = client.get("/test")

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "测试验证错误"
        assert "code" in data["data"]

    def test_global_exception_handler_returns_500(self) -> None:
        """测试全局异常处理器返回 500 状态码。"""
        test_app = FastAPI()
        register_exception_handlers(test_app)

        @test_app.get("/test")
        async def test_route():
            raise RuntimeError("未处理的异常")

        # 使用 raise_server_exceptions=False 来捕获异常响应
        client = TestClient(test_app, raise_server_exceptions=False)

        response = client.get("/test")

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "服务器内部错误"
        assert data["data"] is None

    def test_base_app_exception_to_dict_in_response(self) -> None:
        """测试异常响应中包含 to_dict 内容。"""
        test_app = FastAPI()
        register_exception_handlers(test_app)

        @test_app.get("/test")
        async def test_route():
            raise StorageException(
                "存储失败",
                storage_type="minio",
                details={"bucket": "test-bucket"},
            )

        client = TestClient(test_app, raise_server_exceptions=False)

        response = client.get("/test")

        data = response.json()
        assert data["data"]["code"] == "STORAGE_ERROR"
        assert data["data"]["details"]["storage_type"] == "minio"
        assert data["data"]["details"]["bucket"] == "test-bucket"


# ==================== 健康检查端点测试 ====================


class TestHealthEndpoint:
    """健康检查端点测试类。"""

    def test_health_check_all_services_healthy(self) -> None:
        """测试所有服务健康时返回 healthy 状态。"""
        test_app = FastAPI()

        with (
            patch("src.api.main.check_mysql_health") as mock_mysql,
            patch("src.api.main.check_redis_health") as mock_redis,
            patch("src.api.main.check_minio_health") as mock_minio,
            patch("src.api.main.check_chroma_health") as mock_chroma,
        ):
            mock_mysql.return_value = {"status": "healthy"}
            mock_redis.return_value = {"status": "healthy"}
            mock_minio.return_value = {"status": "healthy"}
            mock_chroma.return_value = {"status": "healthy"}

            register_health_endpoint(test_app)

            client = TestClient(test_app)
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["services"]["mysql"]["status"] == "healthy"
            assert data["services"]["redis"]["status"] == "healthy"
            assert data["services"]["minio"]["status"] == "healthy"
            assert data["services"]["chromadb"]["status"] == "healthy"

    def test_health_check_degraded_when_service_unhealthy(self) -> None:
        """测试有服务不健康时返回 degraded 状态。"""
        test_app = FastAPI()

        with (
            patch("src.api.main.check_mysql_health") as mock_mysql,
            patch("src.api.main.check_redis_health") as mock_redis,
            patch("src.api.main.check_minio_health") as mock_minio,
            patch("src.api.main.check_chroma_health") as mock_chroma,
        ):
            mock_mysql.return_value = {"status": "healthy"}
            mock_redis.return_value = {"status": "unhealthy", "message": "连接失败"}
            mock_minio.return_value = {"status": "healthy"}
            mock_chroma.return_value = {"status": "healthy"}

            register_health_endpoint(test_app)

            client = TestClient(test_app)
            response = client.get("/health")

            data = response.json()
            assert data["status"] == "degraded"
            assert data["services"]["redis"]["status"] == "unhealthy"


# ==================== 健康检查函数测试 ====================


class TestHealthCheckFunctions:
    """健康检查函数测试类。"""

    @pytest.mark.asyncio
    async def test_check_mysql_health_healthy(self) -> None:
        """测试 MySQL 健康检查成功。"""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("src.models.async_session_factory", mock_factory):
            result = await check_mysql_health()

            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_mysql_health_uninitialized(self) -> None:
        """测试 MySQL 未初始化时健康检查。"""
        with patch("src.models.async_session_factory", None):
            result = await check_mysql_health()

            assert result["status"] == "unhealthy"
            assert "未初始化" in result["message"]

    @pytest.mark.asyncio
    async def test_check_mysql_health_exception(self) -> None:
        """测试 MySQL 健康检查异常处理。"""
        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(
            side_effect=Exception("连接失败")
        )
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("src.models.async_session_factory", mock_factory):
            result = await check_mysql_health()

            assert result["status"] == "unhealthy"
            assert "连接失败" in result["message"]

    @pytest.mark.asyncio
    async def test_check_redis_health_healthy(self) -> None:
        """测试 Redis 健康检查成功。"""
        with patch("src.api.main.redis_client") as mock_redis:
            mock_redis.test_connection = AsyncMock(return_value=True)

            result = await check_redis_health()

            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_redis_health_unhealthy(self) -> None:
        """测试 Redis 健康检查失败。"""
        with patch("src.api.main.redis_client") as mock_redis:
            mock_redis.test_connection = AsyncMock(return_value=False)

            result = await check_redis_health()

            assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_redis_health_exception(self) -> None:
        """测试 Redis 健康检查异常处理。"""
        with patch("src.api.main.redis_client") as mock_redis:
            mock_redis.test_connection = AsyncMock(
                side_effect=Exception("Redis 连接失败")
            )

            result = await check_redis_health()

            assert result["status"] == "unhealthy"
            assert "Redis 连接失败" in result["message"]

    @pytest.mark.asyncio
    async def test_check_minio_health_healthy(self) -> None:
        """测试 MinIO 健康检查成功。"""
        with patch("src.api.main.minio_client") as mock_minio:
            mock_minio.test_connection = MagicMock(return_value=True)

            result = await check_minio_health()

            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_minio_health_unhealthy(self) -> None:
        """测试 MinIO 健康检查失败。"""
        with patch("src.api.main.minio_client") as mock_minio:
            mock_minio.test_connection = MagicMock(return_value=False)

            result = await check_minio_health()

            assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_minio_health_exception(self) -> None:
        """测试 MinIO 健康检查异常处理。"""
        with patch("src.api.main.minio_client") as mock_minio:
            mock_minio.test_connection = MagicMock(
                side_effect=Exception("MinIO 连接失败")
            )

            result = await check_minio_health()

            assert result["status"] == "unhealthy"
            assert "MinIO 连接失败" in result["message"]

    @pytest.mark.asyncio
    async def test_check_chroma_health_healthy(self) -> None:
        """测试 ChromaDB 健康检查成功。"""
        with patch("src.api.main.chroma_client") as mock_chroma:
            mock_chroma.test_connection = MagicMock(return_value=True)

            result = await check_chroma_health()

            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_chroma_health_unhealthy(self) -> None:
        """测试 ChromaDB 健康检查失败。"""
        with patch("src.api.main.chroma_client") as mock_chroma:
            mock_chroma.test_connection = MagicMock(return_value=False)

            result = await check_chroma_health()

            assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_chroma_health_exception(self) -> None:
        """测试 ChromaDB 健康检查异常处理。"""
        with patch("src.api.main.chroma_client") as mock_chroma:
            mock_chroma.test_connection = MagicMock(
                side_effect=Exception("ChromaDB 连接失败")
            )

            result = await check_chroma_health()

            assert result["status"] == "unhealthy"
            assert "ChromaDB 连接失败" in result["message"]


# ==================== 异常类型测试 ====================


class TestExceptionTypes:
    """不同异常类型响应测试类。"""

    def test_validation_exception_response(self) -> None:
        """测试验证异常响应。"""
        test_app = FastAPI()
        register_exception_handlers(test_app)

        @test_app.get("/test")
        async def test_route():
            raise ValidationException(
                "参数验证失败",
                field="email",
                value="invalid-email",
            )

        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/test")

        data = response.json()
        assert data["data"]["code"] == "VALIDATION_ERROR"
        assert data["data"]["details"]["field"] == "email"

    def test_llm_exception_response(self) -> None:
        """测试 LLM 异常响应。"""
        test_app = FastAPI()
        register_exception_handlers(test_app)

        @test_app.get("/test")
        async def test_route():
            raise LLMException(
                "LLM 调用超时",
                provider="deepseek",
                model="deepseek-chat",
            )

        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/test")

        data = response.json()
        assert data["data"]["code"] == "LLM_ERROR"
        assert data["data"]["details"]["provider"] == "deepseek"

    def test_parse_exception_response(self) -> None:
        """测试解析异常响应。"""
        test_app = FastAPI()
        register_exception_handlers(test_app)

        @test_app.get("/test")
        async def test_route():
            raise ParseException(
                "PDF 解析失败",
                file_type="pdf",
                file_name="resume.pdf",
            )

        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/test")

        data = response.json()
        assert data["data"]["code"] == "PARSE_ERROR"
        assert data["data"]["details"]["file_type"] == "pdf"

    def test_workflow_exception_response(self) -> None:
        """测试工作流异常响应。"""
        test_app = FastAPI()
        register_exception_handlers(test_app)

        @test_app.get("/test")
        async def test_route():
            raise WorkflowException(
                "节点执行失败",
                node="FilterNode",
                state="processing",
            )

        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/test")

        data = response.json()
        assert data["data"]["code"] == "WORKFLOW_ERROR"
        assert data["data"]["details"]["node"] == "FilterNode"

    def test_database_exception_response(self) -> None:
        """测试数据库异常响应。"""
        test_app = FastAPI()
        register_exception_handlers(test_app)

        @test_app.get("/test")
        async def test_route():
            raise DatabaseException(
                "查询超时",
                operation="select",
                table="talent_info",
            )

        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/test")

        data = response.json()
        assert data["data"]["code"] == "DATABASE_ERROR"
        assert data["data"]["details"]["operation"] == "select"

    def test_cache_exception_response(self) -> None:
        """测试缓存异常响应。"""
        test_app = FastAPI()
        register_exception_handlers(test_app)

        @test_app.get("/test")
        async def test_route():
            raise CacheException(
                "缓存读取失败",
                operation="get",
                key="talent:123",
            )

        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/test")

        data = response.json()
        assert data["data"]["code"] == "CACHE_ERROR"
        assert data["data"]["details"]["operation"] == "get"


# ==================== 全局 app 实例测试 ====================


class TestGlobalAppInstance:
    """全局 app 实例测试类。"""

    def test_global_app_is_fastapi_instance(self) -> None:
        """测试全局 app 是 FastAPI 实例。"""
        assert isinstance(app, FastAPI)

    def test_global_app_has_health_endpoint(self) -> None:
        """测试全局 app 包含健康检查端点。"""
        routes = []
        for route in app.routes:
            if hasattr(route, "path"):
                routes.append(route.path)

        assert "/health" in routes

    def test_global_app_has_api_routes(self) -> None:
        """测试全局 app 包含 API 路由。"""
        routes = []
        for route in app.routes:
            if hasattr(route, "path"):
                routes.append(route.path)

        # 检查是否有 API v1 路由
        api_routes = [r for r in routes if r.startswith("/api/v1")]
        assert len(api_routes) > 0


# ==================== 集成测试 ====================


@pytest.mark.integration
class TestMainIntegration:
    """主应用集成测试类。"""

    @pytest.mark.asyncio
    async def test_health_endpoint_with_async_client(self) -> None:
        """测试使用异步客户端访问健康检查端点。"""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            with (
                patch("src.api.main.check_mysql_health") as mock_mysql,
                patch("src.api.main.check_redis_health") as mock_redis,
                patch("src.api.main.check_minio_health") as mock_minio,
                patch("src.api.main.check_chroma_health") as mock_chroma,
            ):
                mock_mysql.return_value = {"status": "healthy"}
                mock_redis.return_value = {"status": "healthy"}
                mock_minio.return_value = {"status": "healthy"}
                mock_chroma.return_value = {"status": "healthy"}

                response = await client.get("/health")

                assert response.status_code == 200
                data = response.json()
                assert "status" in data
                assert "services" in data
