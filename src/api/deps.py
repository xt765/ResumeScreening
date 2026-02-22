"""API 依赖注入模块。

提供 FastAPI 路由的公共依赖项，包括：
- 数据库会话依赖注入
- 配置实例依赖注入
- 当前用户依赖注入
- 角色权限依赖注入
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import (
    decode_access_token,
    is_token_blacklisted,
)
from src.core.config import Settings, get_settings
import src.models
from src.models.user import RoleEnum, User

security = HTTPBearer(auto_error=False)


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


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    """获取当前登录用户（强制认证）。

    从 Authorization Header 中提取 JWT Token 并验证，
    返回当前登录的用户对象。

    Args:
        session: 数据库会话
        credentials: HTTP Bearer 凭据

    Returns:
        User: 当前登录用户

    Raises:
        HTTPException: 未提供 Token、Token 无效、Token 已失效或用户不存在
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if await is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已失效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_optional(
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User | None:
    """获取当前登录用户（可选认证）。

    从 Authorization Header 中提取 JWT Token 并验证，
    如果 Token 有效则返回用户对象，否则返回 None。

    Args:
        session: 数据库会话
        credentials: HTTP Bearer 凭据

    Returns:
        User | None: 当前登录用户或 None
    """
    if credentials is None:
        return None

    token = credentials.credentials

    payload = decode_access_token(token)
    if payload is None:
        return None

    if await is_token_blacklisted(token):
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        return None

    return user


def require_role(*roles: RoleEnum):
    """创建角色权限依赖。

    返回一个依赖函数，用于验证当前用户是否具有指定角色。

    Args:
        *roles: 允许的角色列表

    Returns:
        依赖函数

    Example:
        ```python
        @router.get("/admin-only")
        async def admin_only(user: User = Depends(require_role(RoleEnum.ADMIN))):
            return {"message": "Admin access granted"}
        ```
    """

    async def role_checker(
        user: User = Depends(get_current_user),
    ) -> User:
        if user.role not in roles:
            logger.warning(
                f"权限不足: user={user.username}, role={user.role.value}, required={[r.value for r in roles]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要 {[r.value for r in roles]} 角色",
            )
        return user

    return role_checker


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]


__all__ = [
    "CurrentUser",
    "OptionalUser",
    "get_current_user",
    "get_current_user_optional",
    "get_session",
    "get_settings_dep",
    "require_role",
]
