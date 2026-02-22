"""API 依赖注入模块。

提供 FastAPI 路由的公共依赖项，包括：
- 数据库会话依赖注入
- 配置实例依赖注入
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
import src.models


async def get_session() -> AsyncGenerator[AsyncSession]:
    """获取数据库会话依赖。

    用于 FastAPI 的 Depends 注入，自动管理会话生命周期。
    每个请求获取独立的会话，请求结束后自动提交或回滚。

    Yields:
        AsyncSession: 异步数据库会话对象

    Raises:
        RuntimeError: 当数据库未初始化时
    """
    if src.models.async_session_factory is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")

    async with src.models.async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_settings_dep() -> Settings:
    """获取配置实例依赖。

    用于 FastAPI 的 Depends 注入，返回应用配置实例。

    Returns:
        Settings: 应用配置实例
    """
    return get_settings()


__all__ = [
    "get_session",
    "get_settings_dep",
]
