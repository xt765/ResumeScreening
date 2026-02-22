"""筛选条件 Schema 模块。

定义筛选条件的创建、更新、响应和查询模型。
支持多条件组合筛选，包括与或非逻辑。
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class EducationLevel(StrEnum):
    """学历等级枚举。

    定义支持的学历层次。

    Attributes:
        DOCTOR: 博士。
        MASTER: 硕士。
        BACHELOR: 本科。
        COLLEGE: 大专。
        HIGH_SCHOOL: 高中及以下。
    """

    DOCTOR = "doctor"
    MASTER = "master"
    BACHELOR = "bachelor"
    COLLEGE = "college"
    HIGH_SCHOOL = "high_school"


class SchoolTier(StrEnum):
    """学校层次枚举。

    定义学校等级分类。

    Attributes:
        TOP: 顶尖院校（985/C9）。
        KEY: 重点院校（211）。
        ORDINARY: 普通院校。
        OVERSEAS: 海外院校。
    """

    TOP = "top"
    KEY = "key"
    ORDINARY = "ordinary"
    OVERSEAS = "overseas"


class LogicalOperator(StrEnum):
    """逻辑运算符枚举。

    定义条件之间的逻辑关系。

    Attributes:
        AND: 与运算，所有条件都必须满足。
        OR: 或运算，满足任一条件即可。
        NOT: 非运算，排除满足条件的结果。
    """

    AND = "and"
    OR = "or"
    NOT = "not"


class ComparisonOperator(StrEnum):
    """比较运算符枚举。

    定义字段值的比较方式。

    Attributes:
        EQ: 等于。
        NE: 不等于。
        GT: 大于。
        GTE: 大于等于。
        LT: 小于。
        LTE: 小于等于。
        IN: 包含于。
        NOT_IN: 不包含于。
        CONTAINS: 包含（字符串/数组）。
        STARTS_WITH: 以...开头。
        ENDS_WITH: 以...结尾。
    """

    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


class FilterCondition(BaseModel):
    """单个筛选条件。

    定义一个字段的筛选规则。

    Attributes:
        field: 字段名称。
        operator: 比较运算符。
        value: 比较值。
    """

    field: str = Field(
        ...,
        description="字段名称",
        examples=["education_level", "work_years", "skills"],
    )
    operator: ComparisonOperator = Field(
        default=ComparisonOperator.EQ,
        description="比较运算符",
    )
    value: Any = Field(
        ...,
        description="比较值",
        examples=["master", 3, ["Python", "Java"]],
    )


class ConditionGroup(BaseModel):
    """条件组。

    支持嵌套的条件组合，实现复杂的筛选逻辑。

    Attributes:
        operator: 逻辑运算符（AND/OR/NOT）。
        conditions: 子条件列表（可以是 FilterCondition 或 ConditionGroup）。
    """

    operator: LogicalOperator = Field(
        default=LogicalOperator.AND,
        description="逻辑运算符",
    )
    conditions: list[Union[FilterCondition, "ConditionGroup"]] = Field(
        default_factory=list,
        description="子条件列表",
    )


class ConditionConfig(BaseModel):
    """筛选条件配置。

    定义具体的筛选条件参数，支持简单模式和高级模式。

    简单模式（向后兼容）：
        - skills: 技能要求列表
        - education_level: 最低学历要求
        - experience_years: 工作经验年限要求
        - major: 专业要求列表
        - school_tier: 学校层次要求

    高级模式：
        - filter_rules: 条件组，支持嵌套和与或非逻辑

    Attributes:
        skills: 技能要求列表（简单模式）。
        education_level: 最低学历要求（简单模式）。
        experience_years: 工作经验年限要求（简单模式）。
        experience_years_max: 工作经验年限上限（简单模式）。
        major: 专业要求列表（简单模式）。
        school_tier: 学校层次要求（简单模式）。
        age_min: 年龄下限（简单模式）。
        age_max: 年龄上限（简单模式）。
        locations: 工作地点要求列表（简单模式）。
        certifications: 证书要求列表（简单模式）。
        salary_min: 期望薪资下限（简单模式）。
        salary_max: 期望薪资上限（简单模式）。
        keywords: 关键词要求列表（简单模式）。
        filter_rules: 高级条件组（高级模式）。
    """

    # 简单模式字段
    skills: list[str] = Field(
        default_factory=list,
        description="技能要求列表",
        examples=[["Python", "Java", "SQL"]],
    )
    education_level: EducationLevel | None = Field(
        default=None,
        description="最低学历要求",
        examples=["master"],
    )
    experience_years: int | None = Field(
        default=None,
        ge=0,
        le=50,
        description="工作经验年限要求（最小值）",
        examples=[3],
    )
    experience_years_max: int | None = Field(
        default=None,
        ge=0,
        le=50,
        description="工作经验年限要求（最大值）",
        examples=[10],
    )
    major: list[str] = Field(
        default_factory=list,
        description="专业要求列表",
        examples=[["计算机科学与技术", "软件工程"]],
    )
    school_tier: SchoolTier | None = Field(
        default=None,
        description="学校层次要求",
        examples=["key"],
    )

    # 扩展筛选字段
    age_min: int | None = Field(
        default=None,
        ge=18,
        le=65,
        description="年龄下限",
        examples=[25],
    )
    age_max: int | None = Field(
        default=None,
        ge=18,
        le=65,
        description="年龄上限",
        examples=[45],
    )
    locations: list[str] = Field(
        default_factory=list,
        description="工作地点要求列表",
        examples=[["北京", "上海", "深圳"]],
    )
    certifications: list[str] = Field(
        default_factory=list,
        description="证书要求列表",
        examples=[["PMP", "AWS认证", "CPA"]],
    )
    salary_min: int | None = Field(
        default=None,
        ge=0,
        description="期望薪资下限（单位：千元/月）",
        examples=[15],
    )
    salary_max: int | None = Field(
        default=None,
        ge=0,
        description="期望薪资上限（单位：千元/月）",
        examples=[30],
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="关键词要求列表（匹配简历文本）",
        examples=[["微服务", "分布式", "高并发"]],
    )

    # 高级模式
    filter_rules: ConditionGroup | None = Field(
        default=None,
        description="高级条件组（支持与或非逻辑）",
    )

    @model_validator(mode="after")
    def validate_experience_years(self) -> "ConditionConfig":
        """验证工作年限范围。

        Returns:
            ConditionConfig: 验证后的配置

        Raises:
            ValueError: 当最大值小于最小值时
        """
        if (
            self.experience_years is not None
            and self.experience_years_max is not None
            and self.experience_years_max < self.experience_years
        ):
            raise ValueError("工作年限最大值不能小于最小值")
        return self

    @model_validator(mode="after")
    def validate_age_range(self) -> "ConditionConfig":
        """验证年龄范围。

        Returns:
            ConditionConfig: 验证后的配置

        Raises:
            ValueError: 当最大值小于最小值时
        """
        if self.age_min is not None and self.age_max is not None and self.age_max < self.age_min:
            raise ValueError("年龄最大值不能小于最小值")
        return self

    @model_validator(mode="after")
    def validate_salary_range(self) -> "ConditionConfig":
        """验证薪资范围。

        Returns:
            ConditionConfig: 验证后的配置

        Raises:
            ValueError: 当最大值小于最小值时
        """
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            raise ValueError("薪资最大值不能小于最小值")
        return self


class ConditionBase(BaseModel):
    """筛选条件基础模型。

    提供筛选条件的公共字段。

    Attributes:
        name: 条件名称。
        description: 条件描述。
        config: 条件配置。
        is_active: 是否启用。
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="条件名称",
        examples=["高级Python开发工程师筛选条件"],
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="条件描述",
        examples=["用于筛选高级Python开发工程师的条件"],
    )
    config: ConditionConfig = Field(
        ...,
        description="条件配置",
    )
    is_active: bool = Field(
        default=True,
        description="是否启用",
    )


