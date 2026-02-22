"""Schema 测试模块。

测试 Pydantic Schema 模型的验证和转换：
- ConditionCreate/Update/Response 测试
- TalentCreate/Response 测试
- 验证器测试
"""

from datetime import date, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from src.schemas.condition import (
    ConditionConfig,
    ConditionCreate,
    ConditionQuery,
    ConditionResponse,
    ConditionUpdate,
    EducationLevel,
    SchoolTier,
)
from src.schemas.talent import (
    CandidateInfo,
    TalentBase,
    TalentCreate,
    TalentListResponse,
    TalentQuery,
    TalentResponse,
)


# ==================== EducationLevel 枚举测试 ====================

class TestEducationLevel:
    """EducationLevel 枚举测试类。"""

    def test_education_level_values(self) -> None:
        """测试学历等级枚举值。"""
        assert EducationLevel.DOCTOR.value == "doctor"
        assert EducationLevel.MASTER.value == "master"
        assert EducationLevel.BACHELOR.value == "bachelor"
        assert EducationLevel.COLLEGE.value == "college"
        assert EducationLevel.HIGH_SCHOOL.value == "high_school"

    def test_education_level_count(self) -> None:
        """测试学历等级枚举值数量。"""
        assert len(EducationLevel) == 5


# ==================== SchoolTier 枚举测试 ====================

class TestSchoolTier:
    """SchoolTier 枚举测试类。"""

    def test_school_tier_values(self) -> None:
        """测试学校层次枚举值。"""
        assert SchoolTier.TOP.value == "top"
        assert SchoolTier.KEY.value == "key"
        assert SchoolTier.ORDINARY.value == "ordinary"
        assert SchoolTier.OVERSEAS.value == "overseas"

    def test_school_tier_count(self) -> None:
        """测试学校层次枚举值数量。"""
        assert len(SchoolTier) == 4


# ==================== ConditionConfig 测试 ====================

class TestConditionConfig:
    """ConditionConfig Schema 测试类。"""

    def test_create_config_with_all_fields(self) -> None:
        """测试创建包含所有字段的配置。"""
        config = ConditionConfig(
            skills=["Python", "Java"],
            education_level=EducationLevel.MASTER,
            experience_years=5,
            major=["计算机科学"],
            school_tier=SchoolTier.KEY,
        )

        assert config.skills == ["Python", "Java"]
        assert config.education_level == EducationLevel.MASTER
        assert config.experience_years == 5
        assert config.major == ["计算机科学"]
        assert config.school_tier == SchoolTier.KEY

    def test_create_config_with_defaults(self) -> None:
        """测试创建使用默认值的配置。"""
        config = ConditionConfig()

        assert config.skills == []
        assert config.education_level is None
        assert config.experience_years is None
        assert config.major == []
        assert config.school_tier is None

    def test_config_experience_years_validation(self) -> None:
        """测试工作年限验证。"""
        # 有效值
        config = ConditionConfig(experience_years=0)
        assert config.experience_years == 0

        config = ConditionConfig(experience_years=50)
        assert config.experience_years == 50

        # 无效值
        with pytest.raises(ValidationError):
            ConditionConfig(experience_years=-1)

        with pytest.raises(ValidationError):
            ConditionConfig(experience_years=51)

    def test_config_model_dump(self) -> None:
        """测试配置转换为字典。"""
        config = ConditionConfig(
            skills=["Python"],
            education_level=EducationLevel.BACHELOR,
            experience_years=3,
        )

        result = config.model_dump()

        assert result["skills"] == ["Python"]
        assert result["education_level"] == "bachelor"
        assert result["experience_years"] == 3


# ==================== ConditionCreate 测试 ====================

class TestConditionCreate:
    """ConditionCreate Schema 测试类。"""

    def test_create_condition_create(self) -> None:
        """测试创建筛选条件创建请求。"""
        data = ConditionCreate(
            name="测试条件",
            description="测试描述",
            config=ConditionConfig(skills=["Python"]),
            is_active=True,
        )

        assert data.name == "测试条件"
        assert data.description == "测试描述"
        assert data.config.skills == ["Python"]
        assert data.is_active is True

    def test_condition_create_name_validation(self) -> None:
        """测试条件名称验证。"""
        # 有效名称
        ConditionCreate(
            name="a",
            config=ConditionConfig(),
        )

        ConditionCreate(
            name="a" * 100,
            config=ConditionConfig(),
        )

        # 无效名称 - 太短
        with pytest.raises(ValidationError):
            ConditionCreate(
                name="",
                config=ConditionConfig(),
            )

        # 无效名称 - 太长
        with pytest.raises(ValidationError):
            ConditionCreate(
                name="a" * 101,
                config=ConditionConfig(),
            )

    def test_condition_create_description_validation(self) -> None:
        """测试条件描述验证。"""
        # 有效描述
        ConditionCreate(
            name="测试",
            description="这是一个描述",
            config=ConditionConfig(),
        )

        # 描述为 None
        data = ConditionCreate(
            name="测试",
            config=ConditionConfig(),
        )
        assert data.description is None

        # 描述太长
        with pytest.raises(ValidationError):
            ConditionCreate(
                name="测试",
                description="a" * 501,
                config=ConditionConfig(),
            )

    def test_condition_create_default_is_active(self) -> None:
        """测试 is_active 默认值为 True。"""
        data = ConditionCreate(
            name="测试",
            config=ConditionConfig(),
        )

        assert data.is_active is True


