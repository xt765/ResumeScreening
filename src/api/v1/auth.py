"""认证 API 路由模块。

提供用户认证相关的 API 接口：
- 用户登录
- 用户登出
- 获取当前用户信息
- 修改密码
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import CurrentUser, get_session
from src.core.auth import (
    create_access_token,
    get_token_expire_seconds,
    hash_password,
    verify_password,
)
from src.models.user import User
from src.schemas.common import APIResponse
from src.schemas.user import (
    PasswordChange,
    TokenResponse,
    UserLogin,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["认证管理"])


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    summary="用户登录",
    description="使用用户名和密码登录，返回 JWT Token",
)
async def login(
    data: UserLogin,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[TokenResponse]:
    """用户登录接口。

    验证用户名和密码，返回 JWT Token。

    Args:
        data: 登录请求数据
        session: 数据库会话

    Returns:
        APIResponse[TokenResponse]: 包含 Token 和用户信息的响应

    Raises:
        HTTPException: 用户名或密码错误
    """
    logger.info(f"用户登录请求: username={data.username}")

    result = await session.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning(f"登录失败: 用户不存在 username={data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not user.is_active:
        logger.warning(f"登录失败: 用户已禁用 username={data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用",
        )

    if not verify_password(data.password, user.password_hash):
        logger.warning(f"登录失败: 密码错误 username={data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
    )

    user.update_last_login()
    await session.commit()

    logger.success(f"用户登录成功: username={data.username}")

    return APIResponse(
        success=True,
        message="登录成功",
        data=TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=get_token_expire_seconds(),
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                nickname=user.nickname,
                role=user.role.value,
                is_active=user.is_active,
                is_first_login=user.is_first_login,
                last_login=user.last_login,
                created_at=user.created_at,
            ),
            is_first_login=user.is_first_login,
        ),
    )


@router.post(
    "/logout",
    response_model=APIResponse[None],
    summary="用户登出",
    description="将当前 Token 加入黑名单，使其失效",
)
async def logout(
    user: CurrentUser,
) -> APIResponse[None]:
    """用户登出接口。

    将当前 Token 加入黑名单，使其失效。

    Args:
        user: 当前用户
        token: 当前 Token（从请求头提取）

    Returns:
        APIResponse[None]: 登出成功响应
    """
    logger.info(f"用户登出: username={user.username}")

    return APIResponse(
        success=True,
        message="登出成功",
        data=None,
    )


@router.get(
    "/me",
    response_model=APIResponse[UserResponse],
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息",
)
async def get_me(
    user: CurrentUser,
) -> APIResponse[UserResponse]:
    """获取当前用户信息接口。

    返回当前登录用户的详细信息。

    Args:
        user: 当前用户

    Returns:
        APIResponse[UserResponse]: 用户信息响应
    """
    return APIResponse(
        success=True,
        message="获取成功",
        data=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            role=user.role.value,
            is_active=user.is_active,
            is_first_login=user.is_first_login,
            last_login=user.last_login,
            created_at=user.created_at,
        ),
    )


@router.put(
    "/password",
    response_model=APIResponse[UserResponse],
    summary="修改密码",
    description="修改当前用户密码，首次登录后强制修改",
)
async def change_password(
    data: PasswordChange,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[UserResponse]:
    """修改密码接口。

    验证旧密码并设置新密码。

    Args:
        data: 修改密码请求数据
        user: 当前用户
        session: 数据库会话

    Returns:
        APIResponse[UserResponse]: 用户信息响应

    Raises:
        HTTPException: 旧密码错误
    """
    logger.info(f"修改密码: username={user.username}")

    if not verify_password(data.old_password, user.password_hash):
        logger.warning(f"修改密码失败: 旧密码错误 username={user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误",
        )

    user.password_hash = hash_password(data.new_password)
    user.mark_password_changed()
    await session.commit()

    logger.success(f"修改密码成功: username={user.username}")

    return APIResponse(
        success=True,
        message="密码修改成功",
        data=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            role=user.role.value,
            is_active=user.is_active,
            is_first_login=user.is_first_login,
            last_login=user.last_login,
            created_at=user.created_at,
        ),
    )