class ConditionCreate(ConditionBase):
    """筛选条件创建请求模型。

    用于创建新的筛选条件。

    Attributes:
        name: 条件名称。
        description: 条件描述。
        config: 条件配置。
        is_active: 是否启用。
    """

    pass


class ConditionUpdate(BaseModel):
    """筛选条件更新请求模型。

    用于更新现有筛选条件，所有字段均为可选。

    Attributes:
        name: 条件名称。
        description: 条件描述。
        config: 条件配置。
        is_active: 是否启用。
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="条件名称",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="条件描述",
    )
    config: ConditionConfig | None = Field(
        default=None,
        description="条件配置",
    )
    is_active: bool | None = Field(
        default=None,
        description="是否启用",
    )


class ConditionResponse(ConditionBase):
    """筛选条件响应模型。

    用于返回筛选条件信息。

    Attributes:
        id: 条件ID。
        name: 条件名称。
        description: 条件描述。
        config: 条件配置。
        is_active: 是否启用。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    id: str = Field(..., description="条件ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class ConditionQuery(BaseModel):
    """筛选条件查询参数模型。

    用于查询筛选条件列表。

    Attributes:
        name: 条件名称（模糊匹配）。
        is_active: 是否启用。
        page: 页码。
        page_size: 每页数量。
    """

    name: str | None = Field(
        default=None,
        max_length=100,
        description="条件名称（模糊匹配）",
    )
    is_active: bool | None = Field(
        default=None,
        description="是否启用",
    )
    page: int = Field(
        default=1,
        ge=1,
        description="页码（从 1 开始）",
    )
    page_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="每页数量",
    )

    @field_validator("page_size", mode="before")
    @classmethod
    def validate_page_size(cls, v: Any) -> int:
        """验证并转换 page_size 参数。

        Args:
            v: 输入值。

        Returns:
            转换后的整数值。

        Raises:
            ValueError: 当值无效时。
        """
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError as err:
                raise ValueError("page_size 必须是有效的整数") from err
        return v


class NLParseRequest(BaseModel):
    """自然语言解析请求模型。

    用于将自然语言描述转换为结构化筛选条件。

    Attributes:
        text: 自然语言描述文本。
    """

    text: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="自然语言描述文本",
        examples=["需要本科及以上学历，3年以上工作经验，掌握 Python 和 Java"],
    )


class NLParseResponse(BaseModel):
    """自然语言解析响应模型。

    返回解析后的结构化筛选条件。

    Attributes:
        name: 条件名称。
        description: 条件描述。
        config: 条件配置。
    """

    name: str = Field(..., description="条件名称")
    description: str | None = Field(default=None, description="条件描述")
    config: ConditionConfig = Field(..., description="条件配置")
