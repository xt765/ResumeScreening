"""用户模型模块。

该模块定义了用户（user）表的 SQLAlchemy 模型，
用于存储系统用户信息。

Classes:
    RoleEnum: 用户角色枚举
    User: 用户表模型
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Index, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class RoleEnum(StrEnum):
    """用户角色枚举。

    定义系统中的用户角色类型。

    Attributes:
        ADMIN: 管理员，可创建/管理用户、查看所有数据
        HR: HR 用户，可管理筛选条件、上传简历、查看人才
        VIEWER: 访客，仅可查看数据，不可修改
    """

    ADMIN = "admin"
    HR = "hr"
    VIEWER = "viewer"


class User(Base, TimestampMixin):
    """用户表模型。

    存储系统用户信息，包括认证信息和角色权限。

    Attributes:
        id: 主键，UUID 格式
        username: 用户名（唯一）
        email: 邮箱（唯一）
        password_hash: 密码哈希（bcrypt）
        nickname: 昵称
        role: 用户角色（admin, hr, viewer）
        is_active: 是否激活
        is_first_login: 是否首次登录（首次登录强制修改密码）
        last_login: 最后登录时间
        created_at: 创建时间
        updated_at: 更新时间

    Table:
        user

    Indexes:
        ix_user_username: 用户名索引（唯一）
        ix_user_email: 邮箱索引（唯一）
    """

    __tablename__ = "user"

    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="主键ID",
    )
    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="用户名",
    )
    email: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="邮箱",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="密码哈希",
    )
    nickname: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        default="",
        comment="昵称",
    )
    role: Mapped[RoleEnum] = mapped_column(
        SQLEnum(RoleEnum),
        nullable=False,
        default=RoleEnum.HR,
        comment="用户角色",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否激活",
    )
    is_first_login: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否首次登录",
    )
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后登录时间",
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

    __table_args__ = (
        Index("ix_user_username", "username", unique=True),
        Index("ix_user_email", "email", unique=True),
        {"comment": "用户表"},
    )

    def __repr__(self) -> str:
        """返回模型的可读字符串表示。"""
        return f"<User(id={self.id}, username={self.username}, role={self.role.value})>"

    def to_dict(self, include_sensitive: bool = False) -> dict[str, Any]:
        """将模型转换为字典格式。

        Args:
            include_sensitive: 是否包含敏感信息（密码哈希）
                默认为 False，敏感信息不会被包含

        Returns:
            dict[str, Any]: 包含所有字段的字典
        """
        result = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "nickname": self.nickname,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_first_login": self.is_first_login,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_sensitive:
            result["password_hash"] = self.password_hash

        return result

    def update_last_login(self) -> None:
        """更新最后登录时间为当前时间。"""
        self.last_login = datetime.now()

    def mark_password_changed(self) -> None:
        """标记密码已修改，取消首次登录状态。"""
        self.is_first_login = False