# ==================== ConditionUpdate 测试 ====================

class TestConditionUpdate:
    """ConditionUpdate Schema 测试类。"""

    def test_create_condition_update_all_fields(self) -> None:
        """测试创建包含所有字段的更新请求。"""
        data = ConditionUpdate(
            name="新名称",
            description="新描述",
            config=ConditionConfig(skills=["Java"]),
            is_active=False,
        )

        assert data.name == "新名称"
        assert data.description == "新描述"
        assert data.config.skills == ["Java"]
        assert data.is_active is False

    def test_condition_update_partial(self) -> None:
        """测试部分更新。"""
        # 只更新名称
        data = ConditionUpdate(name="新名称")
        assert data.name == "新名称"
        assert data.description is None
        assert data.config is None
        assert data.is_active is None

        # 只更新状态
        data = ConditionUpdate(is_active=False)
        assert data.is_active is False

    def test_condition_update_empty(self) -> None:
        """测试空更新。"""
        data = ConditionUpdate()

        assert data.name is None
        assert data.description is None
        assert data.config is None
        assert data.is_active is None


# ==================== ConditionResponse 测试 ====================

class TestConditionResponse:
    """ConditionResponse Schema 测试类。"""

    def test_create_condition_response(self) -> None:
        """测试创建筛选条件响应。"""
        now = datetime.now()
        data = ConditionResponse(
            id="test-id-123",
            name="测试条件",
            description="测试描述",
            config=ConditionConfig(skills=["Python"]),
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        assert data.id == "test-id-123"
        assert data.name == "测试条件"
        assert data.is_active is True
        assert data.created_at == now
        assert data.updated_at == now

    def test_condition_response_from_attributes(self) -> None:
        """测试从模型属性创建响应。"""
        # 模拟模型对象
        class MockCondition:
            id = "test-id"
            name = "测试"
            description = "描述"
            conditions: dict[str, Any] = {"skills": ["Python"]}
            status = "active"
            created_at = datetime.now()
            updated_at = datetime.now()

        mock = MockCondition()
        # 验证 model_config 设置正确
        assert ConditionResponse.model_config.get("from_attributes") is True


# ==================== ConditionQuery 测试 ====================

class TestConditionQuery:
    """ConditionQuery Schema 测试类。"""

    def test_create_condition_query_with_defaults(self) -> None:
        """测试创建使用默认值的查询。"""
        query = ConditionQuery()

        assert query.name is None
        assert query.is_active is None
        assert query.page == 1
        assert query.page_size == 10

    def test_condition_query_page_validation(self) -> None:
        """测试分页参数验证。"""
        # 有效值
        ConditionQuery(page=1, page_size=1)
        ConditionQuery(page=100, page_size=100)

        # 无效页码
        with pytest.raises(ValidationError):
            ConditionQuery(page=0)

        # 无效每页数量
        with pytest.raises(ValidationError):
            ConditionQuery(page_size=0)

        with pytest.raises(ValidationError):
            ConditionQuery(page_size=101)

    def test_condition_query_page_size_string_conversion(self) -> None:
        """测试 page_size 字符串转换。"""
        # 字符串转换为整数
        query = ConditionQuery(page_size="20")
        assert query.page_size == 20

        # 无效字符串
        with pytest.raises(ValidationError):
            ConditionQuery(page_size="invalid")


# ==================== CandidateInfo 测试 ====================

class TestCandidateInfo:
    """CandidateInfo Schema 测试类。"""

    def test_create_candidate_info(self) -> None:
        """测试创建候选人信息。"""
        info = CandidateInfo(
            name="张三",
            phone="13800138000",
            email="zhangsan@example.com",
            education_level=EducationLevel.MASTER,
            school="清华大学",
            major="计算机科学",
            graduation_date=date(2020, 6, 30),
            skills=["Python", "Java"],
            work_years=5,
        )

        assert info.name == "张三"
        assert info.phone == "13800138000"
        assert info.email == "zhangsan@example.com"
        assert info.education_level == EducationLevel.MASTER
        assert info.school == "清华大学"
        assert info.major == "计算机科学"
        assert info.graduation_date == date(2020, 6, 30)
        assert info.skills == ["Python", "Java"]
        assert info.work_years == 5

    def test_candidate_info_phone_validation(self) -> None:
        """测试手机号验证。"""
        # 有效手机号
        info = CandidateInfo(
            name="张三",
            phone="13800138000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
        )
        assert info.phone == "13800138000"

        # 带分隔符的手机号
        info = CandidateInfo(
            name="张三",
            phone="138-0013-8000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
        )
        assert info.phone == "13800138000"

        # 无效手机号
        with pytest.raises(ValidationError):
            CandidateInfo(
                name="张三",
                phone="123",
                email="test@example.com",
                education_level=EducationLevel.BACHELOR,
                school="北京大学",
                major="计算机",
            )

    def test_candidate_info_name_validation(self) -> None:
        """测试姓名验证。"""
        # 有效姓名
        CandidateInfo(
            name="张",
            phone="13800138000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
        )

        # 姓名太短
        with pytest.raises(ValidationError):
            CandidateInfo(
                name="",
                phone="13800138000",
                email="test@example.com",
                education_level=EducationLevel.BACHELOR,
                school="北京大学",
                major="计算机",
            )

        # 姓名太长
        with pytest.raises(ValidationError):
            CandidateInfo(
                name="a" * 51,
                phone="13800138000",
                email="test@example.com",
                education_level=EducationLevel.BACHELOR,
                school="北京大学",
                major="计算机",
            )

    def test_candidate_info_work_years_validation(self) -> None:
        """测试工作年限验证。"""
        # 有效值
        info = CandidateInfo(
            name="张三",
            phone="13800138000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
            work_years=0,
        )
        assert info.work_years == 0

        info = CandidateInfo(
            name="张三",
            phone="13800138000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
            work_years=50,
        )
        assert info.work_years == 50

        # 无效值
        with pytest.raises(ValidationError):
            CandidateInfo(
                name="张三",
                phone="13800138000",
                email="test@example.com",
                education_level=EducationLevel.BACHELOR,
                school="北京大学",
                major="计算机",
                work_years=-1,
            )

        with pytest.raises(ValidationError):
            CandidateInfo(
                name="张三",
                phone="13800138000",
                email="test@example.com",
                education_level=EducationLevel.BACHELOR,
                school="北京大学",
                major="计算机",
                work_years=51,
            )


# ==================== TalentBase 测试 ====================

class TestTalentBase:
    """TalentBase Schema 测试类。"""

    def test_create_talent_base(self) -> None:
        """测试创建人才基础信息。"""
        from pydantic import SecretStr

        talent = TalentBase(
            name="张三",
            phone=SecretStr("13800138000"),
            email=SecretStr("zhangsan@example.com"),
            education_level=EducationLevel.MASTER,
            school="清华大学",
            major="计算机科学",
        )

        assert talent.name == "张三"
        assert talent.phone.get_secret_value() == "13800138000"
        assert talent.email.get_secret_value() == "zhangsan@example.com"


# ==================== TalentCreate 测试 ====================

class TestTalentCreate:
    """TalentCreate Schema 测试类。"""

    def test_create_talent_create(self) -> None:
        """测试创建人才创建请求。"""
        from pydantic import SecretStr

        talent = TalentCreate(
            name="张三",
            phone=SecretStr("13800138000"),
            email=SecretStr("zhangsan@example.com"),
            education_level=EducationLevel.MASTER,
            school="清华大学",
            major="计算机科学",
            work_years=5,
            skills=["Python", "Java"],
            condition_id=1,
            match_score=0.85,
            match_reason="技能匹配度高",
        )

        assert talent.condition_id == 1
        assert talent.match_score == 0.85
        assert talent.match_reason == "技能匹配度高"

    def test_talent_create_match_score_validation(self) -> None:
        """测试匹配分数验证。"""
        from pydantic import SecretStr

        # 有效值
        TalentCreate(
            name="张三",
            phone=SecretStr("13800138000"),
            email=SecretStr("test@example.com"),
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
            match_score=0.0,
        )

        TalentCreate(
            name="张三",
            phone=SecretStr("13800138000"),
            email=SecretStr("test@example.com"),
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
            match_score=1.0,
        )

        # 无效值
        with pytest.raises(ValidationError):
            TalentCreate(
                name="张三",
                phone=SecretStr("13800138000"),
                email=SecretStr("test@example.com"),
                education_level=EducationLevel.BACHELOR,
                school="北京大学",
                major="计算机",
                match_score=-0.1,
            )

        with pytest.raises(ValidationError):
            TalentCreate(
                name="张三",
                phone=SecretStr("13800138000"),
                email=SecretStr("test@example.com"),
                education_level=EducationLevel.BACHELOR,
                school="北京大学",
                major="计算机",
                match_score=1.1,
            )


# ==================== TalentResponse 测试 ====================

class TestTalentResponse:
    """TalentResponse Schema 测试类。"""

    def test_create_talent_response(self) -> None:
        """测试创建人才响应。"""
        now = datetime.now()
        response = TalentResponse(
            id=1,
            name="张三",
            phone="13800138000",
            email="zhangsan@example.com",
            education_level=EducationLevel.MASTER,
            school="清华大学",
            major="计算机科学",
            graduation_date=date(2020, 6, 30),
            skills=["Python"],
            work_years=5,
            resume_path=None,
            condition_id=None,
            match_score=None,
            match_reason=None,
            screening_date=date(2024, 1, 15),
            created_at=now,
            updated_at=now,
        )

        assert response.id == 1
        assert response.name == "张三"
        assert response.phone == "13800138000"
        assert response.email == "zhangsan@example.com"


# ==================== TalentQuery 测试 ====================

class TestTalentQuery:
    """TalentQuery Schema 测试类。"""

    def test_create_talent_query_with_defaults(self) -> None:
        """测试创建使用默认值的查询。"""
        query = TalentQuery()

        assert query.name is None
        assert query.major is None
        assert query.school is None
        assert query.education_level is None
        assert query.min_work_years is None
        assert query.max_work_years is None
        assert query.screening_date_start is None
        assert query.screening_date_end is None
        assert query.min_match_score is None
        assert query.condition_id is None
        assert query.page == 1
        assert query.page_size == 10

    def test_talent_query_work_years_range_validation(self) -> None:
        """测试工作年限范围验证。"""
        # 有效范围
        TalentQuery(min_work_years=1, max_work_years=5)

        # 无效范围 - 最大值小于最小值
        with pytest.raises(ValidationError):
            TalentQuery(min_work_years=5, max_work_years=1)

    def test_talent_query_date_range_validation(self) -> None:
        """测试日期范围验证。"""
        # 有效范围
        TalentQuery(
            screening_date_start=date(2024, 1, 1),
            screening_date_end=date(2024, 12, 31),
        )

        # 无效范围 - 截止日期早于起始日期
        with pytest.raises(ValidationError):
            TalentQuery(
                screening_date_start=date(2024, 12, 31),
                screening_date_end=date(2024, 1, 1),
            )

    def test_talent_query_match_score_validation(self) -> None:
        """测试匹配分数验证。"""
        # 有效值
        TalentQuery(min_match_score=0.0)
        TalentQuery(min_match_score=1.0)

        # 无效值
        with pytest.raises(ValidationError):
            TalentQuery(min_match_score=-0.1)

        with pytest.raises(ValidationError):
            TalentQuery(min_match_score=1.1)


# ==================== TalentListResponse 测试 ====================

class TestTalentListResponse:
    """TalentListResponse Schema 测试类。"""

    def test_create_talent_list_response(self) -> None:
        """测试创建人才列表响应。"""
        now = datetime.now()
        items = [
            TalentResponse(
                id=1,
                name="张三",
                phone="13800138000",
                email="zhangsan@example.com",
                education_level=EducationLevel.MASTER,
                school="清华大学",
                major="计算机科学",
                work_years=5,
                screening_date=date(2024, 1, 15),
                created_at=now,
                updated_at=now,
            ),
        ]

        response = TalentListResponse(
            items=items,
            total=1,
            page=1,
            page_size=10,
            total_pages=1,
        )

        assert len(response.items) == 1
        assert response.total == 1
        assert response.page == 1
        assert response.page_size == 10
        assert response.total_pages == 1

    def test_talent_list_response_empty(self) -> None:
        """测试空列表响应。"""
        response = TalentListResponse(
            items=[],
            total=0,
            page=1,
            page_size=10,
            total_pages=0,
        )

        assert len(response.items) == 0
        assert response.total == 0
        assert response.total_pages == 0


# ==================== 边界情况测试 ====================

class TestSchemaEdgeCases:
    """Schema 边界情况测试类。"""

    def test_condition_config_with_empty_lists(self) -> None:
        """测试配置包含空列表。"""
        config = ConditionConfig(
            skills=[],
            major=[],
        )

        assert config.skills == []
        assert config.major == []

    def test_candidate_info_with_unicode(self) -> None:
        """测试候选人信息包含 Unicode 字符。"""
        info = CandidateInfo(
            name="张三 🎉",
            phone="13800138000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学（PKU）",
            major="计算机科学与技术💻",
        )

        assert "🎉" in info.name
        assert "（PKU）" in info.school
        assert "💻" in info.major

    def test_talent_query_with_all_filters(self) -> None:
        """测试查询包含所有过滤条件。"""
        query = TalentQuery(
            name="张",
            major="计算机",
            school="大学",
            education_level=EducationLevel.MASTER,
            min_work_years=3,
            max_work_years=10,
            screening_date_start=date(2024, 1, 1),
            screening_date_end=date(2024, 12, 31),
            min_match_score=0.5,
            condition_id=1,
            page=2,
            page_size=20,
        )

        assert query.name == "张"
        assert query.major == "计算机"
        assert query.school == "大学"
        assert query.education_level == EducationLevel.MASTER
        assert query.min_work_years == 3
        assert query.max_work_years == 10
        assert query.page == 2
        assert query.page_size == 20


# ==================== 深度验证器测试 ====================


class TestDeepValidators:
    """深度验证器测试类。

    测试各种边界条件和验证逻辑。
    """

    # -------------------- ConditionConfig 验证测试 --------------------

    def test_condition_config_skills_list_validation(self) -> None:
        """测试技能列表验证。"""
        # 空列表
        config = ConditionConfig(skills=[])
        assert config.skills == []

        # 多个技能
        config = ConditionConfig(skills=["Python", "Java", "Go", "Rust"])
        assert len(config.skills) == 4

    def test_condition_config_major_list_validation(self) -> None:
        """测试专业列表验证。"""
        # 空列表
        config = ConditionConfig(major=[])
        assert config.major == []

        # 多个专业
        config = ConditionConfig(major=["计算机科学", "软件工程", "人工智能"])
        assert len(config.major) == 3

    def test_condition_config_experience_years_boundary(self) -> None:
        """测试工作年限边界值。"""
        # 最小值
        config = ConditionConfig(experience_years=0)
        assert config.experience_years == 0

        # 最大值
        config = ConditionConfig(experience_years=50)
        assert config.experience_years == 50

        # 边界外 - 负数
        with pytest.raises(ValidationError):
            ConditionConfig(experience_years=-1)

        # 边界外 - 超过最大值
        with pytest.raises(ValidationError):
            ConditionConfig(experience_years=51)

    # -------------------- CandidateInfo 验证测试 --------------------

    def test_candidate_info_phone_formats(self) -> None:
        """测试各种手机号格式。"""
        # 标准 11 位手机号
        info = CandidateInfo(
            name="张三",
            phone="13800138000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
        )
        assert info.phone == "13800138000"

        # 带分隔符的手机号
        info = CandidateInfo(
            name="张三",
            phone="138-0013-8000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
        )
        assert info.phone == "13800138000"

        # 带空格的手机号
        info = CandidateInfo(
            name="张三",
            phone="138 0013 8000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
        )
        assert info.phone == "13800138000"

    def test_candidate_info_phone_invalid_formats(self) -> None:
        """测试无效手机号格式。"""
        # 太短
        with pytest.raises(ValidationError):
            CandidateInfo(
                name="张三",
                phone="123",
                email="test@example.com",
                education_level=EducationLevel.BACHELOR,
                school="北京大学",
                major="计算机",
            )

        # 非字符串类型
        with pytest.raises(ValidationError):
            CandidateInfo(
                name="张三",
                phone=12345678901,  # type: ignore
                email="test@example.com",
                education_level=EducationLevel.BACHELOR,
                school="北京大学",
                major="计算机",
            )

    def test_candidate_info_email_validation(self) -> None:
        """测试邮箱验证。"""
        # 有效邮箱
        info = CandidateInfo(
            name="张三",
            phone="13800138000",
            email="zhangsan@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
        )
        assert info.email == "zhangsan@example.com"

        # 带子域名的邮箱
        info = CandidateInfo(
            name="张三",
            phone="13800138000",
            email="zhangsan@mail.example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
        )
        assert "mail.example.com" in info.email

        # 无效邮箱
        with pytest.raises(ValidationError):
            CandidateInfo(
                name="张三",
                phone="13800138000",
                email="invalid-email",
                education_level=EducationLevel.BACHELOR,
                school="北京大学",
                major="计算机",
            )

    def test_candidate_info_name_length_validation(self) -> None:
        """测试姓名长度验证。"""
        # 最小长度
        info = CandidateInfo(
            name="张",
            phone="13800138000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
        )
        assert info.name == "张"

        # 最大长度
        long_name = "张" * 50
        info = CandidateInfo(
            name=long_name,
            phone="13800138000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
        )
        assert len(info.name) == 50

        # 超过最大长度
        with pytest.raises(ValidationError):
            CandidateInfo(
                name="张" * 51,
                phone="13800138000",
                email="test@example.com",
                education_level=EducationLevel.BACHELOR,
                school="北京大学",
                major="计算机",
            )

    def test_candidate_info_work_years_boundary(self) -> None:
        """测试工作年限边界值。"""
        # 默认值
        info = CandidateInfo(
            name="张三",
            phone="13800138000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
        )
        assert info.work_years == 0

        # 最小值
        info = CandidateInfo(
            name="张三",
            phone="13800138000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
            work_years=0,
        )
        assert info.work_years == 0

        # 最大值
        info = CandidateInfo(
            name="张三",
            phone="13800138000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
            work_years=50,
        )
        assert info.work_years == 50

        # 超过最大值
        with pytest.raises(ValidationError):
            CandidateInfo(
                name="张三",
                phone="13800138000",
                email="test@example.com",
                education_level=EducationLevel.BACHELOR,
                school="北京大学",
                major="计算机",
                work_years=51,
            )

    # -------------------- ConditionCreate 验证测试 --------------------

    def test_condition_create_name_length_validation(self) -> None:
        """测试条件名称长度验证。"""
        # 最小长度
        data = ConditionCreate(
            name="a",
            config=ConditionConfig(),
        )
        assert data.name == "a"

        # 最大长度
        data = ConditionCreate(
            name="a" * 100,
            config=ConditionConfig(),
        )
        assert len(data.name) == 100

        # 空字符串
        with pytest.raises(ValidationError):
            ConditionCreate(
                name="",
                config=ConditionConfig(),
            )

        # 超过最大长度
        with pytest.raises(ValidationError):
            ConditionCreate(
                name="a" * 101,
                config=ConditionConfig(),
            )

    def test_condition_create_description_length_validation(self) -> None:
        """测试条件描述长度验证。"""
        # 最大长度
        data = ConditionCreate(
            name="测试",
            description="a" * 500,
            config=ConditionConfig(),
        )
        assert len(data.description) == 500

        # 超过最大长度
        with pytest.raises(ValidationError):
            ConditionCreate(
                name="测试",
                description="a" * 501,
                config=ConditionConfig(),
            )

    # -------------------- TalentCreate 验证测试 --------------------

    def test_talent_create_match_score_boundary(self) -> None:
        """测试匹配分数边界值。"""
        from pydantic import SecretStr

        # 最小值
        talent = TalentCreate(
            name="张三",
            phone=SecretStr("13800138000"),
            email=SecretStr("test@example.com"),
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
            match_score=0.0,
        )
        assert talent.match_score == 0.0

        # 最大值
        talent = TalentCreate(
            name="张三",
            phone=SecretStr("13800138000"),
            email=SecretStr("test@example.com"),
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
            match_score=1.0,
        )
        assert talent.match_score == 1.0

        # 超过最大值
        with pytest.raises(ValidationError):
            TalentCreate(
                name="张三",
                phone=SecretStr("13800138000"),
                email=SecretStr("test@example.com"),
                education_level=EducationLevel.BACHELOR,
                school="北京大学",
                major="计算机",
                match_score=1.1,
            )

        # 负数
        with pytest.raises(ValidationError):
            TalentCreate(
                name="张三",
                phone=SecretStr("13800138000"),
                email=SecretStr("test@example.com"),
                education_level=EducationLevel.BACHELOR,
                school="北京大学",
                major="计算机",
                match_score=-0.1,
            )

    # -------------------- TalentQuery 验证测试 --------------------

    def test_talent_query_page_validation(self) -> None:
        """测试分页参数验证。"""
        # 有效值
        query = TalentQuery(page=1)
        assert query.page == 1

        query = TalentQuery(page=1000)
        assert query.page == 1000

        # 无效值
        with pytest.raises(ValidationError):
            TalentQuery(page=0)

        with pytest.raises(ValidationError):
            TalentQuery(page=-1)

    def test_talent_query_page_size_validation(self) -> None:
        """测试每页数量验证。"""
        # 有效值
        query = TalentQuery(page_size=1)
        assert query.page_size == 1

        query = TalentQuery(page_size=100)
        assert query.page_size == 100

        # 无效值
        with pytest.raises(ValidationError):
            TalentQuery(page_size=0)

        with pytest.raises(ValidationError):
            TalentQuery(page_size=101)

    def test_talent_query_work_years_range_validation(self) -> None:
        """测试工作年限范围验证。"""
        # 有效范围
        query = TalentQuery(min_work_years=1, max_work_years=5)
        assert query.min_work_years == 1
        assert query.max_work_years == 5

        # 相等
        query = TalentQuery(min_work_years=5, max_work_years=5)
        assert query.min_work_years == 5
        assert query.max_work_years == 5

        # 无效范围 - 最大值小于最小值
        with pytest.raises(ValidationError) as exc_info:
            TalentQuery(min_work_years=5, max_work_years=1)

        assert "最大工作年限不能小于最小工作年限" in str(exc_info.value)

    def test_talent_query_date_range_validation(self) -> None:
        """测试日期范围验证。"""
        # 有效范围
        query = TalentQuery(
            screening_date_start=date(2024, 1, 1),
            screening_date_end=date(2024, 12, 31),
        )
        assert query.screening_date_start == date(2024, 1, 1)
        assert query.screening_date_end == date(2024, 12, 31)

        # 相同日期
        query = TalentQuery(
            screening_date_start=date(2024, 6, 1),
            screening_date_end=date(2024, 6, 1),
        )
        assert query.screening_date_start == query.screening_date_end

        # 无效范围 - 截止日期早于起始日期
        with pytest.raises(ValidationError) as exc_info:
            TalentQuery(
                screening_date_start=date(2024, 12, 31),
                screening_date_end=date(2024, 1, 1),
            )

        assert "截止日期不能早于起始日期" in str(exc_info.value)

    def test_talent_query_match_score_validation(self) -> None:
        """测试匹配分数验证。"""
        # 有效值
        query = TalentQuery(min_match_score=0.0)
        assert query.min_match_score == 0.0

        query = TalentQuery(min_match_score=0.5)
        assert query.min_match_score == 0.5

        query = TalentQuery(min_match_score=1.0)
        assert query.min_match_score == 1.0

        # 无效值
        with pytest.raises(ValidationError):
            TalentQuery(min_match_score=-0.1)

        with pytest.raises(ValidationError):
            TalentQuery(min_match_score=1.1)


# ==================== 模型转换测试 ====================


class TestModelConversion:
    """模型转换测试类。

    测试 Schema 之间的转换和序列化。
    """

    def test_condition_config_model_dump(self) -> None:
        """测试 ConditionConfig 序列化。"""
        config = ConditionConfig(
            skills=["Python", "Java"],
            education_level=EducationLevel.MASTER,
            experience_years=5,
            major=["计算机科学"],
            school_tier=SchoolTier.KEY,
        )

        result = config.model_dump()

        assert isinstance(result, dict)
        assert result["skills"] == ["Python", "Java"]
        assert result["education_level"] == "master"
        assert result["experience_years"] == 5
        assert result["major"] == ["计算机科学"]
        assert result["school_tier"] == "key"

    def test_condition_config_model_dump_json(self) -> None:
        """测试 ConditionConfig JSON 序列化。"""
        config = ConditionConfig(
            skills=["Python"],
            education_level=EducationLevel.BACHELOR,
        )

        json_str = config.model_dump_json()

        assert isinstance(json_str, str)
        assert "Python" in json_str
        assert "bachelor" in json_str

    def test_condition_create_model_dump(self) -> None:
        """测试 ConditionCreate 序列化。"""
        data = ConditionCreate(
            name="测试条件",
            description="测试描述",
            config=ConditionConfig(skills=["Python"]),
            is_active=True,
        )

        result = data.model_dump()

        assert result["name"] == "测试条件"
        assert result["description"] == "测试描述"
        assert result["config"]["skills"] == ["Python"]
        assert result["is_active"] is True

    def test_condition_update_model_dump(self) -> None:
        """测试 ConditionUpdate 序列化。"""
        data = ConditionUpdate(
            name="新名称",
            is_active=False,
        )

        result = data.model_dump()

        assert result["name"] == "新名称"
        assert result["description"] is None
        assert result["config"] is None
        assert result["is_active"] is False

    def test_candidate_info_model_dump(self) -> None:
        """测试 CandidateInfo 序列化。"""
        info = CandidateInfo(
            name="张三",
            phone="13800138000",
            email="zhangsan@example.com",
            education_level=EducationLevel.MASTER,
            school="清华大学",
            major="计算机科学",
            work_years=5,
        )

        result = info.model_dump()

        assert result["name"] == "张三"
        assert result["phone"] == "13800138000"
        assert result["email"] == "zhangsan@example.com"
        assert result["education_level"] == "master"
        assert result["school"] == "清华大学"
        assert result["major"] == "计算机科学"
        assert result["work_years"] == 5


# ==================== 枚举值测试 ====================


class TestEnumValues:
    """枚举值测试类。

    测试各种枚举类型的值和行为。
    """

    def test_education_level_string_values(self) -> None:
        """测试学历等级字符串值。"""
        assert EducationLevel.DOCTOR.value == "doctor"
        assert EducationLevel.MASTER.value == "master"
        assert EducationLevel.BACHELOR.value == "bachelor"
        assert EducationLevel.COLLEGE.value == "college"
        assert EducationLevel.HIGH_SCHOOL.value == "high_school"

    def test_education_level_from_string(self) -> None:
        """测试从字符串创建学历等级。"""
        assert EducationLevel("doctor") == EducationLevel.DOCTOR
        assert EducationLevel("master") == EducationLevel.MASTER
        assert EducationLevel("bachelor") == EducationLevel.BACHELOR

    def test_school_tier_string_values(self) -> None:
        """测试学校层次字符串值。"""
        assert SchoolTier.TOP.value == "top"
        assert SchoolTier.KEY.value == "key"
        assert SchoolTier.ORDINARY.value == "ordinary"
        assert SchoolTier.OVERSEAS.value == "overseas"

    def test_school_tier_from_string(self) -> None:
        """测试从字符串创建学校层次。"""
        assert SchoolTier("top") == SchoolTier.TOP
        assert SchoolTier("key") == SchoolTier.KEY
        assert SchoolTier("ordinary") == SchoolTier.ORDINARY

    def test_education_level_comparison(self) -> None:
        """测试学历等级比较。"""
        # 枚举值可以比较
        assert EducationLevel.DOCTOR == EducationLevel.DOCTOR
        assert EducationLevel.MASTER != EducationLevel.BACHELOR

    def test_school_tier_comparison(self) -> None:
        """测试学校层次比较。"""
        assert SchoolTier.TOP == SchoolTier.TOP
        assert SchoolTier.KEY != SchoolTier.ORDINARY


# ==================== 特殊场景测试 ====================


class TestSpecialScenarios:
    """特殊场景测试类。

    测试各种特殊和极端情况。
    """

    def test_condition_config_with_none_values(self) -> None:
        """测试配置包含 None 值。"""
        config = ConditionConfig(
            education_level=None,
            experience_years=None,
            school_tier=None,
        )

        assert config.education_level is None
        assert config.experience_years is None
        assert config.school_tier is None

    def test_candidate_info_with_optional_fields(self) -> None:
        """测试候选人信息包含可选字段。"""
        info = CandidateInfo(
            name="张三",
            phone="13800138000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
            graduation_date=None,
            skills=[],
            work_years=0,
        )

        assert info.graduation_date is None
        assert info.skills == []
        assert info.work_years == 0

    def test_talent_create_with_all_optional_fields(self) -> None:
        """测试人才创建包含所有可选字段。"""
        from pydantic import SecretStr

        talent = TalentCreate(
            name="张三",
            phone=SecretStr("13800138000"),
            email=SecretStr("test@example.com"),
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
            graduation_date=None,
            skills=["Python"],
            work_years=3,
            resume_path="/path/to/resume.pdf",
            condition_id=1,
            match_score=0.85,
            match_reason="技能匹配度高",
        )

        assert talent.resume_path == "/path/to/resume.pdf"
        assert talent.condition_id == 1
        assert talent.match_score == 0.85
        assert talent.match_reason == "技能匹配度高"

    def test_condition_update_all_none(self) -> None:
        """测试所有字段为 None 的更新。"""
        update = ConditionUpdate()

        assert update.name is None
        assert update.description is None
        assert update.config is None
        assert update.is_active is None

    def test_talent_query_all_none(self) -> None:
        """测试所有过滤条件为 None 的查询。"""
        query = TalentQuery()

        assert query.name is None
        assert query.major is None
        assert query.school is None
        assert query.education_level is None
        assert query.min_work_years is None
        assert query.max_work_years is None
        assert query.screening_date_start is None
        assert query.screening_date_end is None
        assert query.min_match_score is None
        assert query.condition_id is None
        # 默认值
        assert query.page == 1
        assert query.page_size == 10

    def test_condition_response_datetime_fields(self) -> None:
        """测试条件响应的日期时间字段。"""
        now = datetime.now()
        response = ConditionResponse(
            id="test-id",
            name="测试",
            config=ConditionConfig(),
            created_at=now,
            updated_at=now,
        )

        assert response.created_at == now
        assert response.updated_at == now

    def test_talent_response_datetime_fields(self) -> None:
        """测试人才响应的日期时间字段。"""
        now = datetime.now()
        response = TalentResponse(
            id=1,
            name="张三",
            phone="13800138000",
            email="test@example.com",
            education_level=EducationLevel.BACHELOR,
            school="北京大学",
            major="计算机",
            work_years=3,
            screening_date=date.today(),
            created_at=now,
            updated_at=now,
        )

        assert response.created_at == now
        assert response.updated_at == now
        assert response.screening_date == date.today()
