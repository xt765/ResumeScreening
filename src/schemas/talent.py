"""人才信息 Schema 模块。

定义人才信息的创建、响应和查询模型。
"""

from datetime import date, datetime
import re
from typing import Any

from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator

from .condition import EducationLevel


class CandidateInfo(BaseModel):
    """LLM 提取的候选人信息。

    由 LLM 从简历中提取的结构化候选人信息。

    Attributes:
        name: 候选人姓名。
        phone: 联系电话。
        email: 电子邮箱。
        education_level: 学历层次。
        school: 毕业院校。
        major: 专业。
        graduation_date: 毕业日期。
        skills: 技能列表。
        work_years: 工作年限。
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="候选人姓名",
        examples=["张三"],
    )
    phone: str = Field(
        ...,
        min_length=11,
        max_length=20,
        description="联系电话",
        examples=["13800138000"],
    )
    email: EmailStr = Field(
        ...,
        description="电子邮箱",
        examples=["zhangsan@example.com"],
    )
    education_level: EducationLevel = Field(
        ...,
        description="学历层次",
        examples=["master"],
    )
    school: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="毕业院校",
        examples=["清华大学"],
    )
    major: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="专业",
        examples=["计算机科学与技术"],
    )
    graduation_date: date | None = Field(
        default=None,
        description="毕业日期",
        examples=["2020-06-30"],
    )
    skills: list[str] = Field(
        default_factory=list,
        description="技能列表",
        examples=[["Python", "Java", "SQL", "Docker"]],
    )
    work_years: int = Field(
        default=0,
        ge=0,
        le=50,
        description="工作年限",
        examples=[5],
    )

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: Any) -> str:
        """验证并格式化手机号。

        Args:
            v: 输入值。

        Returns:
            格式化后的手机号。

        Raises:
            ValueError: 当手机号格式无效时。
        """
        if isinstance(v, str):
            # 移除所有非数字字符
            phone = re.sub(r"[^\d]", "", v)
            # 验证中国大陆手机号（11位）
            if len(phone) == 11 and phone.startswith("1"):
                return phone
            # 如果是其他格式，保留原始值但发出警告
            if len(phone) >= 7:
                return phone
            raise ValueError(f"无效的手机号格式: {v}")
        raise ValueError("手机号必须是字符串类型")


class TalentBase(BaseModel):
    """人才信息基础模型。

    提供人才信息的公共字段。

    Attributes:
        name: 候选人姓名。
        phone: 联系电话（加密存储）。
        email: 电子邮箱（加密存储）。
        education_level: 学历层次。
        school: 毕业院校。
        major: 专业。
        graduation_date: 毕业日期。
        skills: 技能列表。
        work_years: 工作年限。
        resume_path: 简历文件路径。
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="候选人姓名",
    )
    phone: SecretStr = Field(
        ...,
        description="联系电话（加密存储）",
    )
    email: SecretStr = Field(
        ...,
        description="电子邮箱（加密存储）",
    )
    education_level: EducationLevel = Field(
        ...,
        description="学历层次",
    )
    school: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="毕业院校",
    )
    major: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="专业",
    )
    graduation_date: date | None = Field(
        default=None,
        description="毕业日期",
    )
    skills: list[str] = Field(
        default_factory=list,
        description="技能列表",
    )
    work_years: int = Field(
        default=0,
        ge=0,
        le=50,
        description="工作年限",
    )
    resume_path: str | None = Field(
        default=None,
        max_length=500,
        description="简历文件路径",
    )


class TalentCreate(TalentBase):
    """人才信息创建请求模型。

    用于创建新的人才记录。

    Attributes:
        name: 候选人姓名。
        phone: 联系电话（加密存储）。
        email: 电子邮箱（加密存储）。
        education_level: 学历层次。
        school: 毕业院校。
        major: 专业。
        graduation_date: 毕业日期。
        skills: 技能列表。
        work_years: 工作年限。
        resume_path: 简历文件路径。
        condition_id: 筛选条件ID。
        match_score: 匹配分数。
        match_reason: 匹配原因。
    """

    condition_id: int | None = Field(
        default=None,
        description="筛选条件ID",
    )
    match_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="匹配分数（0-1之间）",
    )
    match_reason: str | None = Field(
        default=None,
        max_length=1000,
        description="匹配原因",
    )


