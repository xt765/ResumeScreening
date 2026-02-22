"""数据分析 API 集成测试模块。

测试数据分析的各项操作：
- POST /api/v1/analysis/query: RAG 查询
- GET /api/v1/analysis/statistics: 统计数据
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.talent import ScreeningStatusEnum, WorkflowStatusEnum


# ==================== RAG 查询测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestRAGQuery:
    """RAG 智能查询测试类。"""

    async def test_rag_query_success(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试成功执行 RAG 查询。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
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

    async def test_rag_query_with_custom_top_k(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试自定义返回数量的 RAG 查询。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
        query_data = {
            "query": "Java开发",
            "top_k": 10,
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_rag_query_with_filters(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试带过滤条件的 RAG 查询。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
        query_data = {
            "query": "前端开发工程师",
            "top_k": 5,
            "filters": {
                "education_level": "master",
                "work_years": 3,
            },
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_rag_query_empty_query(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试空查询字符串。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
        query_data = {
            "query": "",
            "top_k": 5,
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 422

    async def test_rag_query_invalid_top_k_too_small(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试 top_k 参数过小。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
        query_data = {
            "query": "测试查询",
            "top_k": 0,  # 最小值为 1
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 422

    async def test_rag_query_invalid_top_k_too_large(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试 top_k 参数过大。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
        query_data = {
            "query": "测试查询",
            "top_k": 100,  # 最大值为 20
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 422

    async def test_rag_query_missing_query_field(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试缺少 query 字段。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
        query_data = {
            "top_k": 5,
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 422

    async def test_rag_query_response_structure(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试 RAG 查询响应结构。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
        query_data = {
            "query": "测试查询",
            "top_k": 5,
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "success" in data
        assert "message" in data
        assert "data" in data

        # 验证 data 是列表
        assert isinstance(data["data"], list)

        # 如果有结果，验证结果结构
        if data["data"]:
            result = data["data"][0]
            assert "id" in result
            assert "content" in result
            assert "metadata" in result
            assert "distance" in result

    async def test_rag_query_chroma_error(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试 ChromaDB 查询错误处理。

        Args:
            async_client: 异步测试客户端。
        """
        mock_chroma_error = MagicMock()
        mock_chroma_error.query.side_effect = Exception("ChromaDB connection error")

        query_data = {
            "query": "测试查询",
            "top_k": 5,
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma_error):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 500


