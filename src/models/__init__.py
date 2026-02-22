"""数据库模型模块。

该模块提供 SQLAlchemy 基类、会话管理和数据库初始化功能。
支持异步数据库操作，适用于 FastAPI 应用。

Attributes:
    Base: SQLAlchemy 声明式基类
    async_session_factory: 异步会话工厂
"""

from collections.abc import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .base import Base, TimestampMixin, metadata
from .condition import ScreeningCondition, StatusEnum
from .talent import ScreeningStatusEnum, TalentInfo, WorkflowStatusEnum
from .user import RoleEnum, User


# 异步引擎（延迟初始化）
_async_engine = None

# 异步会话工厂（延迟初始化）
async_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(database_url: str) -> None:
    """初始化数据库连接。

    创建异步引擎和会话工厂，应在应用启动时调用。

    Args:
        database_url: 数据库连接 URL（异步格式）
            例如: mysql+aiomysql://user:password@host:port/database

    Raises:
        ValueError: 当 database_url 为空时
    """
    global _async_engine, async_session_factory

    if not database_url:
        raise ValueError("数据库连接 URL 不能为空")

    logger.info(f"初始化数据库连接: {database_url.split('@')[-1]}")

    # 创建异步引擎
    _async_engine = create_async_engine(
        database_url,
        echo=False,  # 生产环境关闭 SQL 日志
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # 连接健康检查
        pool_recycle=3600,  # 连接回收时间（秒）
    )

    # 创建异步会话工厂
    async_session_factory = async_sessionmaker(
        bind=_async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    logger.success("数据库连接初始化完成")


async def close_db() -> None:
    """关闭数据库连接。

    释放所有数据库连接池资源，应在应用关闭时调用。
    """
    global _async_engine, async_session_factory

    if _async_engine is not None:
        logger.info("关闭数据库连接...")
        await _async_engine.dispose()
        _async_engine = None
        async_session_factory = None
        logger.success("数据库连接已关闭")


async def get_session() -> AsyncGenerator[AsyncSession]:
    """获取数据库会话的依赖注入函数。

    用于 FastAPI 的 Depends 注入，自动管理会话的生命周期。

    Yields:
        AsyncSession: 异步数据库会话对象

    Raises:
        RuntimeError: 当数据库未初始化时

    Example:
        ```python
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(Item))
            return result.scalars().all()
        ```
    """
    if async_session_factory is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.exception(f"数据库会话异常: {e}")
            raise


async def create_tables() -> None:
    """创建所有数据库表。

    根据模型定义创建对应的数据库表结构。
    注意：生产环境建议使用数据库迁移工具（如 Alembic）。
    """
    if _async_engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")

    logger.info("开始创建数据库表...")

    async with _async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.success("数据库表创建完成")


async def drop_tables() -> None:
    """删除所有数据库表。

    警告：此操作会删除所有数据，仅用于测试环境。
    """
    if _async_engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")

    logger.warning("开始删除所有数据库表...")

    async with _async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    logger.warning("所有数据库表已删除")


__all__ = [
    "Base",
    "RoleEnum",
    "ScreeningCondition",
    "ScreeningStatusEnum",
    "StatusEnum",
    "TalentInfo",
    "TimestampMixin",
    "User",
    "WorkflowStatusEnum",
    "async_session_factory",
    "close_db",
    "create_tables",
    "drop_tables",
    "get_session",
    "init_db",
]
