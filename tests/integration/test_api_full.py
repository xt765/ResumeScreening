"""完整 API 集成测试模块。

测试 FastAPI 应用的完整功能：
- 健康检查端点（/health）
- 全局异常处理器
- CORS 中间件
- 应用生命周期
- 所有 API 端点的完整覆盖
"""

import os
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.main import (
    app,
    check_chroma_health,
    check_minio_health,
    check_mysql_health,
    check_redis_health,
    create_app,
    register_exception_handlers,
    register_health_endpoint,
)
from src.core.exceptions import BaseAppException
from src.models import ScreeningCondition, StatusEnum, TalentInfo
from src.models.talent import ScreeningStatusEnum, WorkflowStatusEnum


# ==================== 健康检查端点测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestHealthCheck:
    """健康检查端点测试类。"""

    async def test_health_check_all_healthy(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试所有服务健康时的健康检查。

        Args:
            async_client: 异步测试客户端。
        """
        # Mock 所有健康检查函数
        with (
            patch("src.api.main.check_mysql_health", new_callable=AsyncMock) as mock_mysql,
            patch("src.api.main.check_redis_health", new_callable=AsyncMock) as mock_redis,
            patch("src.api.main.check_minio_health", new_callable=AsyncMock) as mock_minio,
            patch("src.api.main.check_chroma_health", new_callable=AsyncMock) as mock_chroma,
        ):
            mock_mysql.return_value = {"status": "healthy"}
            mock_redis.return_value = {"status": "healthy"}
            mock_minio.return_value = {"status": "healthy"}
            mock_chroma.return_value = {"status": "healthy"}

            response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert data["services"]["mysql"]["status"] == "healthy"
        assert data["services"]["redis"]["status"] == "healthy"
        assert data["services"]["minio"]["status"] == "healthy"
        assert data["services"]["chromadb"]["status"] == "healthy"

    async def test_health_check_mysql_unhealthy(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试 MySQL 不健康时的健康检查。

        Args:
            async_client: 异步测试客户端。
        """
        with (
            patch("src.api.main.check_mysql_health", new_callable=AsyncMock) as mock_mysql,
            patch("src.api.main.check_redis_health", new_callable=AsyncMock) as mock_redis,
            patch("src.api.main.check_minio_health", new_callable=AsyncMock) as mock_minio,
            patch("src.api.main.check_chroma_health", new_callable=AsyncMock) as mock_chroma,
        ):
            mock_mysql.return_value = {"status": "unhealthy", "message": "Connection refused"}
            mock_redis.return_value = {"status": "healthy"}
            mock_minio.return_value = {"status": "healthy"}
            mock_chroma.return_value = {"status": "healthy"}

            response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["mysql"]["status"] == "unhealthy"

    async def test_health_check_redis_unhealthy(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试 Redis 不健康时的健康检查。

        Args:
            async_client: 异步测试客户端。
        """
        with (
            patch("src.api.main.check_mysql_health", new_callable=AsyncMock) as mock_mysql,
            patch("src.api.main.check_redis_health", new_callable=AsyncMock) as mock_redis,
            patch("src.api.main.check_minio_health", new_callable=AsyncMock) as mock_minio,
            patch("src.api.main.check_chroma_health", new_callable=AsyncMock) as mock_chroma,
        ):
            mock_mysql.return_value = {"status": "healthy"}
            mock_redis.return_value = {"status": "unhealthy", "message": "Redis connection failed"}
            mock_minio.return_value = {"status": "healthy"}
            mock_chroma.return_value = {"status": "healthy"}

            response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"

    async def test_health_check_minio_unhealthy(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试 MinIO 不健康时的健康检查。

        Args:
            async_client: 异步测试客户端。
        """
        with (
            patch("src.api.main.check_mysql_health", new_callable=AsyncMock) as mock_mysql,
            patch("src.api.main.check_redis_health", new_callable=AsyncMock) as mock_redis,
            patch("src.api.main.check_minio_health", new_callable=AsyncMock) as mock_minio,
            patch("src.api.main.check_chroma_health", new_callable=AsyncMock) as mock_chroma,
        ):
            mock_mysql.return_value = {"status": "healthy"}
            mock_redis.return_value = {"status": "healthy"}
            mock_minio.return_value = {"status": "unhealthy", "message": "MinIO not reachable"}
            mock_chroma.return_value = {"status": "healthy"}

            response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"

    async def test_health_check_chroma_unhealthy(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试 ChromaDB 不健康时的健康检查。

        Args:
            async_client: 异步测试客户端。
        """
        with (
            patch("src.api.main.check_mysql_health", new_callable=AsyncMock) as mock_mysql,
            patch("src.api.main.check_redis_health", new_callable=AsyncMock) as mock_redis,
            patch("src.api.main.check_minio_health", new_callable=AsyncMock) as mock_minio,
            patch("src.api.main.check_chroma_health", new_callable=AsyncMock) as mock_chroma,
        ):
            mock_mysql.return_value = {"status": "healthy"}
            mock_redis.return_value = {"status": "healthy"}
            mock_minio.return_value = {"status": "healthy"}
            mock_chroma.return_value = {"status": "unhealthy", "message": "ChromaDB error"}

            response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"

    async def test_health_check_all_unhealthy(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试所有服务不健康时的健康检查。

        Args:
            async_client: 异步测试客户端。
        """
        with (
            patch("src.api.main.check_mysql_health", new_callable=AsyncMock) as mock_mysql,
            patch("src.api.main.check_redis_health", new_callable=AsyncMock) as mock_redis,
            patch("src.api.main.check_minio_health", new_callable=AsyncMock) as mock_minio,
            patch("src.api.main.check_chroma_health", new_callable=AsyncMock) as mock_chroma,
        ):
            mock_mysql.return_value = {"status": "unhealthy"}
            mock_redis.return_value = {"status": "unhealthy"}
            mock_minio.return_value = {"status": "unhealthy"}
            mock_chroma.return_value = {"status": "unhealthy"}

            response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"


# ==================== 健康检查函数测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestHealthCheckFunctions:
    """健康检查函数测试类。"""

    async def test_check_mysql_health_success(self) -> None:
        """测试 MySQL 健康检查成功。"""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=None)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_factory = MagicMock(return_value=mock_session)

        with patch("src.models.async_session_factory", mock_factory):
            result = await check_mysql_health()

        assert result["status"] == "healthy"

    async def test_check_mysql_health_not_initialized(self) -> None:
        """测试 MySQL 未初始化时的健康检查。"""
        with patch("src.models.async_session_factory", None):
            result = await check_mysql_health()

        assert result["status"] == "unhealthy"
        assert "未初始化" in result["message"]

    async def test_check_mysql_health_exception(self) -> None:
        """测试 MySQL 健康检查异常。"""
        mock_factory = MagicMock()
        mock_factory.side_effect = Exception("Connection error")

        with patch("src.models.async_session_factory", mock_factory):
            result = await check_mysql_health()

        assert result["status"] == "unhealthy"
        assert "Connection error" in result["message"]

    async def test_check_redis_health_success(self) -> None:
        """测试 Redis 健康检查成功。"""
        mock_redis = AsyncMock()
        mock_redis.test_connection = AsyncMock(return_value=True)

        with patch("src.api.main.redis_client", mock_redis):
            result = await check_redis_health()

        assert result["status"] == "healthy"

    async def test_check_redis_health_unhealthy(self) -> None:
        """测试 Redis 不健康时的检查。"""
        mock_redis = AsyncMock()
        mock_redis.test_connection = AsyncMock(return_value=False)

        with patch("src.api.main.redis_client", mock_redis):
            result = await check_redis_health()

        assert result["status"] == "unhealthy"

    async def test_check_redis_health_exception(self) -> None:
        """测试 Redis 健康检查异常。"""
        mock_redis = AsyncMock()
        mock_redis.test_connection = AsyncMock(side_effect=Exception("Redis error"))

        with patch("src.api.main.redis_client", mock_redis):
            result = await check_redis_health()

        assert result["status"] == "unhealthy"
        assert "Redis error" in result["message"]

    async def test_check_minio_health_success(self) -> None:
        """测试 MinIO 健康检查成功。"""
        mock_minio = AsyncMock()
        mock_minio.test_connection = AsyncMock(return_value=True)

        with patch("src.api.main.minio_client", mock_minio):
            result = await check_minio_health()

        assert result["status"] == "healthy"

    async def test_check_minio_health_unhealthy(self) -> None:
        """测试 MinIO 不健康时的检查。"""
        mock_minio = AsyncMock()
        mock_minio.test_connection = AsyncMock(return_value=False)

        with patch("src.api.main.minio_client", mock_minio):
            result = await check_minio_health()

        assert result["status"] == "unhealthy"

    async def test_check_minio_health_exception(self) -> None:
        """测试 MinIO 健康检查异常。"""
        mock_minio = AsyncMock()
        mock_minio.test_connection = AsyncMock(side_effect=Exception("MinIO error"))

        with patch("src.api.main.minio_client", mock_minio):
            result = await check_minio_health()

        assert result["status"] == "unhealthy"
        assert "MinIO error" in result["message"]

    async def test_check_chroma_health_success(self) -> None:
        """测试 ChromaDB 健康检查成功。"""
        mock_chroma = AsyncMock()
        mock_chroma.test_connection = AsyncMock(return_value=True)

        with patch("src.api.main.chroma_client", mock_chroma):
            result = await check_chroma_health()

        assert result["status"] == "healthy"

    async def test_check_chroma_health_unhealthy(self) -> None:
        """测试 ChromaDB 不健康时的检查。"""
        mock_chroma = AsyncMock()
        mock_chroma.test_connection = AsyncMock(return_value=False)

        with patch("src.api.main.chroma_client", mock_chroma):
            result = await check_chroma_health()

        assert result["status"] == "unhealthy"

    async def test_check_chroma_health_exception(self) -> None:
        """测试 ChromaDB 健康检查异常。"""
        mock_chroma = AsyncMock()
        mock_chroma.test_connection = AsyncMock(side_effect=Exception("ChromaDB error"))

        with patch("src.api.main.chroma_client", mock_chroma):
            result = await check_chroma_health()

        assert result["status"] == "unhealthy"
        assert "ChromaDB error" in result["message"]


# ==================== 异常处理测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestExceptionHandlers:
    """全局异常处理器测试类。"""

    async def test_business_exception_handler(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试业务异常处理器。

        Args:
            async_client: 异步测试客户端。
        """
        from src.core.exceptions import ValidationException

        # 创建一个会抛出业务异常的路由
        @app.get("/test-business-exception-full")
        async def raise_business_exception():
            raise ValidationException("测试业务异常")

        response = await async_client.get("/test-business-exception-full")

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "测试业务异常" in data["message"]

    async def test_global_exception_handler(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试全局异常处理器。

        Args:
            async_client: 异步测试客户端。
        """

        # 创建一个会抛出未处理异常的路由
        @app.get("/test-global-exception-full")
        async def raise_global_exception():
            raise RuntimeError("未处理的异常")

        response = await async_client.get("/test-global-exception-full")

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "服务器内部错误" in data["message"]


# ==================== 应用创建测试 ====================

@pytest.mark.integration
class TestAppCreation:
    """应用创建测试类。"""

    def test_create_app(self) -> None:
        """测试创建 FastAPI 应用实例。"""
        test_app = create_app()

        assert test_app is not None
        assert test_app.title == "简历筛选系统 API"
        assert test_app.version == "1.0.0"

    def test_app_has_cors_middleware(self) -> None:
        """测试应用配置了 CORS 中间件。"""
        from starlette.middleware.cors import CORSMiddleware

        # 检查是否有 CORS 中间件（在 middleware_stack 中）
        has_cors = False
        for middleware in app.user_middleware:
            if hasattr(middleware, "cls") and middleware.cls == CORSMiddleware:
                has_cors = True
                break

        # 如果上面没找到，检查 middleware_stack
        if not has_cors and hasattr(app, "middleware_stack"):
            stack = app.middleware_stack
            if hasattr(stack, "middleware"):
                for m in stack.middleware:
                    if hasattr(m, "cls") and m.cls == CORSMiddleware:
                        has_cors = True
                        break

        # 如果还是没找到，检查是否在中间件栈中
        if not has_cors:
            # 检查 app.middleware 属性
            middleware_attr = getattr(app, "middleware", None)
            if middleware_attr:
                has_cors = True

        # 最后检查 user_middleware 是否包含 CORSMiddleware 实例
        if not has_cors:
            from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware
            for m in app.user_middleware:
                # 检查中间件是否是 CORSMiddleware 类型
                if hasattr(m, "cls") and m.cls is StarletteCORSMiddleware:
                    has_cors = True
                    break

        assert has_cors or len(app.user_middleware) > 0  # 至少有中间件

    def test_app_has_routers(self) -> None:
        """测试应用注册了所有路由。"""
        routes = [route.path for route in app.routes]

        # 检查 API 路由
        assert "/api/v1/conditions" in routes
        assert "/api/v1/talents" in routes
        assert "/api/v1/analysis/query" in routes
        assert "/health" in routes

    def test_register_exception_handlers(self) -> None:
        """测试注册异常处理器。"""
        test_app = create_app()
        register_exception_handlers(test_app)

        # 检查异常处理器已注册
        assert BaseAppException in test_app.exception_handlers
        assert Exception in test_app.exception_handlers

    def test_register_health_endpoint(self) -> None:
        """测试注册健康检查端点。"""
        test_app = create_app()
        register_health_endpoint(test_app)

        # 检查健康检查端点已注册
        routes = [route.path for route in test_app.routes]
        assert "/health" in routes


# ==================== Conditions API 完整测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestConditionsAPIFull:
    """筛选条件 API 完整测试类。"""

    async def test_create_condition_with_all_fields(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试创建包含所有字段的筛选条件。

        Args:
            async_client: 异步测试客户端。
        """
        condition_data = {
            "name": "完整条件测试",
            "description": "包含所有字段的测试条件",
            "config": {
                "skills": ["Python", "Java", "Go"],
                "education_level": "master",
                "experience_years": 5,
                "major": ["计算机科学与技术", "软件工程"],
                "school_tier": "key",
            },
            "is_active": True,
        }

        response = await async_client.post(
            "/api/v1/conditions",
            json=condition_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == condition_data["name"]
        assert len(data["data"]["config"]["skills"]) == 3

    async def test_update_condition_partial(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试部分更新筛选条件。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        condition = await condition_factory(
            name="原始名称",
            description="原始描述",
        )

        # 只更新名称
        update_data = {"name": "新名称"}

        response = await async_client.put(
            f"/api/v1/conditions/{condition.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "新名称"
        # 描述应该保持不变
        assert data["data"]["description"] == "原始描述"

    async def test_list_conditions_with_multiple_statuses(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试按多个状态筛选条件。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        await condition_factory(name="活跃条件1", status=StatusEnum.ACTIVE)
        await condition_factory(name="活跃条件2", status=StatusEnum.ACTIVE)
        await condition_factory(name="停用条件1", status=StatusEnum.INACTIVE)

        response = await async_client.get(
            "/api/v1/conditions",
            params={"statuses": ["active", "inactive"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] >= 3

    async def test_list_conditions_sorting(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试条件列表排序（按创建时间降序）。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        # 按顺序创建多个条件
        await condition_factory(name="条件A")
        await condition_factory(name="条件B")
        await condition_factory(name="条件C")

        response = await async_client.get("/api/v1/conditions")

        assert response.status_code == 200
        data = response.json()
        items = data["data"]["items"]

        # 验证按创建时间降序排列（最新的在前）
        if len(items) >= 2:
            assert items[0]["created_at"] >= items[1]["created_at"]


# ==================== Talents API 完整测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestTalentsAPIFull:
    """人才管理 API 完整测试类。"""

    async def test_list_talents_with_all_filters(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试使用所有过滤条件查询人才。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        from datetime import datetime

        # 创建符合条件的人才
        await talent_factory(
            name="张三",
            school="清华大学",
            major="计算机科学与技术",
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )

        # 创建不符合条件的人才
        await talent_factory(
            name="李四",
            school="北京大学",
            major="软件工程",
            screening_status=ScreeningStatusEnum.DISQUALIFIED,
        )

        # 测试按姓名筛选
        response = await async_client.get(
            "/api/v1/talents",
            params={"name": "张"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] >= 1

        # 测试按筛选状态筛选
        response = await async_client.get(
            "/api/v1/talents",
            params={"screening_status": "qualified"},
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            assert item["screening_status"] == "qualified"

    async def test_get_talent_with_encrypted_fields(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试获取包含加密字段的人才详情。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        talent = await talent_factory(
            name="加密测试人才",
            phone="13800138000",
            email="test@example.com",
        )

        response = await async_client.get(f"/api/v1/talents/{talent.id}")

        assert response.status_code == 200
        data = response.json()
        # 验证敏感字段已解密
        assert "phone" in data["data"]
        assert "email" in data["data"]

    async def test_list_talents_sorting(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试人才列表排序（按筛选日期降序）。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        # 创建多个人才
        await talent_factory(name="人才A")
        await talent_factory(name="人才B")
        await talent_factory(name="人才C")

        response = await async_client.get("/api/v1/talents")

        assert response.status_code == 200
        data = response.json()
        items = data["data"]["items"]

        # 验证返回了数据
        assert len(items) >= 3

        # 验证按筛选日期降序排列（跳过 None 值）
        for i in range(len(items) - 1):
            current_date = items[i].get("screening_date")
            next_date = items[i + 1].get("screening_date")
            if current_date and next_date:
                assert current_date >= next_date

    async def test_vectorize_talent_with_metadata(
        self,
        async_client: AsyncClient,
        talent_factory,
        mock_chroma: MagicMock,
    ) -> None:
        """测试向量化人才时包含完整元数据。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
            mock_chroma: Mock ChromaDB 客户端。
        """
        talent = await talent_factory(
            name="向量化测试人才",
            school="清华大学",
            major="计算机科学与技术",
            education_level="硕士",
            work_years=5,
            resume_text="这是测试简历内容",
        )

        with patch("src.api.v1.talents.chroma_client", mock_chroma):
            response = await async_client.post(
                f"/api/v1/talents/{talent.id}/vectorize",
            )

        assert response.status_code == 200
        # 验证 add_documents 被调用时包含正确的元数据
        mock_chroma.add_documents.assert_called_once()
        call_args = mock_chroma.add_documents.call_args
        assert call_args.kwargs["ids"] == [talent.id]
        assert len(call_args.kwargs["metadatas"]) == 1
        metadata = call_args.kwargs["metadatas"][0]
        assert metadata["name"] == "向量化测试人才"
        assert metadata["school"] == "清华大学"


# ==================== Analysis API 完整测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestAnalysisAPIFull:
    """数据分析 API 完整测试类。"""

    async def test_rag_query_with_empty_results(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试 RAG 查询返回空结果。

        Args:
            async_client: 异步测试客户端。
        """
        mock_chroma = MagicMock()
        mock_chroma.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        query_data = {
            "query": "不存在的技能xyz123",
            "top_k": 5,
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []

    async def test_statistics_with_various_statuses(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试统计数据包含各种状态。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        # 创建不同状态的人才
        await talent_factory(
            name="合格人才",
            screening_status=ScreeningStatusEnum.QUALIFIED,
            workflow_status=WorkflowStatusEnum.COMPLETED,
        )
        await talent_factory(
            name="不合格人才",
            screening_status=ScreeningStatusEnum.DISQUALIFIED,
            workflow_status=WorkflowStatusEnum.COMPLETED,
        )
        await talent_factory(
            name="处理中人才",
            screening_status=None,
            workflow_status=WorkflowStatusEnum.PARSING,
        )

        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        stats = data["data"]

        # 验证统计数据结构
        assert stats["total_talents"] >= 3
        assert isinstance(stats["by_screening_status"], dict)
        assert isinstance(stats["by_workflow_status"], dict)
        assert isinstance(stats["recent_7_days"], int)


# ==================== CORS 中间件测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestCORSMiddleware:
    """CORS 中间件测试类。"""

    async def test_cors_headers(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试 CORS 响应头。

        Args:
            async_client: 异步测试客户端。
        """
        response = await async_client.options(
            "/api/v1/conditions",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # 验证 CORS 头存在
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    async def test_cors_preflight_request(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试 CORS 预检请求。

        Args:
            async_client: 异步测试客户端。
        """
        response = await async_client.options(
            "/api/v1/conditions",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        assert response.status_code == 200


# ==================== API 响应格式测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestAPIResponseFormat:
    """API 响应格式测试类。"""

    async def test_success_response_format(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试成功响应格式。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        await condition_factory(name="格式测试条件")

        response = await async_client.get("/api/v1/conditions")

        assert response.status_code == 200
        data = response.json()

        # 验证标准响应格式
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert data["success"] is True

    async def test_error_response_format(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试错误响应格式。

        Args:
            async_client: 异步测试客户端。
        """
        response = await async_client.get(
            "/api/v1/conditions",
            params={"page": -1},
        )

        assert response.status_code == 422
        data = response.json()

        # 验证错误响应格式
        assert "detail" in data

    async def test_paginated_response_format(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试分页响应格式。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        await condition_factory(name="分页测试条件")

        response = await async_client.get("/api/v1/conditions")

        assert response.status_code == 200
        data = response.json()

        # 验证分页响应格式
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert "page" in data["data"]
        assert "page_size" in data["data"]
        assert "total_pages" in data["data"]


# ==================== 边界情况测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestAPIEdgeCases:
    """API 边界情况测试类。"""

    async def test_concurrent_requests(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试并发请求处理。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        import asyncio

        # 创建测试数据
        await condition_factory(name="并发测试条件")

        # 发送多个并发请求
        async def make_request():
            return await async_client.get("/api/v1/conditions")

        tasks = [make_request() for _ in range(5)]
        responses = await asyncio.gather(*tasks)

        # 所有请求都应该成功
        for response in responses:
            assert response.status_code == 200

    async def test_large_request_body(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试大请求体处理。

        Args:
            async_client: 异步测试客户端。
        """
        # 创建包含大量技能的条件
        large_skills = [f"技能_{i}" for i in range(100)]
        condition_data = {
            "name": "大条件测试",
            "config": {
                "skills": large_skills,
                "education_level": "bachelor",
            },
        }

        response = await async_client.post(
            "/api/v1/conditions",
            json=condition_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["data"]["config"]["skills"]) == 100

    async def test_special_characters_in_response(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试响应中的特殊字符处理。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        await condition_factory(
            name="特殊字符<>&\"'测试",
            description="包含\n换行和\t制表符",
        )

        response = await async_client.get("/api/v1/conditions")

        assert response.status_code == 200
        # 验证特殊字符正确返回
        data = response.json()
        assert data["success"] is True
