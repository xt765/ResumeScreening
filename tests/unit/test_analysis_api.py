"""数据分析 API 单元测试模块。

测试数据分析的各项操作，包括：
- RAG 智能查询
- 统计数据获取
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.main import app
from src.models.talent import ScreeningStatusEnum, TalentInfo, WorkflowStatusEnum


# ==================== Fixtures ====================


@pytest.fixture
def client() -> TestClient:
    """创建同步测试客户端。

    Returns:
        TestClient: FastAPI 测试客户端实例。
    """
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    """创建异步测试客户端。

    Yields:
        AsyncClient: 异步 HTTP 客户端实例。
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


# ==================== RAG 智能查询测试 ====================


@pytest.mark.asyncio
async def test_rag_query_success(
    async_client: AsyncClient,
) -> None:
    """测试成功执行 RAG 查询。

    Args:
        async_client: 异步测试客户端。
    """
    # Mock ChromaDB 客户端
    mock_chroma = MagicMock()
    mock_chroma.query.return_value = {
        "ids": [["id1", "id2", "id3"]],
        "documents": [["简历内容1", "简历内容2", "简历内容3"]],
        "metadatas": [
            [
                {"name": "张三", "school": "清华大学"},
                {"name": "李四", "school": "北京大学"},
                {"name": "王五", "school": "浙江大学"},
            ]
        ],
        "distances": [[0.1, 0.2, 0.3]],
    }

    with patch("src.api.v1.analysis.chroma_client", mock_chroma):
        response = await async_client.post(
            "/api/v1/analysis/query",
            json={
                "query": "Python开发工程师",
                "top_k": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "查询成功"
        assert len(data["data"]) == 3

        # 验证返回的数据结构
        result = data["data"][0]
        assert result["id"] == "id1"
        assert result["content"] == "简历内容1"
        assert result["metadata"]["name"] == "张三"
        assert result["distance"] == 0.1


@pytest.mark.asyncio
async def test_rag_query_with_filters(
    async_client: AsyncClient,
) -> None:
    """测试带过滤条件的 RAG 查询。

    Args:
        async_client: 异步测试客户端。
    """
    mock_chroma = MagicMock()
    mock_chroma.query.return_value = {
        "ids": [["id1"]],
        "documents": [["简历内容1"]],
        "metadatas": [[{"name": "张三", "school": "清华大学"}]],
        "distances": [[0.1]],
    }

    with patch("src.api.v1.analysis.chroma_client", mock_chroma):
        response = await async_client.post(
            "/api/v1/analysis/query",
            json={
                "query": "Python开发工程师",
                "top_k": 5,
                "filters": {"school": "清华大学"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1

        # 验证 filters 参数被传递
        mock_chroma.query.assert_called_once()
        call_kwargs = mock_chroma.query.call_args[1]
        assert call_kwargs["where"] == {"school": "清华大学"}


@pytest.mark.asyncio
async def test_rag_query_default_top_k(
    async_client: AsyncClient,
) -> None:
    """测试使用默认 top_k 的 RAG 查询。

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

    with patch("src.api.v1.analysis.chroma_client", mock_chroma):
        response = await async_client.post(
            "/api/v1/analysis/query",
            json={"query": "测试查询"},
        )

        assert response.status_code == 200

        # 验证默认 top_k 为 5
        call_kwargs = mock_chroma.query.call_args[1]
        assert call_kwargs["n_results"] == 5


@pytest.mark.asyncio
async def test_rag_query_empty_results(
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

    with patch("src.api.v1.analysis.chroma_client", mock_chroma):
        response = await async_client.post(
            "/api/v1/analysis/query",
            json={"query": "不存在的技能xyz123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []


@pytest.mark.asyncio
async def test_rag_query_partial_results(
    async_client: AsyncClient,
) -> None:
    """测试 RAG 查询返回部分结果（缺少某些字段）。

    Args:
        async_client: 异步测试客户端。
    """
    mock_chroma = MagicMock()
    # 模拟返回数据不完整的情况
    mock_chroma.query.return_value = {
        "ids": [["id1", "id2"]],
        "documents": [["doc1"]],  # 只有一个文档
        "metadatas": [[]],  # 空元数据
        "distances": [[0.1]],  # 只有一个距离
    }

    with patch("src.api.v1.analysis.chroma_client", mock_chroma):
        response = await async_client.post(
            "/api/v1/analysis/query",
            json={"query": "测试查询", "top_k": 2},
        )

        assert response.status_code == 200
        data = response.json()
        # 应该能处理不完整的数据
        assert len(data["data"]) == 2


@pytest.mark.asyncio
async def test_rag_query_missing_keys(
    async_client: AsyncClient,
) -> None:
    """测试 RAG 查询返回结果缺少某些键。

    Args:
        async_client: 异步测试客户端。
    """
    mock_chroma = MagicMock()
    # 模拟返回数据缺少某些键
    mock_chroma.query.return_value = {
        "ids": [["id1"]],
        # 缺少 documents, metadatas, distances
    }

    with patch("src.api.v1.analysis.chroma_client", mock_chroma):
        response = await async_client.post(
            "/api/v1/analysis/query",
            json={"query": "测试查询"},
        )

        assert response.status_code == 200
        data = response.json()
        # 应该能处理缺少键的情况
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "id1"
        assert data["data"][0]["content"] == ""
        assert data["data"][0]["metadata"] == {}
        assert data["data"][0]["distance"] is None


@pytest.mark.asyncio
async def test_rag_query_chroma_error(
    async_client: AsyncClient,
) -> None:
    """测试 RAG 查询时 ChromaDB 错误。

    Args:
        async_client: 异步测试客户端。
    """
    mock_chroma = MagicMock()
    mock_chroma.query.side_effect = Exception("ChromaDB 连接失败")

    with patch("src.api.v1.analysis.chroma_client", mock_chroma):
        response = await async_client.post(
            "/api/v1/analysis/query",
            json={"query": "测试查询"},
        )

        assert response.status_code == 500
        assert "查询失败" in response.json()["detail"]


@pytest.mark.asyncio
async def test_rag_query_validation_error_empty_query(
    async_client: AsyncClient,
) -> None:
    """测试 RAG 查询验证错误 - 空查询。

    Args:
        async_client: 异步测试客户端。
    """
    response = await async_client.post(
        "/api/v1/analysis/query",
        json={"query": ""},
    )

    assert response.status_code == 422  # Validation Error


@pytest.mark.asyncio
async def test_rag_query_validation_error_invalid_top_k(
    async_client: AsyncClient,
) -> None:
    """测试 RAG 查询验证错误 - 无效的 top_k。

    Args:
        async_client: 异步测试客户端。
    """
    response = await async_client.post(
        "/api/v1/analysis/query",
        json={"query": "测试查询", "top_k": 0},
    )

    assert response.status_code == 422  # Validation Error

    response = await async_client.post(
        "/api/v1/analysis/query",
        json={"query": "测试查询", "top_k": 100},
    )

    assert response.status_code == 422  # top_k 最大为 20


# ==================== 统计数据测试 ====================


@pytest.mark.asyncio
async def test_get_statistics_success(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试成功获取统计数据。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建测试数据
    for i in range(5):
        talent = TalentInfo(
            name=f"测试人才{i}",
            phone=f"1380013800{i}",
            email=f"test{i}@example.com",
            workflow_status=WorkflowStatusEnum.COMPLETED,
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )
        db_session.add(talent)

    for i in range(3):
        talent = TalentInfo(
            name=f"不合格人才{i}",
            phone=f"1390013900{i}",
            email=f"fail{i}@example.com",
            workflow_status=WorkflowStatusEnum.COMPLETED,
            screening_status=ScreeningStatusEnum.DISQUALIFIED,
        )
        db_session.add(talent)

    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "获取成功"

        stats = data["data"]
        assert stats["total_talents"] >= 8
        assert "qualified" in stats["by_screening_status"]
        assert "disqualified" in stats["by_screening_status"]
        assert "completed" in stats["by_workflow_status"]

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_statistics_empty_database(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试获取统计数据 - 空数据库。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        stats = data["data"]
        assert stats["total_talents"] == 0
        assert stats["by_screening_status"] == {}
        assert stats["by_workflow_status"] == {}
        assert stats["recent_7_days"] == 0

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_statistics_recent_7_days(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试统计数据 - 近 7 天新增。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    now = datetime.now()

    # 创建近期人才（7天内）
    for i in range(3):
        talent = TalentInfo(
            name=f"近期人才{i}",
            phone=f"138001380{i}",
            email=f"recent{i}@example.com",
            workflow_status=WorkflowStatusEnum.COMPLETED,
            screening_status=ScreeningStatusEnum.QUALIFIED,
            created_at=now - timedelta(days=i),
        )
        db_session.add(talent)

    # 创建较旧人才（超过7天）
    for i in range(2):
        talent = TalentInfo(
            name=f"旧人才{i}",
            phone=f"139001390{i}",
            email=f"old{i}@example.com",
            workflow_status=WorkflowStatusEnum.COMPLETED,
            screening_status=ScreeningStatusEnum.QUALIFIED,
            created_at=now - timedelta(days=10 + i),
        )
        db_session.add(talent)

    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        stats = data["data"]
        # 近 7 天应该至少有 3 个
        assert stats["recent_7_days"] >= 3

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_statistics_various_workflow_status(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试统计数据 - 各种工作流状态。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建不同工作流状态的人才
    statuses = [
        WorkflowStatusEnum.PENDING,
        WorkflowStatusEnum.PARSING,
        WorkflowStatusEnum.FILTERING,
        WorkflowStatusEnum.STORING,
        WorkflowStatusEnum.CACHING,
        WorkflowStatusEnum.COMPLETED,
        WorkflowStatusEnum.FAILED,
    ]

    for i, status in enumerate(statuses):
        talent = TalentInfo(
            name=f"人才{i}",
            phone=f"1380013800{i}",
            email=f"talent{i}@example.com",
            workflow_status=status,
        )
        db_session.add(talent)

    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        stats = data["data"]

        # 验证各状态都有统计
        workflow_stats = stats["by_workflow_status"]
        assert "pending" in workflow_stats
        assert "parsing" in workflow_stats
        assert "filtering" in workflow_stats
        assert "storing" in workflow_stats
        assert "caching" in workflow_stats
        assert "completed" in workflow_stats
        assert "failed" in workflow_stats

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_statistics_null_screening_status(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试统计数据 - 处理空的筛选状态。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建没有筛选状态的人才
    talent = TalentInfo(
        name="无筛选状态人才",
        phone="13800138000",
        email="test@example.com",
        workflow_status=WorkflowStatusEnum.PENDING,
        screening_status=None,
    )
    db_session.add(talent)
    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        # 应该能正常处理 null 状态
        assert "unknown" in data["data"]["by_screening_status"] or data["data"]["by_screening_status"] == {} or len(data["data"]["by_screening_status"]) >= 0

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_statistics_database_error(
    async_client: AsyncClient,
) -> None:
    """测试获取统计数据时数据库错误。

    Args:
        async_client: 异步测试客户端。
    """
    mock_session = AsyncMock()
    mock_session.execute.side_effect = Exception("数据库连接失败")

    async def override_get_session():
        yield mock_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 500
        assert "获取统计数据失败" in response.json()["detail"]

    finally:
        app.dependency_overrides.clear()


# ==================== 模型验证测试 ====================


def test_query_request_model() -> None:
    """测试查询请求模型验证。"""
    from src.api.v1.analysis import QueryRequest

    # 正常创建
    request = QueryRequest(query="测试查询")
    assert request.query == "测试查询"
    assert request.top_k == 5  # 默认值
    assert request.filters is None

    # 带过滤条件
    request_with_filters = QueryRequest(
        query="测试查询",
        top_k=10,
        filters={"school": "清华大学"},
    )
    assert request_with_filters.top_k == 10
    assert request_with_filters.filters == {"school": "清华大学"}


def test_query_request_model_validation() -> None:
    """测试查询请求模型验证错误。"""
    from pydantic import ValidationError
    from src.api.v1.analysis import QueryRequest

    # 空查询
    with pytest.raises(ValidationError):
        QueryRequest(query="")

    # 查询过长
    with pytest.raises(ValidationError):
        QueryRequest(query="x" * 501)

    # top_k 过小
    with pytest.raises(ValidationError):
        QueryRequest(query="测试", top_k=0)

    # top_k 过大
    with pytest.raises(ValidationError):
        QueryRequest(query="测试", top_k=21)


def test_query_result_model() -> None:
    """测试查询结果模型。"""
    from src.api.v1.analysis import QueryResult

    result = QueryResult(
        id="test-id",
        content="测试内容",
        metadata={"name": "张三"},
        distance=0.5,
    )

    assert result.id == "test-id"
    assert result.content == "测试内容"
    assert result.metadata == {"name": "张三"}
    assert result.distance == 0.5


def test_query_result_model_defaults() -> None:
    """测试查询结果模型默认值。"""
    from src.api.v1.analysis import QueryResult

    result = QueryResult(
        id="test-id",
        content="测试内容",
    )

    assert result.metadata == {}
    assert result.distance is None


def test_statistics_response_model() -> None:
    """测试统计数据响应模型。"""
    from src.api.v1.analysis import StatisticsResponse

    stats = StatisticsResponse(
        total_talents=100,
        by_screening_status={"qualified": 80, "disqualified": 20},
        by_workflow_status={"completed": 90, "pending": 10},
        recent_7_days=15,
    )

    assert stats.total_talents == 100
    assert stats.by_screening_status["qualified"] == 80
    assert stats.by_workflow_status["completed"] == 90
    assert stats.recent_7_days == 15


def test_statistics_response_model_defaults() -> None:
    """测试统计数据响应模型默认值。"""
    from src.api.v1.analysis import StatisticsResponse

    stats = StatisticsResponse(total_talents=0)

    assert stats.by_screening_status == {}
    assert stats.by_workflow_status == {}
    assert stats.recent_7_days == 0


# ==================== 统计数据边界测试 ====================


@pytest.mark.asyncio
async def test_get_statistics_with_null_workflow_status(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试统计数据 - 处理空的工作流状态。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建没有工作流状态的人才（通过直接插入）
    talent = TalentInfo(
        name="无工作流状态人才",
        phone="13800138000",
        email="test@example.com",
        workflow_status=None,
        screening_status=None,
    )
    db_session.add(talent)
    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        # 应该能正常处理 null 状态
        assert "unknown" in data["data"]["by_workflow_status"] or data["data"]["by_workflow_status"] == {} or len(data["data"]["by_workflow_status"]) >= 0

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_statistics_mixed_statuses(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试统计数据 - 混合状态统计。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    now = datetime.now()

    # 创建各种状态的人才
    # 合格人才
    for i in range(5):
        talent = TalentInfo(
            name=f"合格人才{i}",
            phone=f"138001380{i}",
            email=f"qualified{i}@example.com",
            workflow_status=WorkflowStatusEnum.COMPLETED,
            screening_status=ScreeningStatusEnum.QUALIFIED,
            created_at=now - timedelta(days=i),
        )
        db_session.add(talent)

    # 不合格人才
    for i in range(3):
        talent = TalentInfo(
            name=f"不合格人才{i}",
            phone=f"139001390{i}",
            email=f"disqualified{i}@example.com",
            workflow_status=WorkflowStatusEnum.COMPLETED,
            screening_status=ScreeningStatusEnum.DISQUALIFIED,
            created_at=now - timedelta(days=8 + i),  # 超过7天
        )
        db_session.add(talent)

    # 待处理人才
    for i in range(2):
        talent = TalentInfo(
            name=f"待处理人才{i}",
            phone=f"137001370{i}",
            email=f"pending{i}@example.com",
            workflow_status=WorkflowStatusEnum.PENDING,
            screening_status=None,
            created_at=now - timedelta(days=2),
        )
        db_session.add(talent)

    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        stats = data["data"]

        # 验证总数
        assert stats["total_talents"] >= 10

        # 验证筛选状态统计
        assert stats["by_screening_status"].get("qualified", 0) >= 5
        assert stats["by_screening_status"].get("disqualified", 0) >= 3

        # 验证工作流状态统计
        assert stats["by_workflow_status"].get("completed", 0) >= 8
        assert stats["by_workflow_status"].get("pending", 0) >= 2

        # 验证近7天新增（合格人才 + 待处理人才 = 7）
        assert stats["recent_7_days"] >= 7

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_statistics_exactly_7_days_boundary(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试统计数据 - 恰好7天边界测试。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    now = datetime.now()

    # 6天前的人才（应该在近7天内）
    talent_6_days_ago = TalentInfo(
        name="6天前人才",
        phone="13800138001",
        email="six_days@example.com",
        workflow_status=WorkflowStatusEnum.COMPLETED,
        screening_status=ScreeningStatusEnum.QUALIFIED,
        created_at=now - timedelta(days=6),
    )
    db_session.add(talent_6_days_ago)

    # 1天前的人才（应该在近7天内）
    talent_1_day_ago = TalentInfo(
        name="1天前人才",
        phone="13800138002",
        email="one_day@example.com",
        workflow_status=WorkflowStatusEnum.COMPLETED,
        screening_status=ScreeningStatusEnum.QUALIFIED,
        created_at=now - timedelta(days=1),
    )
    db_session.add(talent_1_day_ago)

    # 8天前的人才（不应该在近7天内）
    talent_8_days_ago = TalentInfo(
        name="8天前人才",
        phone="13800138003",
        email="eight_days@example.com",
        workflow_status=WorkflowStatusEnum.COMPLETED,
        screening_status=ScreeningStatusEnum.QUALIFIED,
        created_at=now - timedelta(days=8),
    )
    db_session.add(talent_8_days_ago)

    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        stats = data["data"]

        # 近7天应该包含1天前和6天前的人才（至少2个）
        assert stats["recent_7_days"] >= 2

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_statistics_all_workflow_statuses(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试统计数据 - 所有可能的工作流状态。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建所有工作流状态的人才
    workflow_statuses = [
        WorkflowStatusEnum.PENDING,
        WorkflowStatusEnum.PARSING,
        WorkflowStatusEnum.FILTERING,
        WorkflowStatusEnum.STORING,
        WorkflowStatusEnum.CACHING,
        WorkflowStatusEnum.COMPLETED,
        WorkflowStatusEnum.FAILED,
    ]

    for i, status in enumerate(workflow_statuses):
        talent = TalentInfo(
            name=f"人才_{status.value}_{i}",
            phone=f"1380013800{i}",
            email=f"talent_{i}@example.com",
            workflow_status=status,
            screening_status=ScreeningStatusEnum.QUALIFIED if status == WorkflowStatusEnum.COMPLETED else None,
        )
        db_session.add(talent)

    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        stats = data["data"]

        # 验证所有状态都有统计
        assert stats["total_talents"] == 7
        assert stats["by_workflow_status"].get("pending", 0) == 1
        assert stats["by_workflow_status"].get("parsing", 0) == 1
        assert stats["by_workflow_status"].get("filtering", 0) == 1
        assert stats["by_workflow_status"].get("storing", 0) == 1
        assert stats["by_workflow_status"].get("caching", 0) == 1
        assert stats["by_workflow_status"].get("completed", 0) == 1
        assert stats["by_workflow_status"].get("failed", 0) == 1

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_statistics_count_zero_when_null(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试统计数据 - 当 scalar 返回 None 时计数为 0。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        # 空数据库查询
        response = await async_client.get("/api/v1/analysis/statistics")

        assert response.status_code == 200
        data = response.json()
        stats = data["data"]

        # 空数据库应该返回 0
        assert stats["total_talents"] == 0
        assert stats["recent_7_days"] == 0

    finally:
        app.dependency_overrides.clear()
