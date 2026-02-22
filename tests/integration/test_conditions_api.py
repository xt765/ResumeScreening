"""筛选条件 API 集成测试模块。

测试筛选条件的 CRUD 操作：
- POST /api/v1/conditions: 新增筛选条件
- PUT /api/v1/conditions/{id}: 修改筛选条件
- DELETE /api/v1/conditions/{id}: 逻辑删除
- GET /api/v1/conditions: 分页查询
"""

from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ScreeningCondition, StatusEnum


# ==================== 创建筛选条件测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestCreateCondition:
    """创建筛选条件测试类。"""

    async def test_create_condition_success(
        self,
        async_client: AsyncClient,
        sample_condition_data: dict[str, Any],
    ) -> None:
        """测试成功创建筛选条件。

        Args:
            async_client: 异步测试客户端。
            sample_condition_data: 示例筛选条件数据。
        """
        response = await async_client.post(
            "/api/v1/conditions",
            json=sample_condition_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "筛选条件创建成功"
        assert data["data"]["name"] == sample_condition_data["name"]
        assert data["data"]["is_active"] is True
        assert "id" in data["data"]
        assert "created_at" in data["data"]

    async def test_create_condition_with_minimal_data(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试使用最小数据创建筛选条件。

        Args:
            async_client: 异步测试客户端。
        """
        minimal_data = {
            "name": f"最小条件_{uuid4().hex[:8]}",
            "config": {},
        }

        response = await async_client.post(
            "/api/v1/conditions",
            json=minimal_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == minimal_data["name"]

    async def test_create_condition_inactive(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试创建停用状态的筛选条件。

        Args:
            async_client: 异步测试客户端。
        """
        condition_data = {
            "name": f"停用条件_{uuid4().hex[:8]}",
            "config": {"skills": ["Java"]},
            "is_active": False,
        }

        response = await async_client.post(
            "/api/v1/conditions",
            json=condition_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["is_active"] is False

    async def test_create_condition_invalid_name_empty(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试创建筛选条件（空名称）。

        Args:
            async_client: 异步测试客户端。
        """
        invalid_data = {
            "name": "",
            "config": {},
        }

        response = await async_client.post(
            "/api/v1/conditions",
            json=invalid_data,
        )

        assert response.status_code == 422

    async def test_create_condition_invalid_name_too_long(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试创建筛选条件（名称过长）。

        Args:
            async_client: 异步测试客户端。
        """
        invalid_data = {
            "name": "x" * 101,  # 超过 100 字符限制
            "config": {},
        }

        response = await async_client.post(
            "/api/v1/conditions",
            json=invalid_data,
        )

        assert response.status_code == 422

    async def test_create_condition_missing_config(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试创建筛选条件（缺少 config 字段）。

        Args:
            async_client: 异步测试客户端。
        """
        invalid_data = {
            "name": f"测试条件_{uuid4().hex[:8]}",
        }

        response = await async_client.post(
            "/api/v1/conditions",
            json=invalid_data,
        )

        assert response.status_code == 422


# ==================== 更新筛选条件测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestUpdateCondition:
    """更新筛选条件测试类。"""

    async def test_update_condition_name(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试更新筛选条件名称。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        condition = await condition_factory(name="原始名称")

        update_data = {"name": "更新后的名称"}

        response = await async_client.put(
            f"/api/v1/conditions/{condition.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "更新后的名称"

    async def test_update_condition_description(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试更新筛选条件描述。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        condition = await condition_factory(description="原始描述")

        update_data = {"description": "更新后的描述"}

        response = await async_client.put(
            f"/api/v1/conditions/{condition.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["description"] == "更新后的描述"

    async def test_update_condition_config(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试更新筛选条件配置。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        condition = await condition_factory()

        update_data = {
            "config": {
                "skills": ["Go", "Rust"],
                "experience_years": 5,
            },
        }

        response = await async_client.put(
            f"/api/v1/conditions/{condition.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert "Go" in data["data"]["config"]["skills"]
        assert data["data"]["config"]["experience_years"] == 5

    async def test_update_condition_status(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试更新筛选条件状态。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        condition = await condition_factory()

        update_data = {"is_active": False}

        response = await async_client.put(
            f"/api/v1/conditions/{condition.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["is_active"] is False

    async def test_update_condition_multiple_fields(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试同时更新多个字段。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        condition = await condition_factory(name="原始名称")

        update_data = {
            "name": "新名称",
            "description": "新描述",
            "is_active": False,
        }

        response = await async_client.put(
            f"/api/v1/conditions/{condition.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "新名称"
        assert data["data"]["description"] == "新描述"
        assert data["data"]["is_active"] is False

    async def test_update_nonexistent_condition(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试更新不存在的筛选条件。

        Args:
            async_client: 异步测试客户端。
        """
        update_data = {"name": "更新名称"}

        response = await async_client.put(
            f"/api/v1/conditions/{str(uuid4())}",
            json=update_data,
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "筛选条件不存在"

    async def test_update_deleted_condition(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试更新已删除的筛选条件。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        condition = await condition_factory(status=StatusEnum.DELETED)

        update_data = {"name": "更新名称"}

        response = await async_client.put(
            f"/api/v1/conditions/{condition.id}",
            json=update_data,
        )

        assert response.status_code == 404


# ==================== 删除筛选条件测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestDeleteCondition:
    """删除筛选条件测试类。"""

    async def test_delete_condition_success(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试成功删除筛选条件。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        condition = await condition_factory(name="待删除条件")

        response = await async_client.delete(
            f"/api/v1/conditions/{condition.id}",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "筛选条件删除成功"

    async def test_delete_nonexistent_condition(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试删除不存在的筛选条件。

        Args:
            async_client: 异步测试客户端。
        """
        response = await async_client.delete(
            f"/api/v1/conditions/{str(uuid4())}",
        )

        assert response.status_code == 404

    async def test_delete_already_deleted_condition(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试删除已删除的筛选条件。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        condition = await condition_factory(status=StatusEnum.DELETED)

        response = await async_client.delete(
            f"/api/v1/conditions/{condition.id}",
        )

        assert response.status_code == 404


# ==================== 查询筛选条件测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestListConditions:
    """查询筛选条件测试类。"""

    async def test_list_conditions_success(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试成功查询筛选条件列表。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        # 创建测试数据
        await condition_factory(name="条件A")
        await condition_factory(name="条件B")

        response = await async_client.get("/api/v1/conditions")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert "page" in data["data"]
        assert "page_size" in data["data"]
        assert data["data"]["total"] >= 2

    async def test_list_conditions_pagination(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试分页查询筛选条件。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        # 创建多个条件
        for i in range(15):
            await condition_factory(name=f"分页条件_{i}")

        # 查询第一页
        response = await async_client.get(
            "/api/v1/conditions",
            params={"page": 1, "page_size": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) <= 10
        assert data["data"]["page"] == 1

        # 查询第二页
        response = await async_client.get(
            "/api/v1/conditions",
            params={"page": 2, "page_size": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["page"] == 2

    async def test_list_conditions_filter_by_name(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试按名称过滤筛选条件。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        await condition_factory(name="Python开发条件")
        await condition_factory(name="Java开发条件")
        await condition_factory(name="前端开发条件")

        response = await async_client.get(
            "/api/v1/conditions",
            params={"name": "Python"},
        )

        assert response.status_code == 200
        data = response.json()
        # 应该只返回包含 "Python" 的条件
        for item in data["data"]["items"]:
            assert "Python" in item["name"]

    async def test_list_conditions_filter_by_status(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试按状态过滤筛选条件。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        await condition_factory(name="活跃条件", status=StatusEnum.ACTIVE)
        await condition_factory(name="停用条件", status=StatusEnum.INACTIVE)

        response = await async_client.get(
            "/api/v1/conditions",
            params={"statuses": ["active"]},
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            assert item["is_active"] is True

    async def test_list_conditions_exclude_deleted(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试查询时排除已删除的条件。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        await condition_factory(name="活跃条件", status=StatusEnum.ACTIVE)
        await condition_factory(name="已删除条件", status=StatusEnum.DELETED)

        response = await async_client.get("/api/v1/conditions")

        assert response.status_code == 200
        data = response.json()
        # 已删除的条件不应该出现在结果中
        for item in data["data"]["items"]:
            assert item["is_active"] is not None  # 排除已删除

    async def test_list_conditions_empty_result(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试查询空结果。

        Args:
            async_client: 异步测试客户端。
        """
        response = await async_client.get(
            "/api/v1/conditions",
            params={"name": "不存在的条件名称_xyz"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 0
        assert data["data"]["items"] == []

    async def test_list_conditions_invalid_page(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试无效页码参数。

        Args:
            async_client: 异步测试客户端。
        """
        response = await async_client.get(
            "/api/v1/conditions",
            params={"page": 0},  # 页码必须 >= 1
        )

        assert response.status_code == 422

    async def test_list_conditions_invalid_page_size(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试无效分页大小参数。

        Args:
            async_client: 异步测试客户端。
        """
        response = await async_client.get(
            "/api/v1/conditions",
            params={"page_size": 200},  # 最大 100
        )

        assert response.status_code == 422


# ==================== 边界情况测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestConditionEdgeCases:
    """筛选条件边界情况测试类。"""

    async def test_create_condition_with_special_characters(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试创建包含特殊字符的筛选条件。

        Args:
            async_client: 异步测试客户端。
        """
        condition_data = {
            "name": "条件<>&\"'特殊字符",
            "description": "描述包含<特殊>字符",
            "config": {},
        }

        response = await async_client.post(
            "/api/v1/conditions",
            json=condition_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["name"] == condition_data["name"]

    async def test_create_condition_with_unicode(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试创建包含 Unicode 字符的筛选条件。

        Args:
            async_client: 异步测试客户端。
        """
        condition_data = {
            "name": "中文条件🎉测试",
            "description": "包含表情符号的描述🚀",
            "config": {"skills": ["Python"]},
        }

        response = await async_client.post(
            "/api/v1/conditions",
            json=condition_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert "🎉" in data["data"]["name"]

    async def test_list_conditions_with_unicode_search(
        self,
        async_client: AsyncClient,
        condition_factory,
    ) -> None:
        """测试使用 Unicode 字符搜索筛选条件。

        Args:
            async_client: 异步测试客户端。
            condition_factory: 筛选条件工厂。
        """
        await condition_factory(name="中文测试条件")

        response = await async_client.get(
            "/api/v1/conditions",
            params={"name": "中文"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] >= 1

    async def test_condition_response_structure(
        self,
        async_client: AsyncClient,
        sample_condition_data: dict[str, Any],
    ) -> None:
        """测试筛选条件响应结构完整性。

        Args:
            async_client: 异步测试客户端。
            sample_condition_data: 示例筛选条件数据。
        """
        response = await async_client.post(
            "/api/v1/conditions",
            json=sample_condition_data,
        )

        assert response.status_code == 201
        data = response.json()

        # 验证响应结构
        assert "success" in data
        assert "message" in data
        assert "data" in data

        # 验证 data 字段
        condition_data = data["data"]
        assert "id" in condition_data
        assert "name" in condition_data
        assert "description" in condition_data
        assert "config" in condition_data
        assert "is_active" in condition_data
        assert "created_at" in condition_data
        assert "updated_at" in condition_data

        # 验证 config 结构
        config = condition_data["config"]
        assert "skills" in config
        assert "education_level" in config
        assert "experience_years" in config
        assert "major" in config
        assert "school_tier" in config
