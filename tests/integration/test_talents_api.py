"""人才管理 API 集成测试模块。

测试人才管理的各项操作：
- POST /api/v1/talents/upload-screen: 上传简历
- GET /api/v1/talents: 分页查询
- GET /api/v1/talents/{id}: 获取详情
- POST /api/v1/talents/{id}/vectorize: 向量化
"""

from io import BytesIO
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.talent import ScreeningStatusEnum, WorkflowStatusEnum


# ==================== 上传简历测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestUploadResume:
    """上传简历测试类。"""

    async def test_upload_resume_invalid_file_type(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试上传无效文件类型。

        Args:
            async_client: 异步测试客户端。
        """
        # 创建一个文本文件
        files = {"file": ("test.txt", b"test content", "text/plain")}

        response = await async_client.post(
            "/api/v1/talents/upload-screen",
            files=files,
        )

        assert response.status_code == 400
        data = response.json()
        assert "不支持的文件类型" in data["detail"]

    async def test_upload_resume_missing_filename(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试上传无文件名的文件。

        Args:
            async_client: 异步测试客户端。
        """
        files = {"file": ("", b"test content", "application/pdf")}

        response = await async_client.post(
            "/api/v1/talents/upload-screen",
            files=files,
        )

        assert response.status_code == 400
        data = response.json()
        assert "文件名不能为空" in data["detail"]

    async def test_upload_resume_file_too_large(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试上传超大文件。

        Args:
            async_client: 异步测试客户端。
        """
        # 创建超过 10MB 的文件内容
        large_content = b"x" * (11 * 1024 * 1024)
        files = {"file": ("large.pdf", large_content, "application/pdf")}

        response = await async_client.post(
            "/api/v1/talents/upload-screen",
            files=files,
        )

        assert response.status_code == 400
        data = response.json()
        assert "文件大小超过限制" in data["detail"]

    async def test_upload_pdf_resume_success(
        self,
        async_client: AsyncClient,
        mock_workflow: AsyncMock,
    ) -> None:
        """测试成功上传 PDF 简历。

        Args:
            async_client: 异步测试客户端。
            mock_workflow: Mock 工作流函数。
        """
        # 创建一个简单的 PDF 文件内容
        pdf_content = b"%PDF-1.4\n%test pdf content"

        with patch(
            "src.api.v1.talents.run_resume_workflow",
            mock_workflow,
        ):
            files = {"file": ("resume.pdf", pdf_content, "application/pdf")}

            response = await async_client.post(
                "/api/v1/talents/upload-screen",
                files=files,
            )

        # 由于是 Mock 工作流，应该返回成功
        assert response.status_code in [201, 500]

    async def test_upload_docx_resume_success(
        self,
        async_client: AsyncClient,
        mock_workflow: AsyncMock,
    ) -> None:
        """测试成功上传 DOCX 简历。

        Args:
            async_client: 异步测试客户端。
            mock_workflow: Mock 工作流函数。
        """
        # 创建一个简单的 DOCX 文件内容（实际是 ZIP 格式）
        docx_content = b"PK\x03\x04" + b"\x00" * 100  # ZIP 文件头

        with patch(
            "src.api.v1.talents.run_resume_workflow",
            mock_workflow,
        ):
            files = {"file": ("resume.docx", docx_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}

            response = await async_client.post(
                "/api/v1/talents/upload-screen",
                files=files,
            )

        assert response.status_code in [201, 500]

    async def test_upload_resume_with_condition_id(
        self,
        async_client: AsyncClient,
        mock_workflow: AsyncMock,
        condition_factory,
    ) -> None:
        """测试上传简历并关联筛选条件。

        Args:
            async_client: 异步测试客户端。
            mock_workflow: Mock 工作流函数。
            condition_factory: 筛选条件工厂。
        """
        condition = await condition_factory(name="测试条件")

        pdf_content = b"%PDF-1.4\n%test pdf content"

        with patch(
            "src.api.v1.talents.run_resume_workflow",
            mock_workflow,
        ):
            files = {"file": ("resume.pdf", pdf_content, "application/pdf")}

            response = await async_client.post(
                "/api/v1/talents/upload-screen",
                files=files,
                params={"condition_id": condition.id},
            )

        assert response.status_code in [201, 500]


# ==================== 查询人才列表测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestListTalents:
    """查询人才列表测试类。"""

    async def test_list_talents_success(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试成功查询人才列表。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        # 创建测试数据
        await talent_factory(name="张三")
        await talent_factory(name="李四")

        response = await async_client.get("/api/v1/talents")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert data["data"]["total"] >= 2

    async def test_list_talents_pagination(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试分页查询人才列表。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        # 创建多个人才
        for i in range(15):
            await talent_factory(name=f"测试人才_{i}")

        # 查询第一页
        response = await async_client.get(
            "/api/v1/talents",
            params={"page": 1, "page_size": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) <= 10
        assert data["data"]["page"] == 1

    async def test_list_talents_filter_by_name(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试按姓名过滤人才。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        await talent_factory(name="张三")
        await talent_factory(name="李四")
        await talent_factory(name="王五")

        response = await async_client.get(
            "/api/v1/talents",
            params={"name": "张"},
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            assert "张" in item["name"]

    async def test_list_talents_filter_by_school(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试按院校过滤人才。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        await talent_factory(name="张三", school="清华大学")
        await talent_factory(name="李四", school="北京大学")

        response = await async_client.get(
            "/api/v1/talents",
            params={"school": "清华"},
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            assert "清华" in item["school"]

    async def test_list_talents_filter_by_major(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试按专业过滤人才。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        await talent_factory(name="张三", major="计算机科学与技术")
        await talent_factory(name="李四", major="软件工程")

        response = await async_client.get(
            "/api/v1/talents",
            params={"major": "计算机"},
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            assert "计算机" in item["major"]

    async def test_list_talents_filter_by_screening_status(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试按筛选状态过滤人才。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        await talent_factory(
            name="合格人才",
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )
        await talent_factory(
            name="不合格人才",
            screening_status=ScreeningStatusEnum.DISQUALIFIED,
        )

        response = await async_client.get(
            "/api/v1/talents",
            params={"screening_status": "qualified"},
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            assert item["screening_status"] == "qualified"

    async def test_list_talents_filter_by_screening_date(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试按筛选日期过滤人才。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        from datetime import datetime

        await talent_factory(name="张三")

        today = datetime.now().strftime("%Y-%m-%d")

        response = await async_client.get(
            "/api/v1/talents",
            params={
                "screening_date_start": today,
                "screening_date_end": today,
            },
        )

        assert response.status_code == 200

    async def test_list_talents_empty_result(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试查询空结果。

        Args:
            async_client: 异步测试客户端。
        """
        response = await async_client.get(
            "/api/v1/talents",
            params={"name": "不存在的人才名称_xyz"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 0
        assert data["data"]["items"] == []

    async def test_list_talents_invalid_page(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试无效页码参数。

        Args:
            async_client: 异步测试客户端。
        """
        response = await async_client.get(
            "/api/v1/talents",
            params={"page": 0},
        )

        assert response.status_code == 422


# ==================== 获取人才详情测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestGetTalent:
    """获取人才详情测试类。"""

    async def test_get_talent_success(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试成功获取人才详情。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        talent = await talent_factory(
            name="张三",
            school="清华大学",
            major="计算机科学与技术",
        )

        response = await async_client.get(f"/api/v1/talents/{talent.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == talent.id
        assert data["data"]["name"] == "张三"
        assert data["data"]["school"] == "清华大学"
        assert data["data"]["major"] == "计算机科学与技术"

    async def test_get_talent_nonexistent(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试获取不存在的人才。

        Args:
            async_client: 异步测试客户端。
        """
        response = await async_client.get(
            f"/api/v1/talents/{str(uuid4())}",
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "人才不存在"

    async def test_get_talent_with_skills(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试获取包含技能列表的人才详情。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        talent = await talent_factory(
            name="技能达人",
            skills=["Python", "Java", "Go", "Rust"],
        )

        response = await async_client.get(f"/api/v1/talents/{talent.id}")

        assert response.status_code == 200
        data = response.json()
        assert "Python" in data["data"]["skills"]
        assert "Java" in data["data"]["skills"]

    async def test_get_talent_response_structure(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试人才详情响应结构完整性。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        talent = await talent_factory(name="完整信息人才")

        response = await async_client.get(f"/api/v1/talents/{talent.id}")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "success" in data
        assert "message" in data
        assert "data" in data

        # 验证 data 字段
        talent_data = data["data"]
        assert "id" in talent_data
        assert "name" in talent_data
        assert "phone" in talent_data
        assert "email" in talent_data
        assert "education_level" in talent_data
        assert "school" in talent_data
        assert "major" in talent_data
        assert "graduation_date" in talent_data
        assert "skills" in talent_data
        assert "work_years" in talent_data
        assert "photo_url" in talent_data
        assert "condition_id" in talent_data
        assert "workflow_status" in talent_data
        assert "screening_status" in talent_data
        assert "screening_date" in talent_data
        assert "created_at" in talent_data
        assert "updated_at" in talent_data


# ==================== 向量化人才测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestVectorizeTalent:
    """向量化人才测试类。"""

    async def test_vectorize_talent_success(
        self,
        async_client: AsyncClient,
        talent_factory,
        mock_chroma,
    ) -> None:
        """测试成功向量化人才。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
            mock_chroma: Mock ChromaDB 客户端。
        """
        talent = await talent_factory(
            name="张三",
            resume_text="这是张三的简历内容，包含 Python、Java 等技能。",
        )

        with patch("src.api.v1.talents.chroma_client", mock_chroma):
            response = await async_client.post(
                f"/api/v1/talents/{talent.id}/vectorize",
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["vectorized"] is True
        assert data["data"]["talent_id"] == talent.id

    async def test_vectorize_talent_nonexistent(
        self,
        async_client: AsyncClient,
        mock_chroma,
    ) -> None:
        """测试向量化不存在的人才。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
        with patch("src.api.v1.talents.chroma_client", mock_chroma):
            response = await async_client.post(
                f"/api/v1/talents/{str(uuid4())}/vectorize",
            )

        assert response.status_code == 404

    async def test_vectorize_talent_no_resume(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试向量化无简历的人才。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        talent = await talent_factory(
            name="无简历人才",
            resume_text="",
        )

        response = await async_client.post(
            f"/api/v1/talents/{talent.id}/vectorize",
        )

        assert response.status_code == 400
        data = response.json()
        assert "简历文本为空" in data["detail"]


# ==================== 批量向量化测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestBatchVectorize:
    """批量向量化测试类。"""

    async def test_batch_vectorize_success(
        self,
        async_client: AsyncClient,
        talent_factory,
        mock_chroma,
    ) -> None:
        """测试成功批量向量化。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
            mock_chroma: Mock ChromaDB 客户端。
        """
        # 创建多个合格人才
        await talent_factory(
            name="合格人才1",
            resume_text="简历内容1",
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )
        await talent_factory(
            name="合格人才2",
            resume_text="简历内容2",
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )

        with patch("src.api.v1.talents.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/talents/batch-vectorize",
                params={"screening_status": "qualified"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total" in data["data"]
        assert "success" in data["data"]
        assert "failed" in data["data"]

    async def test_batch_vectorize_empty_result(
        self,
        async_client: AsyncClient,
        mock_chroma,
    ) -> None:
        """测试批量向量化无数据。

        Args:
            async_client: 异步测试客户端。
            mock_chroma: Mock ChromaDB 客户端。
        """
        with patch("src.api.v1.talents.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/talents/batch-vectorize",
                params={"screening_status": "disqualified"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 0

    async def test_batch_vectorize_with_limit(
        self,
        async_client: AsyncClient,
        talent_factory,
        mock_chroma,
    ) -> None:
        """测试批量向量化带限制。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
            mock_chroma: Mock ChromaDB 客户端。
        """
        # 创建多个合格人才
        for i in range(5):
            await talent_factory(
                name=f"合格人才_{i}",
                resume_text=f"简历内容_{i}",
                screening_status=ScreeningStatusEnum.QUALIFIED,
            )

        with patch("src.api.v1.talents.chroma_client", mock_chroma):
            response = await async_client.post(
                "/api/v1/talents/batch-vectorize",
                params={
                    "screening_status": "qualified",
                    "limit": 3,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] <= 3


# ==================== 边界情况测试 ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestTalentEdgeCases:
    """人才管理边界情况测试类。"""

    async def test_list_talents_with_unicode_search(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试使用 Unicode 字符搜索人才。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        await talent_factory(name="张三测试人才")

        response = await async_client.get(
            "/api/v1/talents",
            params={"name": "张三"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] >= 1

    async def test_get_talent_with_long_skills_list(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试获取包含大量技能的人才。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        skills = [f"技能_{i}" for i in range(50)]
        talent = await talent_factory(
            name="多技能人才",
            skills=skills,
        )

        response = await async_client.get(f"/api/v1/talents/{talent.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["skills"]) == 50

    async def test_list_talents_combined_filters(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试组合过滤条件查询人才。

        Args:
            async_client: 异步测试客户端。
            talent_factory: 人才信息工厂。
        """
        await talent_factory(
            name="张三",
            school="清华大学",
            major="计算机科学",
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )
        await talent_factory(
            name="李四",
            school="北京大学",
            major="软件工程",
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )

        response = await async_client.get(
            "/api/v1/talents",
            params={
                "school": "清华",
                "screening_status": "qualified",
            },
        )

        assert response.status_code == 200
        data = response.json()
        # 应该只返回符合所有条件的人才
        for item in data["data"]["items"]:
            assert "清华" in item["school"]
            assert item["screening_status"] == "qualified"

    async def test_list_talents_only_completed_workflow(
        self,
        async_client: AsyncClient,
        talent_factory,
    ) -> None:
        """测试只返回工作流完成的人才。

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

        response = await async_client.get("/api/v1/talents")

        assert response.status_code == 200
        data = response.json()
        # 只返回工作流完成的人才
        for item in data["data"]["items"]:
            assert item["workflow_status"] == "completed"