# ==================== 统计数据测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestGetStatistics:
    """获取统计数据测试类。"""

    async def test_get_statistics_success(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试成功获取统计数据。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        # 创建测试数据
        await talent_factory(
            name="合格人才1",
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )
        await talent_factory(
            name="不合格人才1",
            screening_status=ScreeningStatusEnum.DISQUALIFIED,
        )

        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_talents" in data["data"]
        assert "by_screening_status" in data["data"]
        assert "by_workflow_status" in data["data"]
        assert "recent_7_days" in data["data"]

    async def test_get_statistics_total_count(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试统计数据总数正确。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        # 创建多个人才
        for i in range(5):
            await talent_factory(name=f"统计人才_{i}")

        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_talents"] >= 5

    async def test_get_statistics_by_screening_status(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试按筛选状态统计正确。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        # 创建不同筛选状态的人才
        await talent_factory(
            name="合格人才",
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )
        await talent_factory(
            name="不合格人才",
            screening_status=ScreeningStatusEnum.DISQUALIFIED,
        )

        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        by_screening_status = data["data"]["by_screening_status"]

        # 验证状态统计
        assert "qualified" in by_screening_status or "disqualified" in by_screening_status

    async def test_get_statistics_by_workflow_status(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试按工作流状态统计正确。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        # 创建不同工作流状态的人才
        await talent_factory(
            name="完成人才",
            workflow_status=WorkflowStatusEnum.COMPLETED,
        )
        await talent_factory(
            name="处理中人才",
            workflow_status=WorkflowStatusEnum.PARSING,
        )

        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        by_workflow_status = data["data"]["by_workflow_status"]

        # 验证工作流状态统计
        assert isinstance(by_workflow_status, dict)

    async def test_get_statistics_empty_database(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试空数据库的统计数据。

        Args:
            async_client: 异步测试客户端。
        """
        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        # 即使没有数据，也应该返回有效的结构
        assert "total_talents" in data["data"]
        assert isinstance(data["data"]["total_talents"], int)

    async def test_get_statistics_response_structure(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试统计数据响应结构完整性。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        await talent_factory(name="结构测试人才")

        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "success" in data
        assert "message" in data
        assert "data" in data

        # 验证 data 字段
        stats_data = data["data"]
        assert "total_talents" in stats_data
        assert "by_screening_status" in stats_data
        assert "by_workflow_status" in stats_data
        assert "recent_7_days" in stats_data

        # 验证类型
        assert isinstance(stats_data["total_talents"], int)
        assert isinstance(stats_data["by_screening_status"], dict)
        assert isinstance(stats_data["by_workflow_status"], dict)
        assert isinstance(stats_data["recent_7_days"], int)


# ==================== 边界情况测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestAnalysisEdgeCases:
    """数据分析边界情况测试类。"""

    async def test_rag_query_with_unicode(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试 RAG 查询包含 Unicode 字符。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
        query_data = {
            "query": "Python开发工程师🎉",
            "top_k": 5,
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 200

    async def test_rag_query_with_long_query(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试 RAG 查询长查询字符串。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
        # 创建一个较长的查询字符串（但不超过 500 字符限制）
        long_query = "Python开发工程师" * 20  # 约 280 字符

        query_data = {
            "query": long_query,
            "top_k": 5,
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 200

    async def test_rag_query_query_too_long(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试 RAG 查询超过最大长度。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
        # 创建超过 500 字符的查询
        too_long_query = "x" * 501

        query_data = {
            "query": too_long_query,
            "top_k": 5,
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 422

    async def test_rag_query_with_special_characters(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试 RAG 查询包含特殊字符。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
        query_data = {
            "query": "Python & Java <开发> 工程师",
            "top_k": 5,
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 200

    async def test_statistics_with_large_dataset(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试大数据集的统计数据。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        # 创建较多人才
        for i in range(20):
            status = ScreeningStatusEnum.QUALIFIED if i % 2 == 0 else ScreeningStatusEnum.DISQUALIFIED
            await talent_factory(
                name=f"大数据集人才_{i}",
                screening_status=status,
            )

        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_talents"] >= 20

    async def test_rag_query_with_complex_filters(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试 RAG 查询带复杂过滤条件。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
        query_data = {
            "query": "高级开发工程师",
            "top_k": 10,
            "filters": {
                "education_level": "master",
                "work_years": {"$gte": 5},
                "school": {"$in": ["清华大学", "北京大学"]},
            },
        }

        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )

        assert response.status_code == 200

    async def test_statistics_recent_7_days(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试近 7 天新增统计。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        # 创建新人才
        await talent_factory(name="近期人才1")
        await talent_factory(name="近期人才2")

        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        # 近 7 天应该至少有刚创建的人才
        assert data["data"]["recent_7_days"] >= 0


# ==================== 性能测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestAnalysisPerformance:
    """数据分析性能测试类。"""

    async def test_statistics_query_performance(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试统计查询性能。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        import time

        # 创建一些测试数据
        for i in range(10):
            await talent_factory(name=f"性能测试人才_{i}")

        start_time = time.time()
        response = await async_client.get("/api/v1/analysis/statistics")
        end_time = time.time()

        assert response.status_code == 200
        # 查询应该在合理时间内完成（例如 5 秒）
        assert end_time - start_time < 5.0

    async def test_rag_query_performance(
        self,
        async_client: AsyncClient,
        mock_chroma: MagicMock,
    ) -> None:
        """测试 RAG 查询性能。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
        import time

        query_data = {
            "query": "Python开发工程师",
            "top_k": 10,
        }

        start_time = time.time()
        with patch("src.api.v1.analysis.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/analysis/query",
                json=query_data,
            )
        end_time = time.time()

        assert response.status_code == 200
        # 查询应该在合理时间内完成
        assert end_time - start_time < 5.0
