"""SQLAlchemy 基类定义。

该模块定义 SQLAlchemy 的声明式基类和混入类，
避免循环导入问题。

Classes:
    Base: SQLAlchemy 声明式基类
    TimestampMixin: 时间戳混入类
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# 命名约定，用于约束名称生成
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类。

    所有数据库模型都应继承此类，以获得统一的元数据配置和通用方法。

    Attributes:
        metadata: 包含命名约定的元数据对象
    """

    metadata = metadata


class TimestampMixin:
    """时间戳混入类。

    为模型提供 created_at 和 updated_at 字段的自动管理。
    子类需要使用 mapped_column 定义这些字段。

    Note:
        由于 SQLAlchemy Mapped 类型与普通类型不兼容，
        子类需要重新定义这些字段并使用 Mapped[datetime] 类型。
    """

    pass


__all__ = ["Base", "TimestampMixin", "metadata"]
