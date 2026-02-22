"""
人才信息表模型。

该模块定义了人才信息（talent_info）表的 SQLAlchemy 模型，
用于存储简历筛选后的人才详细信息。

Classes:
    WorkflowStatusEnum: 工作流状态枚举
    ScreeningStatusEnum: 筛选结果状态枚举
    TalentInfo: 人才信息表模型
"""

from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    CHAR,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class WorkflowStatusEnum(StrEnum):
    """工作流状态枚举。

    定义简历处理工作流的各个阶段状态。

    Attributes:
        PENDING: 待处理
        PARSING: 解析中
        FILTERING: 筛选中
        STORING: 存储中
        CACHING: 缓存中
        COMPLETED: 已完成
        FAILED: 处理失败
    """

    PENDING = "pending"
    PARSING = "parsing"
    FILTERING = "filtering"
    STORING = "storing"
    CACHING = "caching"
    COMPLETED = "completed"
    FAILED = "failed"


class ScreeningStatusEnum(StrEnum):
    """筛选结果状态枚举。

    定义简历筛选的最终结果。

    Attributes:
        QUALIFIED: 符合条件
        DISQUALIFIED: 不符合条件
    """

    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"


class TalentInfo(Base, TimestampMixin):
    """
    人才信息表模型。

    存储简历筛选后的人才详细信息，包括基本信息、教育背景、
    技能、工作经历等。

    Attributes:
        id: 主键，UUID 格式
        name: 姓名
        phone: 电话（AES 加密存储）
        email: 邮箱（AES 加密存储）
        education_level: 学历
        school: 毕业院校
        major: 专业
        graduation_date: 毕业日期
        skills: 技能列表（JSON 格式）
        work_years: 工作年限
        photo_url: 照片地址（MinIO 存储 URL）
        resume_text: 简历文本内容
        condition_id: 关联的筛选条件 ID
        workflow_status: 工作流处理状态
        screening_status: 筛选结果状态
        screening_date: 筛选日期
        error_message: 错误信息（处理失败时记录）
        created_at: 创建时间
        updated_at: 更新时间

    Table:
        talent_info

    Indexes:
        ix_talent_info_name: 姓名索引
        ix_talent_info_school: 院校索引
        ix_talent_info_major: 专业索引
        ix_talent_info_education_level: 学历索引
        ix_talent_info_screening_status: 筛选状态索引
        ix_talent_info_screening_date: 筛选日期索引
    """

    __tablename__ = "talent_info"

    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="主键ID",
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="姓名",
    )
    phone: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        default="",
        comment="电话（加密）",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        default="",
        comment="邮箱（加密）",
    )
    education_level: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        default="",
        comment="学历",
    )
    school: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        default="",
        comment="毕业院校",
    )
    major: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        default="",
        comment="专业",
    )
    graduation_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="毕业日期",
    )
    skills: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
        default=list,
        comment="技能列表",
    )
    work_years: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment="工作年限",
    )
    photo_url: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        default="",
        comment="照片地址",
    )
    resume_text: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        default="",
        comment="简历文本",
    )
    condition_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("screening_condition.id", ondelete="SET NULL"),
        nullable=True,
        comment="筛选条件ID",
    )
    workflow_status: Mapped[WorkflowStatusEnum] = mapped_column(
        SQLEnum(WorkflowStatusEnum),
        nullable=False,
        default=WorkflowStatusEnum.PENDING,
        comment="工作流状态",
    )
    screening_status: Mapped[ScreeningStatusEnum | None] = mapped_column(
        SQLEnum(ScreeningStatusEnum),
        nullable=True,
        comment="筛选结果状态",
    )
    screening_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="筛选日期",
    )
    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        default="",
        comment="错误信息",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    # 定义索引
    __table_args__ = (
        Index("ix_talent_info_name", "name"),
        Index("ix_talent_info_school", "school"),
        Index("ix_talent_info_major", "major"),
        Index("ix_talent_info_education_level", "education_level"),
        Index("ix_talent_info_screening_status", "screening_status"),
        Index("ix_talent_info_screening_date", "screening_date"),
        {"comment": "人才信息表"},
    )

    def __repr__(self) -> str:
        """返回模型的可读字符串表示。"""
        return (
            f"<TalentInfo(id={self.id}, name={self.name}, "
            f"workflow_status={self.workflow_status.value})>"
        )

    def to_dict(self, include_sensitive: bool = False) -> dict[str, Any]:
        """
        将模型转换为字典格式。

        Args:
            include_sensitive: 是否包含敏感信息（电话、邮箱）
                默认为 False，敏感信息会被脱敏处理

        Returns:
            dict[str, Any]: 包含所有字段的字典
        """
        result = {
            "id": self.id,
            "name": self.name,
            "education_level": self.education_level,
            "school": self.school,
            "major": self.major,
            "graduation_date": (self.graduation_date.isoformat() if self.graduation_date else None),
            "skills": self.skills or [],
            "work_years": self.work_years,
            "photo_url": self.photo_url,
            "condition_id": self.condition_id,
            "workflow_status": self.workflow_status.value,
            "screening_status": (self.screening_status.value if self.screening_status else None),
            "screening_date": (self.screening_date.isoformat() if self.screening_date else None),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # 敏感信息处理
        if include_sensitive:
            result["phone"] = self.phone
            result["email"] = self.email
        else:
            # 脱敏处理
            result["phone"] = self._mask_phone(self.phone) if self.phone else ""
            result["email"] = self._mask_email(self.email) if self.email else ""

        return result

    @staticmethod
    def _mask_phone(phone: str) -> str:
        """
        手机号脱敏处理。

        将手机号中间4位替换为星号，如：138****1234

        Args:
            phone: 原始手机号

        Returns:
            str: 脱敏后的手机号
        """
        if not phone or len(phone) < 7:
            return phone
        return f"{phone[:3]}****{phone[-4:]}"

    @staticmethod
    def _mask_email(email: str) -> str:
        """
        邮箱脱敏处理。

        将邮箱用户名部分保留前3位，其余替换为星号，
        如：abc***@example.com

        Args:
            email: 原始邮箱

        Returns:
            str: 脱敏后的邮箱
        """
        if not email or "@" not in email:
            return email
        username, domain = email.split("@", 1)
        if len(username) <= 3:
            masked_username = username[0] + "***"
        else:
            masked_username = username[:3] + "***"
        return f"{masked_username}@{domain}"

    def mark_as_qualified(self) -> None:
        """
        标记为符合筛选条件。

        设置筛选状态为 QUALIFIED，并记录筛选日期。
        """
        self.screening_status = ScreeningStatusEnum.QUALIFIED
        self.screening_date = datetime.now()

    def mark_as_disqualified(self) -> None:
        """
        标记为不符合筛选条件。

        设置筛选状态为 DISQUALIFIED，并记录筛选日期。
        """
        self.screening_status = ScreeningStatusEnum.DISQUALIFIED
        self.screening_date = datetime.now()

    def set_error(self, error_message: str) -> None:
        """
        设置处理错误信息。

        将工作流状态设置为 FAILED，并记录错误信息。

        Args:
            error_message: 错误信息描述
        """
        self.workflow_status = WorkflowStatusEnum.FAILED
        self.error_message = error_message
