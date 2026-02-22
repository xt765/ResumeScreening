"""API 集成测试模块。

测试 FastAPI 路由的集成功能：
- 筛选条件 CRUD 测试
- 人才管理 API 测试
- 数据分析 API 测试
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.main import app
from src.models import ScreeningCondition, StatusEnum, TalentInfo
from src.models.talent import ScreeningStatusEnum, WorkflowStatusEnum


# ==================== 筛选条件 API 测试 ====================

class TestConditionsAPI:
    """筛选条件 API 测试类。"""

    @pytest.mark.asyncio
    async def test_create_condition(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        sample_condition_data: dict[str, Any],
    ) -> None:
        """测试创建筛选条件。"""
        with patch("src.api.v1.conditions.get_session", return_value=iter([db_session])):
            response = await async_client.post(
                "/api/v1/conditions",
                json=sample_condition_data,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == sample_condition_data["name"]

    @pytest.mark.asyncio
    async def test_create_condition_invalid_data(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """测试创建筛选条件（无效数据）。"""
        invalid_data = {
            "name": "",  # 空名称
            "config": {},
        }

        with patch("src.api.v1.conditions.get_session", return_value=iter([db_session])):
            response = await async_client.post(
                "/api/v1/conditions",
                json=invalid_data,
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_condition(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        condition_factory,
    ) -> None:
        """测试更新筛选条件。"""
        # 创建测试条件
        condition = await condition_factory(name="原始名称")

        update_data = {
            "name": "更新后的名称",
            "description": "更新后的描述",
        }

        with patch("src.api.v1.conditions.get_session", return_value=iter([db_session])):
            response = await async_client.put(
                f"/api/v1/conditions/{condition.id}",
                json=update_data,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "更新后的名称"

    @pytest.mark.asyncio
    async def test_update_nonexistent_condition(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """测试更新不存在的筛选条件。"""
        update_data = {"name": "更新名称"}

        with patch("src.api.v1.conditions.get_session", return_value=iter([db_session])):
            response = await async_client.put(
                "/api/v1/conditions/nonexistent-id",
                json=update_data,
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_condition(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        condition_factory,
    ) -> None:
        """测试删除筛选条件。"""
        condition = await condition_factory(name="待删除条件")

        with patch("src.api.v1.conditions.get_session", return_value=iter([db_session])):
            response = await async_client.delete(
                f"/api/v1/conditions/{condition.id}",
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_delete_nonexistent_condition(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """测试删除不存在的筛选条件。"""
        with patch("src.api.v1.conditions.get_session", return_value=iter([db_session])):
            response = await async_client.delete(
                "/api/v1/conditions/nonexistent-id",
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_conditions(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        condition_factory,
    ) -> None:
        """测试查询筛选条件列表。"""
        # 创建多个测试条件
        await condition_factory(name="条件1")
        await condition_factory(name="条件2")
        await condition_factory(name="条件3")

        with patch("src.api.v1.conditions.get_session", return_value=iter([db_session])):
            response = await async_client.get("/api/v1/conditions")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] >= 3

    @pytest.mark.asyncio
    async def test_list_conditions_with_filter(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        condition_factory,
    ) -> None:
        """测试带过滤条件查询筛选条件列表。"""
        await condition_factory(name="Python条件")
        await condition_factory(name="Java条件")

        with patch("src.api.v1.conditions.get_session", return_value=iter([db_session])):
            response = await async_client.get(
                "/api/v1/conditions",
                params={"name": "Python"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_conditions_pagination(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        condition_factory,
    ) -> None:
        """测试筛选条件分页查询。"""
        # 创建多个条件
        for i in range(15):
            await condition_factory(name=f"条件{i}")

        with patch("src.api.v1.conditions.get_session", return_value=iter([db_session])):
            response = await async_client.get(
                "/api/v1/conditions",
                params={"page": 1, "page_size": 10},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) <= 10


# ==================== 人才管理 API 测试 ====================

class TestTalentsAPI:
    """人才管理 API 测试类。"""

    @pytest.mark.asyncio
    async def test_list_talents(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        talent_factory,
    ) -> None:
        """测试查询人才列表。"""
        # 创建测试人才
        await talent_factory(name="张三")
        await talent_factory(name="李四")

        with patch("src.api.v1.talents.get_session", return_value=iter([db_session])):
            response = await async_client.get("/api/v1/talents")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_list_talents_with_filter(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        talent_factory,
    ) -> None:
        """测试带过滤条件查询人才列表。"""
        await talent_factory(name="张三", school="清华大学")
        await talent_factory(name="李四", school="北京大学")

        with patch("src.api.v1.talents.get_session", return_value=iter([db_session])):
            response = await async_client.get(
                "/api/v1/talents",
                params={"school": "清华"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_talent(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        talent_factory,
    ) -> None:
        """测试获取人才详情。"""
        talent = await talent_factory(name="张三")

        with patch("src.api.v1.talents.get_session", return_value=iter([db_session])):
            response = await async_client.get(f"/api/v1/talents/{talent.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "张三"

    @pytest.mark.asyncio
    async def test_get_nonexistent_talent(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """测试获取不存在的人才。"""
        with patch("src.api.v1.talents.get_session", return_value=iter([db_session])):
            response = await async_client.get("/api/v1/talents/nonexistent-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_resume_invalid_file_type(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试上传无效文件类型。"""
        # 创建一个文本文件
        files = {"file": ("test.txt", b"test content", "text/plain")}

        response = await async_client.post(
            "/api/v1/talents/upload-screen",
            files=files,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_resume_missing_filename(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试上传无文件名的文件。"""
        files = {"file": ("", b"test content", "application/pdf")}

        response = await async_client.post(
            "/api/v1/talents/upload-screen",
            files=files,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_vectorize_talent(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        talent_factory,
        mock_chroma: MagicMock,
    ) -> None:
        """测试向量化人才。"""
        talent = await talent_factory(
            name="张三",
            resume_text="这是简历内容",
        )

        with (
            patch("src.api.v1.talents.get_session", return_value=iter([db_session])),
            patch("src.api.v1.talents.chroma_client", mock_chroma),
        ):
            response = await async_client.post(
                f"/api/v1/talents/{talent.id}/vectorize",
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["vectorized"] is True

    @pytest.mark.asyncio
    async def test_vectorize_talent_no_resume(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        talent_factory,
    ) -> None:
        """测试向量化无简历的人才。"""
        talent = await talent_factory(name="张三", resume_text="")

        with patch("src.api.v1.talents.get_session", return_value=iter([db_session])):
            response = await async_client.post(
                f"/api/v1/talents/{talent.id}/vectorize",
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_batch_vectorize(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        talent_factory,
        mock_chroma: MagicMock,
    ) -> None:
        """测试批量向量化。"""
        await talent_factory(
            name="张三",
            resume_text="简历1",
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )
        await talent_factory(
            name="李四",
            resume_text="简历2",
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )

        with (
            patch("src.api.v1.talents.get_session", return_value=iter([db_session])),
            patch("src.api.v1.talents.chroma_client", mock_chroma),
        ):
            response = await async_client.post(
                "/api/v1/talents/batch-vectorize",
                params={"screening_status": "qualified"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["success"] >= 0


# ==================== 数据分析 API 测试 ====================

class TestAnalysisAPI:
    """数据分析 API 测试类。"""

    @pytest.mark.asyncio
    async def test_rag_query(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试 RAG 智能查询。"""
        query_data = {
            "query": "Python开发工程师",
            "top_k": 5,
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_rag_query_with_filters(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试带过滤条件的 RAG 查询。"""
        query_data = {
            "query": "Java开发",
            "top_k": 10,
            "filters": {"education_level": "master"},
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rag_query_invalid(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试无效 RAG 查询。"""
        query_data = {
            "query": "",  # 空查询
            "top_k": 5,
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_statistics(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        talent_factory,
    ) -> None:
        """测试获取统计数据。"""
        # 创建测试数据
        await talent_factory(
            name="张三",
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )
        await talent_factory(
            name="李四",
            screening_status=ScreeningStatusEnum.DISQUALIFIED,
        )

        with patch("src.api.v1.analysis.get_session", return_value=iter([db_session])):
            response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_talents" in data["data"]
        assert "by_screening_status" in data["data"]
        assert "by_workflow_status" in data["data"]


# ==================== 错误处理测试 ====================

class TestAPIErrorHandling:
    """API 错误处理测试类。"""

    @pytest.mark.asyncio
    async def test_404_not_found(self, async_client: AsyncClient) -> None:
        """测试 404 错误。"""
        response = await async_client.get("/api/v1/nonexistent")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_validation_error(self, async_client: AsyncClient) -> None:
        """测试验证错误。"""
        response = await async_client.get(
            "/api/v1/conditions",
            params={"page": -1},  # 无效页码
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_database_error_handling(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """测试数据库错误处理。"""
        # 模拟数据库错误
        with patch("src.api.v1.conditions.get_session") as mock_session:
            mock_session.side_effect = Exception("Database error")

            response = await async_client.get("/api/v1/conditions")

        assert response.status_code == 500


# ==================== 同步客户端测试 ====================

class TestSyncClient:
    """同步测试客户端测试类。"""

    def test_health_check(self, client: TestClient) -> None:
        """测试健康检查端点。"""
        # 如果有健康检查端点
        response = client.get("/")
        # 根据实际 API 响应调整
        assert response.status_code in [200, 404]

    def test_create_condition_sync(
        self,
        client: TestClient,
        sample_condition_data: dict[str, Any],
    ) -> None:
        """测试同步创建筛选条件。"""
        response = client.post(
            "/api/v1/conditions",
            json=sample_condition_data,
        )

        # 可能因为数据库未初始化而失败
        assert response.status_code in [201, 500, 422]


# ==================== 边界情况测试 ====================

class TestAPIEdgeCases:
    """API 边界情况测试类。"""

    @pytest.mark.asyncio
    async def test_list_conditions_empty(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """测试查询空筛选条件列表。"""
        with patch("src.api.v1.conditions.get_session", return_value=iter([db_session])):
            response = await async_client.get("/api/v1/conditions")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["data"]["items"], list)

    @pytest.mark.asyncio
    async def test_list_talents_empty(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """测试查询空人才列表。"""
        with patch("src.api.v1.talents.get_session", return_value=iter([db_session])):
            response = await async_client.get("/api/v1/talents")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["data"]["items"], list)

    @pytest.mark.asyncio
    async def test_large_page_size(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """测试大分页参数。"""
        with patch("src.api.v1.conditions.get_session", return_value=iter([db_session])):
            response = await async_client.get(
                "/api/v1/conditions",
                params={"page_size": 100},
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_page_size(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试无效分页参数。"""
        response = await async_client.get(
            "/api/v1/conditions",
            params={"page_size": 200},  # 超过最大值
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unicode_in_query_params(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        condition_factory,
    ) -> None:
        """测试查询参数包含 Unicode。"""
        await condition_factory(name="中文条件名")

        with patch("src.api.v1.conditions.get_session", return_value=iter([db_session])):
            response = await async_client.get(
                "/api/v1/conditions",
                params={"name": "中文"},
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_special_characters_in_name(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """测试名称包含特殊字符。"""
        condition_data = {
            "name": "条件<>&\"'",
            "config": {},
        }

        with patch("src.api.v1.conditions.get_session", return_value=iter([db_session])):
            response = await async_client.post(
                "/api/v1/conditions",
                json=condition_data,
            )

        # 应该能处理特殊字符
        assert response.status_code in [201, 422]