class TalentResponse(BaseModel):
    """人才信息响应模型。

    用于返回人才信息，解密敏感字段。

    Attributes:
        id: 人才记录ID。
        name: 候选人姓名。
        phone: 联系电话（已解密）。
        email: 电子邮箱（已解密）。
        education_level: 学历层次。
        school: 毕业院校。
        major: 专业。
        graduation_date: 毕业日期。
        skills: 技能列表。
        work_years: 工作年限。
        resume_path: 简历文件路径。
        condition_id: 筛选条件ID。
        match_score: 匹配分数。
        match_reason: 匹配原因。
        screening_date: 筛选日期。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    id: int = Field(..., description="人才记录ID")
    name: str = Field(..., description="候选人姓名")
    phone: str = Field(..., description="联系电话（已解密）")
    email: str = Field(..., description="电子邮箱（已解密）")
    education_level: EducationLevel = Field(..., description="学历层次")
    school: str = Field(..., description="毕业院校")
    major: str = Field(..., description="专业")
    graduation_date: date | None = Field(None, description="毕业日期")
    skills: list[str] = Field(default_factory=list, description="技能列表")
    work_years: int = Field(..., description="工作年限")
    resume_path: str | None = Field(None, description="简历文件路径")
    condition_id: int | None = Field(None, description="筛选条件ID")
    match_score: float | None = Field(None, description="匹配分数")
    match_reason: str | None = Field(None, description="匹配原因")
    screening_date: date = Field(..., description="筛选日期")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class TalentQuery(BaseModel):
    """人才信息查询参数模型。

    用于查询人才信息列表。

    Attributes:
        name: 候选人姓名（模糊匹配）。
        major: 专业（模糊匹配）。
        school: 毕业院校（模糊匹配）。
        education_level: 学历层次。
        min_work_years: 最小工作年限。
        max_work_years: 最大工作年限。
        screening_date_start: 筛选日期起始。
        screening_date_end: 筛选日期截止。
        min_match_score: 最小匹配分数。
        condition_id: 筛选条件ID。
        page: 页码。
        page_size: 每页数量。
    """

    name: str | None = Field(
        default=None,
        max_length=50,
        description="候选人姓名（模糊匹配）",
    )
    major: str | None = Field(
        default=None,
        max_length=100,
        description="专业（模糊匹配）",
    )
    school: str | None = Field(
        default=None,
        max_length=100,
        description="毕业院校（模糊匹配）",
    )
    education_level: EducationLevel | None = Field(
        default=None,
        description="学历层次",
    )
    min_work_years: int | None = Field(
        default=None,
        ge=0,
        le=50,
        description="最小工作年限",
    )
    max_work_years: int | None = Field(
        default=None,
        ge=0,
        le=50,
        description="最大工作年限",
    )
    screening_date_start: date | None = Field(
        default=None,
        description="筛选日期起始",
    )
    screening_date_end: date | None = Field(
        default=None,
        description="筛选日期截止",
    )
    min_match_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="最小匹配分数",
    )
    condition_id: int | None = Field(
        default=None,
        description="筛选条件ID",
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

    @field_validator("max_work_years", mode="after")
    @classmethod
    def validate_work_years_range(cls, v: int | None, info: Any) -> int | None:
        """验证工作年限范围。

        Args:
            v: 最大工作年限值。
            info: 验证上下文信息。

        Returns:
            验证后的值。

        Raises:
            ValueError: 当范围无效时。
        """
        min_years = info.data.get("min_work_years")
        if v is not None and min_years is not None and v < min_years:
            raise ValueError("最大工作年限不能小于最小工作年限")
        return v

    @field_validator("screening_date_end", mode="after")
    @classmethod
    def validate_date_range(cls, v: date | None, info: Any) -> date | None:
        """验证日期范围。

        Args:
            v: 截止日期值。
            info: 验证上下文信息。

        Returns:
            验证后的值。

        Raises:
            ValueError: 当范围无效时。
        """
        start_date = info.data.get("screening_date_start")
        if v is not None and start_date is not None and v < start_date:
            raise ValueError("截止日期不能早于起始日期")
        return v


class TalentListResponse(BaseModel):
    """人才列表响应模型。

    用于返回人才列表及统计信息。

    Attributes:
        items: 人才列表。
        total: 总记录数。
        page: 当前页码。
        page_size: 每页数量。
        total_pages: 总页数。
    """

    items: list[TalentResponse] = Field(..., description="人才列表")
    total: int = Field(..., ge=0, description="总记录数")
    page: int = Field(..., ge=1, description="当前页码")
    page_size: int = Field(..., ge=1, le=100, description="每页数量")
    total_pages: int = Field(..., ge=0, description="总页数")


class TalentUpdateRequest(BaseModel):
    """人才信息更新请求模型。

    用于更新人才信息。

    Attributes:
        name: 候选人姓名。
        phone: 联系电话。
        email: 电子邮箱。
        education_level: 学历层次。
        school: 毕业院校。
        major: 专业。
        graduation_date: 毕业日期。
        skills: 技能列表。
        work_years: 工作年限。
        screening_status: 筛选状态。
    """

    name: str | None = Field(default=None, min_length=1, max_length=50, description="候选人姓名")
    phone: str | None = Field(default=None, min_length=11, max_length=20, description="联系电话")
    email: EmailStr | None = Field(default=None, description="电子邮箱")
    education_level: EducationLevel | None = Field(default=None, description="学历层次")
    school: str | None = Field(default=None, min_length=1, max_length=100, description="毕业院校")
    major: str | None = Field(default=None, min_length=1, max_length=100, description="专业")
    graduation_date: date | None = Field(default=None, description="毕业日期")
    skills: list[str] | None = Field(default=None, description="技能列表")
    work_years: int | None = Field(default=None, ge=0, le=50, description="工作年限")
    screening_status: str | None = Field(default=None, description="筛选状态")


class BatchDeleteRequest(BaseModel):
    """批量删除请求模型。

    Attributes:
        ids: 人才ID列表。
    """

    ids: list[str] = Field(..., min_length=1, description="人才ID列表")


class BatchUpdateStatusRequest(BaseModel):
    """批量更新状态请求模型。

    Attributes:
        ids: 人才ID列表。
        screening_status: 筛选状态。
    """

    ids: list[str] = Field(..., min_length=1, description="人才ID列表")
    screening_status: str = Field(..., description="筛选状态（qualified/unqualified）")
