"""
筛选条件表模型。

该模块定义了筛选条件（screening_condition）表的 SQLAlchemy 模型，
用于存储简历筛选的条件配置。

Classes:
    StatusEnum: 筛选条件状态枚举
    ScreeningCondition: 筛选条件表模型
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class StatusEnum(StrEnum):
    """筛选条件状态枚举。

    定义筛选条件的生命周期状态。

    Attributes:
        ACTIVE: 活跃状态，可用于筛选
        INACTIVE: 停用状态，暂不可用
        DELETED: 已删除状态（软删除）
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class ScreeningCondition(Base, TimestampMixin):
    """
    筛选条件表模型。

    存储简历筛选的条件配置，包括技能要求、学历要求、工作年限等。

    Attributes:
        id: 主键，UUID 格式
        name: 条件名称
        description: 条件描述
        conditions: 筛选条件配置（JSON 格式）
            - skills: 技能要求列表
            - education_level: 学历要求
            - experience_years: 工作年限要求
            - major: 专业要求列表
            - school_tier: 院校层次要求列表
        status: 条件状态（active/inactive/deleted）
        created_at: 创建时间
        updated_at: 更新时间

    Table:
        screening_condition
    """

    __tablename__ = "screening_condition"

    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="主键ID",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="条件名称",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="条件描述",
    )
    conditions: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="筛选条件配置",
    )
    status: Mapped[StatusEnum] = mapped_column(
        SQLEnum(StatusEnum),
        nullable=False,
        default=StatusEnum.ACTIVE,
        comment="条件状态",
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

    def __repr__(self) -> str:
        """返回模型的可读字符串表示。"""
        return f"<ScreeningCondition(id={self.id}, name={self.name}, status={self.status.value})>"

    def to_dict(self) -> dict[str, Any]:
        """
        将模型转换为字典格式。

        Returns:
            dict[str, Any]: 包含所有字段的字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def skills(self) -> list[str]:
        """
        获取技能要求列表。

        Returns:
            list[str]: 技能要求列表
        """
        return self.conditions.get("skills", [])

    @property
    def education_level(self) -> str:
        """
        获取学历要求。

        Returns:
            str: 学历要求
        """
        return self.conditions.get("education_level", "")

    @property
    def experience_years(self) -> int:
        """
        获取工作年限要求。

        Returns:
            int: 工作年限要求
        """
        return self.conditions.get("experience_years", 0)

    @property
    def major(self) -> list[str]:
        """
        获取专业要求列表。

        Returns:
            list[str]: 专业要求列表
        """
        return self.conditions.get("major", [])

    @property
    def school_tier(self) -> list[str]:
        """
        获取院校层次要求列表。

        Returns:
            list[str]: 院校层次要求列表
        """
        return self.conditions.get("school_tier", [])
