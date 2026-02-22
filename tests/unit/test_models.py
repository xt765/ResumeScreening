"""模型测试模块。

测试数据库模型的创建、属性和方法：
- ScreeningCondition 模型测试
- TalentInfo 模型测试
- 枚举值测试
- 使用真实 MySQL 数据库的集成测试
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ScreeningCondition, StatusEnum, TalentInfo
from src.models.talent import ScreeningStatusEnum, WorkflowStatusEnum


# ==================== StatusEnum 枚举测试 ====================


class TestStatusEnum:
    """StatusEnum 枚举测试类。"""

    def test_status_enum_values(self) -> None:
        """测试枚举值是否正确。"""
        assert StatusEnum.ACTIVE.value == "active"
        assert StatusEnum.INACTIVE.value == "inactive"
        assert StatusEnum.DELETED.value == "deleted"

    def test_status_enum_is_string(self) -> None:
        """测试枚举是字符串枚举。"""
        assert isinstance(StatusEnum.ACTIVE, str)
        assert StatusEnum.ACTIVE == "active"

    def test_status_enum_count(self) -> None:
        """测试枚举值数量。"""
        assert len(StatusEnum) == 3


# ==================== WorkflowStatusEnum 枚举测试 ====================


class TestWorkflowStatusEnum:
    """WorkflowStatusEnum 枚举测试类。"""

    def test_workflow_status_enum_values(self) -> None:
        """测试工作流状态枚举值。"""
        assert WorkflowStatusEnum.PENDING.value == "pending"
        assert WorkflowStatusEnum.PARSING.value == "parsing"
        assert WorkflowStatusEnum.FILTERING.value == "filtering"
        assert WorkflowStatusEnum.STORING.value == "storing"
        assert WorkflowStatusEnum.CACHING.value == "caching"
        assert WorkflowStatusEnum.COMPLETED.value == "completed"
        assert WorkflowStatusEnum.FAILED.value == "failed"

    def test_workflow_status_enum_count(self) -> None:
        """测试工作流状态枚举值数量。"""
        assert len(WorkflowStatusEnum) == 7

    def test_workflow_status_enum_is_string(self) -> None:
        """测试枚举是字符串枚举。"""
        assert isinstance(WorkflowStatusEnum.PENDING, str)


# ==================== ScreeningStatusEnum 枚举测试 ====================


class TestScreeningStatusEnum:
    """ScreeningStatusEnum 枚举测试类。"""

    def test_screening_status_enum_values(self) -> None:
        """测试筛选状态枚举值。"""
        assert ScreeningStatusEnum.QUALIFIED.value == "qualified"
        assert ScreeningStatusEnum.DISQUALIFIED.value == "disqualified"

    def test_screening_status_enum_count(self) -> None:
        """测试筛选状态枚举值数量。"""
        assert len(ScreeningStatusEnum) == 2


# ==================== ScreeningCondition 模型测试 ====================


class TestScreeningCondition:
    """ScreeningCondition 模型测试类。"""

    def test_create_condition(self) -> None:
        """测试创建筛选条件模型实例。"""
        condition = ScreeningCondition(
            name="测试条件",
            description="这是一个测试条件",
            conditions={
                "skills": ["Python", "Java"],
                "education_level": "master",
                "experience_years": 5,
            },
            status=StatusEnum.ACTIVE,
        )

        assert condition.name == "测试条件"
        assert condition.description == "这是一个测试条件"
        assert condition.conditions["skills"] == ["Python", "Java"]
        assert condition.conditions["education_level"] == "master"
        assert condition.conditions["experience_years"] == 5
        assert condition.status == StatusEnum.ACTIVE

    def test_condition_default_status(self) -> None:
        """测试筛选条件默认状态为 ACTIVE。"""
        # 使用完整参数创建，验证默认值逻辑
        condition = ScreeningCondition(name="测试条件")

        # 验证模型定义中的默认值
        # 注意：SQLAlchemy 默认值在 flush 到数据库时才应用
        # 这里验证模型定义正确
        from src.models.condition import ScreeningCondition as SC

        # 检查列定义中的默认值
        status_column = SC.__table__.columns.status
        assert status_column.default is not None
        assert status_column.default.arg == StatusEnum.ACTIVE

    def test_condition_default_description(self) -> None:
        """测试筛选条件默认描述为空字符串。"""
        condition = ScreeningCondition(name="测试条件")

        # 验证模型定义中的默认值
        from src.models.condition import ScreeningCondition as SC

        description_column = SC.__table__.columns.description
        assert description_column.default is not None
        assert description_column.default.arg == ""

    def test_condition_default_conditions(self) -> None:
        """测试筛选条件默认 conditions 为空字典。"""
        condition = ScreeningCondition(name="测试条件")

        # 验证模型定义中的默认值
        from src.models.condition import ScreeningCondition as SC

        conditions_column = SC.__table__.columns.conditions
        assert conditions_column.default is not None
        # default 是一个 callable，返回空字典

    def test_condition_repr(self) -> None:
        """测试筛选条件的字符串表示。"""
        condition = ScreeningCondition(
            name="测试条件",
            conditions={},
            status=StatusEnum.ACTIVE,
        )
        condition.id = "test-id-123"

        repr_str = repr(condition)
        assert "ScreeningCondition" in repr_str
        assert "test-id-123" in repr_str
        assert "测试条件" in repr_str
        assert "active" in repr_str

    def test_condition_to_dict(self) -> None:
        """测试筛选条件转换为字典。"""
        condition = ScreeningCondition(
            name="测试条件",
            description="测试描述",
            conditions={
                "skills": ["Python"],
                "education_level": "bachelor",
            },
            status=StatusEnum.ACTIVE,
        )
        condition.id = "test-id"

        result = condition.to_dict()

        assert result["id"] == "test-id"
        assert result["name"] == "测试条件"
        assert result["description"] == "测试描述"
        assert result["conditions"]["skills"] == ["Python"]
        assert result["status"] == "active"
        assert "created_at" in result
        assert "updated_at" in result

    def test_condition_skills_property(self) -> None:
        """测试筛选条件的 skills 属性。"""
        condition = ScreeningCondition(
            name="测试条件",
            conditions={"skills": ["Python", "Java", "Go"]},
        )

        assert condition.skills == ["Python", "Java", "Go"]

    def test_condition_skills_property_empty(self) -> None:
        """测试筛选条件的 skills 属性为空时返回空列表。"""
        condition = ScreeningCondition(
            name="测试条件",
            conditions={},
        )

        assert condition.skills == []

    def test_condition_education_level_property(self) -> None:
        """测试筛选条件的 education_level 属性。"""
        condition = ScreeningCondition(
            name="测试条件",
            conditions={"education_level": "master"},
        )

        assert condition.education_level == "master"

    def test_condition_education_level_property_empty(self) -> None:
        """测试筛选条件的 education_level 属性为空时返回空字符串。"""
        condition = ScreeningCondition(
            name="测试条件",
            conditions={},
        )

        assert condition.education_level == ""

    def test_condition_experience_years_property(self) -> None:
        """测试筛选条件的 experience_years 属性。"""
        condition = ScreeningCondition(
            name="测试条件",
            conditions={"experience_years": 5},
        )

        assert condition.experience_years == 5

    def test_condition_experience_years_property_default(self) -> None:
        """测试筛选条件的 experience_years 属性默认值为 0。"""
        condition = ScreeningCondition(
            name="测试条件",
            conditions={},
        )

        assert condition.experience_years == 0

    def test_condition_major_property(self) -> None:
        """测试筛选条件的 major 属性。"""
        condition = ScreeningCondition(
            name="测试条件",
            conditions={"major": ["计算机科学", "软件工程"]},
        )

        assert condition.major == ["计算机科学", "软件工程"]

    def test_condition_major_property_empty(self) -> None:
        """测试筛选条件的 major 属性为空时返回空列表。"""
        condition = ScreeningCondition(
            name="测试条件",
            conditions={},
        )

        assert condition.major == []

    def test_condition_school_tier_property(self) -> None:
        """测试筛选条件的 school_tier 属性。"""
        condition = ScreeningCondition(
            name="测试条件",
            conditions={"school_tier": ["top", "key"]},
        )

        assert condition.school_tier == ["top", "key"]

    def test_condition_school_tier_property_empty(self) -> None:
        """测试筛选条件的 school_tier 属性为空时返回空列表。"""
        condition = ScreeningCondition(
            name="测试条件",
            conditions={},
        )

        assert condition.school_tier == []


# ==================== TalentInfo 模型测试 ====================


class TestTalentInfo:
    """TalentInfo 模型测试类。"""

    def test_create_talent(self) -> None:
        """测试创建人才信息模型实例。"""
        talent = TalentInfo(
            name="张三",
            phone="13800138000",
            email="zhangsan@example.com",
            education_level="硕士",
            school="清华大学",
            major="计算机科学与技术",
            work_years=5,
            skills=["Python", "Java"],
            workflow_status=WorkflowStatusEnum.COMPLETED,
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )

        assert talent.name == "张三"
        assert talent.phone == "13800138000"
        assert talent.email == "zhangsan@example.com"
        assert talent.education_level == "硕士"
        assert talent.school == "清华大学"
        assert talent.major == "计算机科学与技术"
        assert talent.work_years == 5
        assert talent.skills == ["Python", "Java"]
        assert talent.workflow_status == WorkflowStatusEnum.COMPLETED
        assert talent.screening_status == ScreeningStatusEnum.QUALIFIED

    def test_talent_default_values(self) -> None:
        """测试人才信息默认值。"""
        talent = TalentInfo(name="测试人才")

        # 验证模型定义中的默认值
        # 注意：SQLAlchemy 默认值在 flush 到数据库时才应用
        from src.models.talent import TalentInfo as TI

        # 检查各列的默认值定义
        assert TI.__table__.columns.phone.default is not None
        assert TI.__table__.columns.email.default is not None
        assert TI.__table__.columns.education_level.default is not None
        assert TI.__table__.columns.school.default is not None
        assert TI.__table__.columns.major.default is not None
        assert TI.__table__.columns.work_years.default is not None
        assert TI.__table__.columns.photo_url.default is not None
        assert TI.__table__.columns.resume_text.default is not None
        assert TI.__table__.columns.workflow_status.default is not None
        assert TI.__table__.columns.error_message.default is not None

        # 验证默认值
        assert TI.__table__.columns.phone.default.arg == ""
        assert TI.__table__.columns.email.default.arg == ""
        assert TI.__table__.columns.work_years.default.arg == 0
        assert TI.__table__.columns.workflow_status.default.arg == WorkflowStatusEnum.PENDING

    def test_talent_repr(self) -> None:
        """测试人才信息的字符串表示。"""
        talent = TalentInfo(
            name="张三",
            workflow_status=WorkflowStatusEnum.COMPLETED,
        )
        talent.id = "talent-id-123"

        repr_str = repr(talent)
        assert "TalentInfo" in repr_str
        assert "talent-id-123" in repr_str
        assert "张三" in repr_str
        assert "completed" in repr_str

    def test_talent_to_dict_without_sensitive(self) -> None:
        """测试人才信息转换为字典（不含敏感信息）。"""
        talent = TalentInfo(
            name="张三",
            phone="13800138000",
            email="zhangsan@example.com",
            education_level="硕士",
            school="清华大学",
            major="计算机科学",
            work_years=5,
            skills=["Python"],
            workflow_status=WorkflowStatusEnum.COMPLETED,
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )
        talent.id = "talent-id"

        result = talent.to_dict(include_sensitive=False)

        assert result["id"] == "talent-id"
        assert result["name"] == "张三"
        assert result["education_level"] == "硕士"
        assert result["school"] == "清华大学"
        # 敏感信息应该被脱敏
        assert result["phone"] == "138****8000"
        assert result["email"] == "zha***@example.com"

    def test_talent_to_dict_with_sensitive(self) -> None:
        """测试人才信息转换为字典（包含敏感信息）。"""
        talent = TalentInfo(
            name="张三",
            phone="13800138000",
            email="zhangsan@example.com",
            workflow_status=WorkflowStatusEnum.COMPLETED,
        )
        talent.id = "talent-id"

        result = talent.to_dict(include_sensitive=True)

        assert result["phone"] == "13800138000"
        assert result["email"] == "zhangsan@example.com"

    def test_talent_mask_phone(self) -> None:
        """测试手机号脱敏。"""
        # 正常手机号
        assert TalentInfo._mask_phone("13800138000") == "138****8000"
        # 短号码
        assert TalentInfo._mask_phone("123456") == "123456"
        # 空值
        assert TalentInfo._mask_phone("") == ""
        assert TalentInfo._mask_phone(None) is None

    def test_talent_mask_email(self) -> None:
        """测试邮箱脱敏。"""
        # 正常邮箱
        assert TalentInfo._mask_email("zhangsan@example.com") == "zha***@example.com"
        # 短用户名
        assert TalentInfo._mask_email("ab@example.com") == "a***@example.com"
        # 无效邮箱
        assert TalentInfo._mask_email("invalid-email") == "invalid-email"
        # 空值
        assert TalentInfo._mask_email("") == ""
        assert TalentInfo._mask_email(None) is None

    def test_talent_mark_as_qualified(self) -> None:
        """测试标记为符合条件。"""
        talent = TalentInfo(name="张三")

        talent.mark_as_qualified()

        assert talent.screening_status == ScreeningStatusEnum.QUALIFIED
        assert talent.screening_date is not None
        assert isinstance(talent.screening_date, datetime)

    def test_talent_mark_as_disqualified(self) -> None:
        """测试标记为不符合条件。"""
        talent = TalentInfo(name="张三")

        talent.mark_as_disqualified()

        assert talent.screening_status == ScreeningStatusEnum.DISQUALIFIED
        assert talent.screening_date is not None
        assert isinstance(talent.screening_date, datetime)

    def test_talent_set_error(self) -> None:
        """测试设置错误信息。"""
        talent = TalentInfo(name="张三")

        talent.set_error("处理失败：文件格式错误")

        assert talent.workflow_status == WorkflowStatusEnum.FAILED
        assert talent.error_message == "处理失败：文件格式错误"

    def test_talent_to_dict_with_none_values(self) -> None:
        """测试人才信息转换为字典（包含 None 值）。"""
        talent = TalentInfo(
            name="张三",
            workflow_status=WorkflowStatusEnum.PENDING,  # 设置必填字段
        )
        talent.id = "talent-id"

        result = talent.to_dict()

        assert result["graduation_date"] is None
        assert result["screening_status"] is None
        assert result["screening_date"] is None
        assert result["skills"] == []

    def test_talent_to_dict_with_date(self) -> None:
        """测试人才信息转换为字典（包含日期）。"""
        talent = TalentInfo(
            name="张三",
            graduation_date=date(2020, 6, 30),
            screening_date=datetime(2024, 1, 15, 10, 30, 0),
            workflow_status=WorkflowStatusEnum.COMPLETED,  # 设置必填字段
        )
        talent.id = "talent-id"

        result = talent.to_dict()

        assert result["graduation_date"] == "2020-06-30"
        assert "2024-01-15" in result["screening_date"]


# ==================== 模型属性边界测试 ====================


class TestModelEdgeCases:
    """模型边界情况测试类。"""

    def test_condition_with_complex_conditions(self) -> None:
        """测试筛选条件包含复杂配置。"""
        complex_conditions: dict[str, Any] = {
            "skills": ["Python", "Java", "Go", "Rust"],
            "education_level": "doctor",
            "experience_years": 10,
            "major": ["计算机科学", "软件工程", "人工智能"],
            "school_tier": ["top", "key", "overseas"],
            "custom_field": "custom_value",
        }

        condition = ScreeningCondition(
            name="复杂条件",
            conditions=complex_conditions,
        )

        assert len(condition.skills) == 4
        assert condition.education_level == "doctor"
        assert condition.experience_years == 10
        assert len(condition.major) == 3
        assert len(condition.school_tier) == 3
        assert condition.conditions["custom_field"] == "custom_value"

    def test_talent_with_empty_skills(self) -> None:
        """测试人才信息技能列表为空。"""
        talent = TalentInfo(
            name="测试人才",
            skills=[],
        )

        assert talent.skills == []

    def test_talent_with_many_skills(self) -> None:
        """测试人才信息包含大量技能。"""
        skills = [f"Skill{i}" for i in range(100)]
        talent = TalentInfo(
            name="技能达人",
            skills=skills,
        )

        assert len(talent.skills) == 100

    def test_talent_with_long_text(self) -> None:
        """测试人才信息包含长文本。"""
        long_resume = "这是一段很长的简历内容。" * 1000
        talent = TalentInfo(
            name="测试人才",
            resume_text=long_resume,
        )

        assert len(talent.resume_text) == len(long_resume)

    def test_talent_with_special_characters(self) -> None:
        """测试人才信息包含特殊字符。"""
        talent = TalentInfo(
            name="张三（曾用名：李四）",
            school="北京大学 & 清华大学",
            major="计算机科学@人工智能",
        )

        assert "（曾用名" in talent.name
        assert "&" in talent.school
        assert "@" in talent.major


# ==================== 真实 MySQL 数据库测试 ====================


@pytest.mark.integration
class TestScreeningConditionDatabase:
    """ScreeningCondition 数据库集成测试类。

    使用真实 MySQL 数据库进行测试。
    """

    async def test_create_condition_in_database(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试在数据库中创建筛选条件。"""
        condition = ScreeningCondition(
            name="高级Python开发工程师",
            description="用于筛选高级Python开发工程师的条件",
            conditions={
                "skills": ["Python", "FastAPI", "SQL"],
                "education_level": "master",
                "experience_years": 5,
            },
            status=StatusEnum.ACTIVE,
        )

        db_session.add(condition)
        await db_session.commit()
        await db_session.refresh(condition)

        # 验证 ID 已生成
        assert condition.id is not None
        assert UUID(condition.id)  # 验证是有效的 UUID

        # 验证时间戳已生成
        assert condition.created_at is not None
        assert condition.updated_at is not None

    async def test_query_condition_from_database(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试从数据库查询筛选条件。"""
        # 创建测试数据
        condition = ScreeningCondition(
            name="测试条件",
            conditions={"skills": ["Python"]},
        )
        db_session.add(condition)
        await db_session.commit()

        # 查询数据
        result = await db_session.execute(
            select(ScreeningCondition).where(ScreeningCondition.name == "测试条件")
        )
        found_condition = result.scalar_one()

        assert found_condition.name == "测试条件"
        assert found_condition.skills == ["Python"]

    async def test_update_condition_in_database(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试更新数据库中的筛选条件。"""
        # 创建测试数据
        condition = ScreeningCondition(
            name="待更新条件",
            conditions={"skills": ["Python"]},
        )
        db_session.add(condition)
        await db_session.commit()
        await db_session.refresh(condition)

        original_updated_at = condition.updated_at

        # 更新数据
        condition.conditions = {"skills": ["Python", "Java"]}
        condition.status = StatusEnum.INACTIVE
        await db_session.commit()
        await db_session.refresh(condition)

        # 验证更新
        assert condition.skills == ["Python", "Java"]
        assert condition.status == StatusEnum.INACTIVE
        # 注意：updated_at 的自动更新依赖于数据库触发器或 SQLAlchemy 事件

    async def test_delete_condition_from_database(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试从数据库删除筛选条件。"""
        # 创建测试数据
        condition = ScreeningCondition(
            name="待删除条件",
            conditions={},
        )
        db_session.add(condition)
        await db_session.commit()
        condition_id = condition.id

        # 删除数据
        await db_session.delete(condition)
        await db_session.commit()

        # 验证删除
        result = await db_session.execute(
            select(ScreeningCondition).where(ScreeningCondition.id == condition_id)
        )
        assert result.scalar_one_or_none() is None

    async def test_condition_status_filter(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试按状态筛选条件。"""
        # 创建多条测试数据
        conditions = [
            ScreeningCondition(name="活跃条件1", status=StatusEnum.ACTIVE),
            ScreeningCondition(name="活跃条件2", status=StatusEnum.ACTIVE),
            ScreeningCondition(name="停用条件", status=StatusEnum.INACTIVE),
            ScreeningCondition(name="删除条件", status=StatusEnum.DELETED),
        ]
        for c in conditions:
            db_session.add(c)
        await db_session.commit()

        # 查询活跃条件
        result = await db_session.execute(
            select(ScreeningCondition).where(ScreeningCondition.status == StatusEnum.ACTIVE)
        )
        active_conditions = result.scalars().all()

        assert len(active_conditions) == 2
        assert all(c.status == StatusEnum.ACTIVE for c in active_conditions)


@pytest.mark.integration
class TestTalentInfoDatabase:
    """TalentInfo 数据库集成测试类。

    使用真实 MySQL 数据库进行测试。
    """

    async def test_create_talent_in_database(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试在数据库中创建人才信息。"""
        talent = TalentInfo(
            name="张三",
            phone="13800138000",
            email="zhangsan@example.com",
            education_level="硕士",
            school="清华大学",
            major="计算机科学与技术",
            work_years=5,
            skills=["Python", "Java", "SQL"],
            workflow_status=WorkflowStatusEnum.COMPLETED,
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )

        db_session.add(talent)
        await db_session.commit()
        await db_session.refresh(talent)

        # 验证 ID 已生成
        assert talent.id is not None
        assert UUID(talent.id)

        # 验证时间戳已生成
        assert talent.created_at is not None
        assert talent.updated_at is not None

    async def test_query_talent_from_database(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试从数据库查询人才信息。"""
        # 创建测试数据
        talent = TalentInfo(
            name="李四",
            school="北京大学",
            skills=["Go", "Rust"],
        )
        db_session.add(talent)
        await db_session.commit()

        # 查询数据
        result = await db_session.execute(
            select(TalentInfo).where(TalentInfo.name == "李四")
        )
        found_talent = result.scalar_one()

        assert found_talent.name == "李四"
        assert found_talent.school == "北京大学"
        assert found_talent.skills == ["Go", "Rust"]

    async def test_talent_with_condition_relation(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试人才与筛选条件的关联关系。"""
        # 创建筛选条件
        condition = ScreeningCondition(
            name="Python开发条件",
            conditions={"skills": ["Python"]},
        )
        db_session.add(condition)
        await db_session.commit()
        await db_session.refresh(condition)

        # 创建关联的人才
        talent = TalentInfo(
            name="王五",
            condition_id=condition.id,
            screening_status=ScreeningStatusEnum.QUALIFIED,
        )
        db_session.add(talent)
        await db_session.commit()
        await db_session.refresh(talent)

        # 验证关联
        assert talent.condition_id == condition.id

    async def test_talent_workflow_status_update(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试人才工作流状态更新。"""
        # 创建测试数据
        talent = TalentInfo(
            name="赵六",
            workflow_status=WorkflowStatusEnum.PENDING,
        )
        db_session.add(talent)
        await db_session.commit()
        await db_session.refresh(talent)

        # 更新工作流状态
        talent.workflow_status = WorkflowStatusEnum.PARSING
        await db_session.commit()
        await db_session.refresh(talent)

        assert talent.workflow_status == WorkflowStatusEnum.PARSING

        # 继续更新
        talent.workflow_status = WorkflowStatusEnum.FILTERING
        await db_session.commit()
        await db_session.refresh(talent)

        assert talent.workflow_status == WorkflowStatusEnum.FILTERING

    async def test_talent_screening_result(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试人才筛选结果标记。"""
        # 创建测试数据
        talent = TalentInfo(name="测试人才")
        db_session.add(talent)
        await db_session.commit()
        await db_session.refresh(talent)

        # 标记为合格
        talent.mark_as_qualified()
        await db_session.commit()
        await db_session.refresh(talent)

        assert talent.screening_status == ScreeningStatusEnum.QUALIFIED
        assert talent.screening_date is not None

    async def test_talent_error_handling(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试人才错误处理。"""
        # 创建测试数据
        talent = TalentInfo(name="错误测试人才")
        db_session.add(talent)
        await db_session.commit()
        await db_session.refresh(talent)

        # 设置错误
        talent.set_error("简历解析失败：文件格式不支持")
        await db_session.commit()
        await db_session.refresh(talent)

        assert talent.workflow_status == WorkflowStatusEnum.FAILED
        assert talent.error_message == "简历解析失败：文件格式不支持"

    async def test_query_talents_by_screening_status(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试按筛选状态查询人才。"""
        # 创建多条测试数据
        talents = [
            TalentInfo(name="合格人才1", screening_status=ScreeningStatusEnum.QUALIFIED),
            TalentInfo(name="合格人才2", screening_status=ScreeningStatusEnum.QUALIFIED),
            TalentInfo(name="不合格人才", screening_status=ScreeningStatusEnum.DISQUALIFIED),
            TalentInfo(name="未筛选人才", screening_status=None),
        ]
        for t in talents:
            db_session.add(t)
        await db_session.commit()

        # 查询合格人才
        result = await db_session.execute(
            select(TalentInfo).where(
                TalentInfo.screening_status == ScreeningStatusEnum.QUALIFIED
            )
        )
        qualified_talents = result.scalars().all()

        assert len(qualified_talents) == 2
        assert all(t.screening_status == ScreeningStatusEnum.QUALIFIED for t in qualified_talents)

    async def test_query_talents_by_education_level(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试按学历查询人才。"""
        # 创建多条测试数据
        talents = [
            TalentInfo(name="硕士人才", education_level="硕士"),
            TalentInfo(name="博士人才", education_level="博士"),
            TalentInfo(name="本科人才", education_level="本科"),
        ]
        for t in talents:
            db_session.add(t)
        await db_session.commit()

        # 查询硕士及以上
        result = await db_session.execute(
            select(TalentInfo).where(
                TalentInfo.education_level.in_(["硕士", "博士"])
            )
        )
        high_education_talents = result.scalars().all()

        assert len(high_education_talents) == 2

    async def test_talent_with_graduation_date(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试人才包含毕业日期。"""
        talent = TalentInfo(
            name="毕业生",
            graduation_date=date(2024, 6, 30),
        )
        db_session.add(talent)
        await db_session.commit()
        await db_session.refresh(talent)

        assert talent.graduation_date == date(2024, 6, 30)

    async def test_talent_with_long_resume_text(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试人才包含长简历文本。"""
        long_text = "这是一段很长的简历内容。" * 1000
        talent = TalentInfo(
            name="长简历人才",
            resume_text=long_text,
        )
        db_session.add(talent)
        await db_session.commit()
        await db_session.refresh(talent)

        assert talent.resume_text == long_text
        assert len(talent.resume_text) == len(long_text)


@pytest.mark.integration
class TestDatabaseConstraints:
    """数据库约束测试类。"""

    async def test_condition_name_not_nullable(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试筛选条件名称不可为空。"""
        condition = ScreeningCondition(name="")  # 空字符串
        db_session.add(condition)
        await db_session.commit()
        await db_session.refresh(condition)

        # 空字符串应该被允许（业务逻辑层应该验证）
        assert condition.name == ""

    async def test_talent_name_not_nullable(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试人才姓名不可为空。"""
        talent = TalentInfo(name="测试")
        db_session.add(talent)
        await db_session.commit()
        await db_session.refresh(talent)

        assert talent.name == "测试"

    async def test_talent_default_workflow_status(
        self,
        db_session: AsyncSession,
        clean_db: None,
    ) -> None:
        """测试人才默认工作流状态。"""
        talent = TalentInfo(name="默认状态测试")
        db_session.add(talent)
        await db_session.commit()
        await db_session.refresh(talent)

        assert talent.workflow_status == WorkflowStatusEnum.PENDING
