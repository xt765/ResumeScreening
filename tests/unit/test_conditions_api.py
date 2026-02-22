"""筛选条件 API 单元测试模块。

测试筛选条件的 CRUD 操作，包括：
- 创建筛选条件
- 更新筛选条件
- 删除筛选条件（逻辑删除）
- 分页查询筛选条件
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.main import app
from src.models.condition import ScreeningCondition, StatusEnum
from src.schemas.condition import ConditionConfig, EducationLevel, SchoolTier


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


@pytest.fixture
def sample_condition_create() -> dict:
    """提供创建筛选条件的示例数据。

    Returns:
        dict: 创建请求数据字典。
    """
    return {
        "name": "高级Python开发工程师",
        "description": "用于筛选高级Python开发工程师的条件",
        "config": {
            "skills": ["Python", "FastAPI", "SQL"],
            "education_level": "bachelor",
            "experience_years": 3,
            "major": ["计算机科学与技术", "软件工程"],
            "school_tier": "key",
        },
        "is_active": True,
    }


@pytest.fixture
def sample_condition_update() -> dict:
    """提供更新筛选条件的示例数据。

    Returns:
        dict: 更新请求数据字典。
    """
    return {
        "name": "高级Python开发工程师（更新）",
        "description": "更新后的筛选条件描述",
        "config": {
            "skills": ["Python", "FastAPI", "SQL", "Docker"],
            "education_level": "master",
            "experience_years": 5,
            "major": ["计算机科学与技术"],
            "school_tier": "top",
        },
        "is_active": False,
    }


# ==================== 创建筛选条件测试 ====================


@pytest.mark.asyncio
async def test_create_condition_success(
    db_session: AsyncSession,
    async_client: AsyncClient,
    sample_condition_create: dict,
) -> None:
    """测试成功创建筛选条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
        sample_condition_create: 创建请求数据。
    """
    # Mock 数据库会话依赖
    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.post(
            "/api/v1/conditions",
            json=sample_condition_create,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "筛选条件创建成功"
        assert data["data"]["name"] == sample_condition_create["name"]
        assert data["data"]["description"] == sample_condition_create["description"]
        assert data["data"]["is_active"] is True

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_condition_with_inactive_status(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试创建不激活状态的筛选条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        create_data = {
            "name": "测试条件-不激活",
            "description": "测试描述",
            "config": {
                "skills": ["Python"],
                "education_level": "bachelor",
            },
            "is_active": False,
        }

        response = await async_client.post(
            "/api/v1/conditions",
            json=create_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["is_active"] is False

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_condition_without_description(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试创建没有描述的筛选条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        create_data = {
            "name": "测试条件-无描述",
            "config": {
                "skills": ["Python"],
            },
        }

        response = await async_client.post(
            "/api/v1/conditions",
            json=create_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["description"] == ""

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_condition_database_error(
    db_session: AsyncSession,
    async_client: AsyncClient,
    sample_condition_create: dict,
) -> None:
    """测试创建筛选条件时数据库错误。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
        sample_condition_create: 创建请求数据。
    """
    # 创建一个会抛出异常的 mock session
    mock_session = AsyncMock()
    mock_session.add.side_effect = Exception("数据库连接失败")

    async def override_get_session():
        yield mock_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.post(
            "/api/v1/conditions",
            json=sample_condition_create,
        )

        assert response.status_code == 500
        assert "创建筛选条件失败" in response.json()["detail"]

    finally:
        app.dependency_overrides.clear()


# ==================== 更新筛选条件测试 ====================


@pytest.mark.asyncio
async def test_update_condition_success(
    db_session: AsyncSession,
    async_client: AsyncClient,
    sample_condition_update: dict,
) -> None:
    """测试成功更新筛选条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
        sample_condition_update: 更新请求数据。
    """
    # 先创建一个条件
    condition = ScreeningCondition(
        name="原始条件",
        description="原始描述",
        conditions={
            "skills": ["Python"],
            "education_level": "bachelor",
        },
        status=StatusEnum.ACTIVE,
    )
    db_session.add(condition)
    await db_session.flush()
    await db_session.refresh(condition)
    condition_id = condition.id

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.put(
            f"/api/v1/conditions/{condition_id}",
            json=sample_condition_update,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "筛选条件更新成功"
        assert data["data"]["name"] == sample_condition_update["name"]
        assert data["data"]["is_active"] is False

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_condition_partial(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试部分更新筛选条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 先创建一个条件
    condition = ScreeningCondition(
        name="原始条件",
        description="原始描述",
        conditions={
            "skills": ["Python"],
            "education_level": "bachelor",
        },
        status=StatusEnum.ACTIVE,
    )
    db_session.add(condition)
    await db_session.flush()
    await db_session.refresh(condition)
    condition_id = condition.id

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        # 只更新名称
        update_data = {"name": "更新后的名称"}

        response = await async_client.put(
            f"/api/v1/conditions/{condition_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "更新后的名称"
        assert data["data"]["description"] == "原始描述"  # 描述保持不变

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_condition_all_fields(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试更新筛选条件的所有字段。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 先创建一个条件
    condition = ScreeningCondition(
        name="原始条件",
        description="原始描述",
        conditions={
            "skills": ["Python"],
            "education_level": "bachelor",
        },
        status=StatusEnum.ACTIVE,
    )
    db_session.add(condition)
    await db_session.flush()
    await db_session.refresh(condition)
    condition_id = condition.id

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        # 更新所有字段
        update_data = {
            "name": "新名称",
            "description": "新描述",
            "config": {
                "skills": ["Java", "Go"],
                "education_level": "master",
            },
            "is_active": False,
        }

        response = await async_client.put(
            f"/api/v1/conditions/{condition_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "新名称"
        assert data["data"]["description"] == "新描述"
        assert data["data"]["config"]["skills"] == ["Java", "Go"]
        assert data["data"]["is_active"] is False

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_condition_only_description(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试只更新描述字段。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 先创建一个条件
    condition = ScreeningCondition(
        name="原始条件",
        description="原始描述",
        conditions={"skills": ["Python"]},
        status=StatusEnum.ACTIVE,
    )
    db_session.add(condition)
    await db_session.flush()
    await db_session.refresh(condition)
    condition_id = condition.id

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        update_data = {"description": "更新后的描述"}

        response = await async_client.put(
            f"/api/v1/conditions/{condition_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["description"] == "更新后的描述"
        assert data["data"]["name"] == "原始条件"  # 名称保持不变

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_condition_only_config(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试只更新配置字段。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 先创建一个条件
    condition = ScreeningCondition(
        name="原始条件",
        description="原始描述",
        conditions={"skills": ["Python"]},
        status=StatusEnum.ACTIVE,
    )
    db_session.add(condition)
    await db_session.flush()
    await db_session.refresh(condition)
    condition_id = condition.id

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        update_data = {
            "config": {
                "skills": ["Rust", "C++"],
                "experience_years": 5,
            }
        }

        response = await async_client.put(
            f"/api/v1/conditions/{condition_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["config"]["skills"] == ["Rust", "C++"]

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_condition_only_is_active(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试只更新激活状态字段。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 先创建一个条件
    condition = ScreeningCondition(
        name="原始条件",
        description="原始描述",
        conditions={"skills": ["Python"]},
        status=StatusEnum.ACTIVE,
    )
    db_session.add(condition)
    await db_session.flush()
    await db_session.refresh(condition)
    condition_id = condition.id

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        update_data = {"is_active": False}

        response = await async_client.put(
            f"/api/v1/conditions/{condition_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["is_active"] is False

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_condition_description_none(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试更新描述为 None。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 先创建一个条件
    condition = ScreeningCondition(
        name="原始条件",
        description="原始描述",
        conditions={"skills": ["Python"]},
        status=StatusEnum.ACTIVE,
    )
    db_session.add(condition)
    await db_session.flush()
    await db_session.refresh(condition)
    condition_id = condition.id

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        update_data = {"description": None}

        response = await async_client.put(
            f"/api/v1/conditions/{condition_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        # 描述为 None 时应该被转换为空字符串
        assert data["data"]["description"] == ""

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_condition_not_found(
    db_session: AsyncSession,
    async_client: AsyncClient,
    sample_condition_update: dict,
) -> None:
    """测试更新不存在的筛选条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
        sample_condition_update: 更新请求数据。
    """
    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        fake_id = str(uuid4())
        response = await async_client.put(
            f"/api/v1/conditions/{fake_id}",
            json=sample_condition_update,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "筛选条件不存在"

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_condition_deleted(
    db_session: AsyncSession,
    async_client: AsyncClient,
    sample_condition_update: dict,
) -> None:
    """测试更新已删除的筛选条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
        sample_condition_update: 更新请求数据。
    """
    # 创建一个已删除的条件
    condition = ScreeningCondition(
        name="已删除条件",
        description="描述",
        conditions={"skills": ["Python"]},
        status=StatusEnum.DELETED,
    )
    db_session.add(condition)
    await db_session.flush()
    await db_session.refresh(condition)
    condition_id = condition.id

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.put(
            f"/api/v1/conditions/{condition_id}",
            json=sample_condition_update,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "筛选条件不存在"

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_condition_database_error(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试更新筛选条件时数据库错误。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建一个条件用于获取 ID
    condition = ScreeningCondition(
        name="测试条件",
        description="描述",
        conditions={"skills": ["Python"]},
        status=StatusEnum.ACTIVE,
    )
    db_session.add(condition)
    await db_session.flush()
    await db_session.refresh(condition)
    condition_id = condition.id

    # 创建一个会抛出异常的 mock session
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock()
    mock_session.execute.return_value.scalar_one_or_none.return_value = condition
    mock_session.flush.side_effect = Exception("数据库错误")

    async def override_get_session():
        yield mock_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.put(
            f"/api/v1/conditions/{condition_id}",
            json={"name": "新名称"},
        )

        assert response.status_code == 500
        assert "更新筛选条件失败" in response.json()["detail"]

    finally:
        app.dependency_overrides.clear()


# ==================== 删除筛选条件测试 ====================


@pytest.mark.asyncio
async def test_delete_condition_success(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试成功删除筛选条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 先创建一个条件
    condition = ScreeningCondition(
        name="待删除条件",
        description="描述",
        conditions={"skills": ["Python"]},
        status=StatusEnum.ACTIVE,
    )
    db_session.add(condition)
    await db_session.flush()
    await db_session.refresh(condition)
    condition_id = condition.id

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.delete(
            f"/api/v1/conditions/{condition_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "筛选条件删除成功"
        assert data["data"] is None

        # 验证状态已变为 DELETED
        await db_session.refresh(condition)
        assert condition.status == StatusEnum.DELETED

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_condition_inactive_status(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试删除停用状态的筛选条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 先创建一个停用状态的条件
    condition = ScreeningCondition(
        name="停用条件",
        description="描述",
        conditions={"skills": ["Python"]},
        status=StatusEnum.INACTIVE,
    )
    db_session.add(condition)
    await db_session.flush()
    await db_session.refresh(condition)
    condition_id = condition.id

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.delete(
            f"/api/v1/conditions/{condition_id}"
        )

        assert response.status_code == 200
        # 验证状态已变为 DELETED
        await db_session.refresh(condition)
        assert condition.status == StatusEnum.DELETED

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_condition_not_found(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试删除不存在的筛选条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        fake_id = str(uuid4())
        response = await async_client.delete(
            f"/api/v1/conditions/{fake_id}"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "筛选条件不存在"

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_condition_already_deleted(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试删除已删除的筛选条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建一个已删除的条件
    condition = ScreeningCondition(
        name="已删除条件",
        description="描述",
        conditions={"skills": ["Python"]},
        status=StatusEnum.DELETED,
    )
    db_session.add(condition)
    await db_session.flush()
    await db_session.refresh(condition)
    condition_id = condition.id

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.delete(
            f"/api/v1/conditions/{condition_id}"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "筛选条件不存在"

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_condition_database_error(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试删除筛选条件时数据库错误。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建一个条件用于获取 ID
    condition = ScreeningCondition(
        name="测试条件",
        description="描述",
        conditions={"skills": ["Python"]},
        status=StatusEnum.ACTIVE,
    )
    db_session.add(condition)
    await db_session.flush()
    await db_session.refresh(condition)
    condition_id = condition.id

    # 创建一个会抛出异常的 mock session
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock()
    mock_session.execute.return_value.scalar_one_or_none.return_value = condition
    mock_session.flush.side_effect = Exception("数据库错误")

    async def override_get_session():
        yield mock_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.delete(
            f"/api/v1/conditions/{condition_id}"
        )

        assert response.status_code == 500
        assert "删除筛选条件失败" in response.json()["detail"]

    finally:
        app.dependency_overrides.clear()


# ==================== 分页查询筛选条件测试 ====================


@pytest.mark.asyncio
async def test_list_conditions_success(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试成功分页查询筛选条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建多个条件
    for i in range(3):
        condition = ScreeningCondition(
            name=f"测试条件{i}",
            description=f"描述{i}",
            conditions={"skills": ["Python"]},
            status=StatusEnum.ACTIVE,
        )
        db_session.add(condition)
    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.get(
            "/api/v1/conditions",
            params={"page": 1, "page_size": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "查询成功"
        assert data["data"]["total"] >= 3
        assert data["data"]["page"] == 1
        assert data["data"]["page_size"] == 10

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_conditions_with_name_filter(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试按名称模糊查询筛选条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建不同名称的条件
    condition1 = ScreeningCondition(
        name="Python开发工程师",
        description="描述1",
        conditions={"skills": ["Python"]},
        status=StatusEnum.ACTIVE,
    )
    condition2 = ScreeningCondition(
        name="Java开发工程师",
        description="描述2",
        conditions={"skills": ["Java"]},
        status=StatusEnum.ACTIVE,
    )
    db_session.add_all([condition1, condition2])
    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.get(
            "/api/v1/conditions",
            params={"name": "Python"},
        )

        assert response.status_code == 200
        data = response.json()
        # 应该只返回包含 Python 的条件
        for item in data["data"]["items"]:
            assert "Python" in item["name"]

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_conditions_with_status_filter(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试按状态筛选查询筛选条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建不同状态的条件
    condition1 = ScreeningCondition(
        name="活跃条件",
        description="描述1",
        conditions={"skills": ["Python"]},
        status=StatusEnum.ACTIVE,
    )
    condition2 = ScreeningCondition(
        name="停用条件",
        description="描述2",
        conditions={"skills": ["Java"]},
        status=StatusEnum.INACTIVE,
    )
    condition3 = ScreeningCondition(
        name="已删除条件",
        description="描述3",
        conditions={"skills": ["Go"]},
        status=StatusEnum.DELETED,
    )
    db_session.add_all([condition1, condition2, condition3])
    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        # 查询活跃状态
        response = await async_client.get(
            "/api/v1/conditions",
            params={"statuses": ["active"]},
        )

        assert response.status_code == 200
        data = response.json()
        # 默认排除已删除，所以应该只有 active 和 inactive
        # 加上状态筛选后只有 active
        for item in data["data"]["items"]:
            assert item["is_active"] is True

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_conditions_pagination(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试分页功能。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建多个条件
    for i in range(15):
        condition = ScreeningCondition(
            name=f"分页测试条件{i:02d}",
            description=f"描述{i}",
            conditions={"skills": ["Python"]},
            status=StatusEnum.ACTIVE,
        )
        db_session.add(condition)
    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        # 第一页
        response = await async_client.get(
            "/api/v1/conditions",
            params={"page": 1, "page_size": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 5
        assert data["data"]["page"] == 1
        assert data["data"]["total_pages"] >= 3

        # 第二页
        response = await async_client.get(
            "/api/v1/conditions",
            params={"page": 2, "page_size": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 5
        assert data["data"]["page"] == 2

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_conditions_empty(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试查询空列表。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.get(
            "/api/v1/conditions",
            params={"name": "不存在的条件名称xyz"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 0
        assert data["data"]["items"] == []
        assert data["data"]["total_pages"] == 0

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_conditions_exclude_deleted(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试查询排除已删除的条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建活跃和已删除的条件
    condition1 = ScreeningCondition(
        name="活跃条件",
        description="描述1",
        conditions={"skills": ["Python"]},
        status=StatusEnum.ACTIVE,
    )
    condition2 = ScreeningCondition(
        name="已删除条件",
        description="描述2",
        conditions={"skills": ["Java"]},
        status=StatusEnum.DELETED,
    )
    db_session.add_all([condition1, condition2])
    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.get("/api/v1/conditions")

        assert response.status_code == 200
        data = response.json()
        # 已删除的条件不应该出现在结果中
        for item in data["data"]["items"]:
            assert item["name"] != "已删除条件"

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_conditions_database_error(
    async_client: AsyncClient,
) -> None:
    """测试查询时数据库错误。

    Args:
        async_client: 异步测试客户端。
    """
    # 创建一个会抛出异常的 mock session
    mock_session = AsyncMock()
    mock_session.execute.side_effect = Exception("数据库连接失败")

    async def override_get_session():
        yield mock_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        response = await async_client.get("/api/v1/conditions")

        assert response.status_code == 500
        assert "查询筛选条件失败" in response.json()["detail"]

    finally:
        app.dependency_overrides.clear()


# ==================== 辅助函数测试 ====================


def test_map_to_response() -> None:
    """测试模型映射函数。"""
    from datetime import datetime

    from src.api.v1.conditions import _map_to_response

    condition = ScreeningCondition(
        id=str(uuid4()),
        name="测试条件",
        description="测试描述",
        conditions={
            "skills": ["Python", "Java"],
            "education_level": "master",
            "experience_years": 5,
        },
        status=StatusEnum.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    response = _map_to_response(condition)

    assert response.id == condition.id
    assert response.name == "测试条件"
    assert response.description == "测试描述"
    assert response.is_active is True
    assert response.config.skills == ["Python", "Java"]


def test_map_to_response_inactive() -> None:
    """测试模型映射函数 - 停用状态。"""
    from datetime import datetime

    from src.api.v1.conditions import _map_to_response

    condition = ScreeningCondition(
        id=str(uuid4()),
        name="测试条件",
        description="测试描述",
        conditions={"skills": ["Python"]},
        status=StatusEnum.INACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    response = _map_to_response(condition)

    assert response.is_active is False


def test_map_to_response_none_description() -> None:
    """测试模型映射函数 - 描述为 None。"""
    from datetime import datetime

    from src.api.v1.conditions import _map_to_response

    condition = ScreeningCondition(
        id=str(uuid4()),
        name="测试条件",
        description=None,
        conditions={"skills": ["Python"]},
        status=StatusEnum.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    response = _map_to_response(condition)

    assert response.description == ""


# ==================== 分页查询边界测试 ====================


@pytest.mark.asyncio
async def test_list_conditions_total_pages_calculation(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试分页查询时总页数计算。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建 23 个条件，测试总页数计算
    for i in range(23):
        condition = ScreeningCondition(
            name=f"分页计算条件{i:02d}",
            description=f"描述{i}",
            conditions={"skills": ["Python"]},
            status=StatusEnum.ACTIVE,
        )
        db_session.add(condition)
    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        # 使用 page_size=10，应该有 3 页
        response = await async_client.get(
            "/api/v1/conditions",
            params={"page": 1, "page_size": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 23
        assert data["data"]["total_pages"] == 3
        assert len(data["data"]["items"]) == 10

        # 第三页应该只有 3 条
        response = await async_client.get(
            "/api/v1/conditions",
            params={"page": 3, "page_size": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 3

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_conditions_with_multiple_status_filter(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试按多个状态筛选查询筛选条件。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建不同状态的条件
    condition1 = ScreeningCondition(
        name="活跃条件",
        description="描述1",
        conditions={"skills": ["Python"]},
        status=StatusEnum.ACTIVE,
    )
    condition2 = ScreeningCondition(
        name="停用条件",
        description="描述2",
        conditions={"skills": ["Java"]},
        status=StatusEnum.INACTIVE,
    )
    condition3 = ScreeningCondition(
        name="已删除条件",
        description="描述3",
        conditions={"skills": ["Go"]},
        status=StatusEnum.DELETED,
    )
    db_session.add_all([condition1, condition2, condition3])
    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        # 查询活跃和停用状态
        response = await async_client.get(
            "/api/v1/conditions",
            params={"statuses": ["active", "inactive"]},
        )

        assert response.status_code == 200
        data = response.json()
        # 应该返回活跃和停用的条件，不包含已删除的
        assert data["data"]["total"] == 2
        for item in data["data"]["items"]:
            assert item["name"] != "已删除条件"

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_conditions_offset_calculation(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试分页偏移量计算。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建按名称排序的条件
    for i in range(10):
        condition = ScreeningCondition(
            name=f"偏移测试条件{i:02d}",
            description=f"描述{i}",
            conditions={"skills": ["Python"]},
            status=StatusEnum.ACTIVE,
        )
        db_session.add(condition)
    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        # 第一页
        response = await async_client.get(
            "/api/v1/conditions",
            params={"page": 1, "page_size": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 3
        first_page_items = [item["name"] for item in data["data"]["items"]]

        # 第二页
        response = await async_client.get(
            "/api/v1/conditions",
            params={"page": 2, "page_size": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 3
        second_page_items = [item["name"] for item in data["data"]["items"]]

        # 确保两页的数据不重复
        assert set(first_page_items).isdisjoint(set(second_page_items))

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_conditions_with_name_and_status_filter(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """测试同时按名称和状态筛选查询。

    Args:
        db_session: 数据库会话。
        async_client: 异步测试客户端。
    """
    # 创建不同名称和状态的条件
    condition1 = ScreeningCondition(
        name="Python开发-活跃",
        description="描述1",
        conditions={"skills": ["Python"]},
        status=StatusEnum.ACTIVE,
    )
    condition2 = ScreeningCondition(
        name="Python开发-停用",
        description="描述2",
        conditions={"skills": ["Python"]},
        status=StatusEnum.INACTIVE,
    )
    condition3 = ScreeningCondition(
        name="Java开发-活跃",
        description="描述3",
        conditions={"skills": ["Java"]},
        status=StatusEnum.ACTIVE,
    )
    db_session.add_all([condition1, condition2, condition3])
    await db_session.flush()

    async def override_get_session():
        yield db_session

    from src.api.deps import get_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        # 同时按名称和状态筛选
        response = await async_client.get(
            "/api/v1/conditions",
            params={"name": "Python", "statuses": ["active"]},
        )

        assert response.status_code == 200
        data = response.json()
        # 应该只返回包含 Python 且状态为活跃的条件
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["name"] == "Python开发-活跃"

    finally:
        app.dependency_overrides.clear()
