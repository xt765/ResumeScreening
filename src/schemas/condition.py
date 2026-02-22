"""筛选条件 Schema 模块。

定义筛选条件的创建、更新、响应和查询模型。
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


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


class ConditionConfig(BaseModel):
    """筛选条件配置。

    定义具体的筛选条件参数。

    Attributes:
        skills: 技能要求列表。
        education_level: 最低学历要求。
        experience_years: 工作经验年限要求（最小值）。
        major: 专业要求列表。
        school_tier: 学校层次要求。
    """

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
