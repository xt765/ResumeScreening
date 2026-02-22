"""用户管理 API 路由模块。

提供管理员用户管理相关的 API 接口：
- 创建用户
- 获取用户列表
- 更新用户信息
- 禁用/删除用户
- 重置用户密码
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session, require_role
from src.core.auth import hash_password
from src.models.user import RoleEnum, User
from src.schemas.common import APIResponse, PaginatedResponse
from src.schemas.user import (
    PasswordReset,
    UserCreate,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.post(
    "",
    response_model=APIResponse[UserResponse],
    summary="创建用户",
    description="管理员创建新用户账号",
)
async def create_user(
    data: UserCreate,
    admin: User = Depends(require_role(RoleEnum.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[UserResponse]:
    """创建用户接口。

    管理员创建新用户账号。

    Args:
        data: 创建用户请求数据
        admin: 当前管理员用户
        session: 数据库会话

    Returns:
        APIResponse[UserResponse]: 创建的用户信息

    Raises:
        HTTPException: 用户名或邮箱已存在
    """
    logger.info(f"创建用户: username={data.username}, role={data.role.value}")

    existing = await session.execute(
        select(User).where((User.username == data.username) | (User.email == data.email))
    )
    if existing.scalar_one_or_none():
        logger.warning(f"创建用户失败: 用户名或邮箱已存在 username={data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已存在",
        )

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        nickname=data.nickname,
        role=data.role,
        is_first_login=True,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    logger.success(f"创建用户成功: username={data.username}")

    return APIResponse(
        success=True,
        message="用户创建成功",
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


@router.get(
    "",
    response_model=APIResponse[PaginatedResponse[UserResponse]],
    summary="获取用户列表",
    description="管理员获取用户列表，支持分页和筛选",
)
async def get_users(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    role: RoleEnum | None = Query(default=None, description="角色筛选"),
    is_active: bool | None = Query(default=None, description="状态筛选"),
    keyword: str | None = Query(default=None, description="关键词搜索"),
    admin: User = Depends(require_role(RoleEnum.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[PaginatedResponse[UserResponse]]:
    """获取用户列表接口。

    管理员获取用户列表，支持分页和筛选。

    Args:
        page: 页码
        page_size: 每页数量
        role: 角色筛选
        is_active: 状态筛选
        keyword: 关键词搜索
        admin: 当前管理员用户
        session: 数据库会话

    Returns:
        APIResponse[PaginatedResponse[UserResponse]]: 用户列表
    """
    logger.debug(f"获取用户列表: page={page}, page_size={page_size}")

    query = select(User)

    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if keyword:
        query = query.where(
            (User.username.contains(keyword))
            | (User.email.contains(keyword))
            | (User.nickname.contains(keyword))
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    users = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return APIResponse(
        success=True,
        message="获取成功",
        data=PaginatedResponse(
            items=[
                UserResponse(
                    id=u.id,
                    username=u.username,
                    email=u.email,
                    nickname=u.nickname,
                    role=u.role.value,
                    is_active=u.is_active,
                    is_first_login=u.is_first_login,
                    last_login=u.last_login,
                    created_at=u.created_at,
                )
                for u in users
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.put(
    "/{user_id}",
    response_model=APIResponse[UserResponse],
    summary="更新用户信息",
    description="管理员更新用户信息",
)
async def update_user(
    user_id: str,
    data: UserUpdate,
    admin: User = Depends(require_role(RoleEnum.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[UserResponse]:
    """更新用户信息接口。

    管理员更新用户信息。

    Args:
        user_id: 用户 ID
        data: 更新用户请求数据
        admin: 当前管理员用户
        session: 数据库会话

    Returns:
        APIResponse[UserResponse]: 更新后的用户信息

    Raises:
        HTTPException: 用户不存在
    """
    logger.info(f"更新用户: user_id={user_id}")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    if data.nickname is not None:
        user.nickname = data.nickname
    if data.email is not None:
        existing = await session.execute(
            select(User).where(User.email == data.email, User.id != user_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用",
            )
        user.email = data.email
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.role is not None:
        user.role = data.role

    await session.commit()
    await session.refresh(user)

    logger.success(f"更新用户成功: user_id={user_id}")

    return APIResponse(
        success=True,
        message="更新成功",
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


@router.delete(
    "/{user_id}",
    response_model=APIResponse[None],
    summary="禁用用户",
    description="管理员禁用用户账号",
)
async def delete_user(
    user_id: str,
    admin: User = Depends(require_role(RoleEnum.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[None]:
    """禁用用户接口。

    管理员禁用用户账号（设置 is_active 为 False）。

    Args:
        user_id: 用户 ID
        admin: 当前管理员用户
        session: 数据库会话

    Returns:
        APIResponse[None]: 操作结果

    Raises:
        HTTPException: 用户不存在或不能禁用自己
    """
    logger.info(f"禁用用户: user_id={user_id}")

    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己的账号",
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    user.is_active = False
    await session.commit()

    logger.success(f"禁用用户成功: user_id={user_id}")

    return APIResponse(
        success=True,
        message="用户已禁用",
        data=None,
    )


@router.post(
    "/{user_id}/reset-password",
    response_model=APIResponse[None],
    summary="重置用户密码",
    description="管理员重置用户密码",
)
async def reset_password(
    user_id: str,
    data: PasswordReset,
    admin: User = Depends(require_role(RoleEnum.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[None]:
    """重置用户密码接口。

    管理员重置用户密码。

    Args:
        user_id: 用户 ID
        data: 重置密码请求数据
        admin: 当前管理员用户
        session: 数据库会话

    Returns:
        APIResponse[None]: 操作结果

    Raises:
        HTTPException: 用户不存在
    """
    logger.info(f"重置用户密码: user_id={user_id}")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    user.password_hash = hash_password(data.new_password)
    user.is_first_login = True
    await session.commit()

    logger.success(f"重置用户密码成功: user_id={user_id}")

    return APIResponse(
        success=True,
        message="密码已重置",
        data=None,
    )
