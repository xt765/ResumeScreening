"""用户相关 Schema 模块。

提供用户认证和管理的请求/响应模型。

Classes:
    UserCreate: 管理员创建用户请求
    UserLogin: 登录请求
    UserResponse: 用户响应
    TokenResponse: Token 响应
    PasswordChange: 修改密码请求
    UserUpdate: 更新用户请求
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from src.models.user import RoleEnum


class UserCreate(BaseModel):
    """管理员创建用户请求模型。

    Attributes:
        username: 用户名
        email: 邮箱
        password: 初始密码
        nickname: 昵称
        role: 用户角色
    """

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=100, description="初始密码")
    nickname: str = Field(default="", max_length=50, description="昵称")
    role: RoleEnum = Field(default=RoleEnum.HR, description="用户角色")


class UserLogin(BaseModel):
    """登录请求模型。

    Attributes:
        username: 用户名
        password: 密码
    """

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户响应模型。

    Attributes:
        id: 用户 ID
        username: 用户名
        email: 邮箱
        nickname: 昵称
        role: 用户角色
        is_active: 是否激活
        is_first_login: 是否首次登录
        last_login: 最后登录时间
        created_at: 创建时间
    """

    id: str = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    nickname: str = Field(default="", description="昵称")
    role: str = Field(..., description="用户角色")
    is_active: bool = Field(default=True, description="是否激活")
    is_first_login: bool = Field(default=True, description="是否首次登录")
    last_login: datetime | None = Field(default=None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        """Pydantic 配置。"""

        from_attributes = True


class TokenResponse(BaseModel):
    """Token 响应模型。

    Attributes:
        access_token: 访问令牌
        token_type: 令牌类型
        expires_in: 过期时间（秒）
        user: 用户信息
        is_first_login: 是否首次登录
    """

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: UserResponse = Field(..., description="用户信息")
    is_first_login: bool = Field(..., description="是否首次登录")


class PasswordChange(BaseModel):
    """修改密码请求模型。

    Attributes:
        old_password: 旧密码
        new_password: 新密码
    """

    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="新密码",
    )


class UserUpdate(BaseModel):
    """更新用户请求模型。

    Attributes:
        nickname: 昵称
        email: 邮箱
        is_active: 是否激活
        role: 用户角色
    """

    nickname: str | None = Field(default=None, max_length=50, description="昵称")
    email: EmailStr | None = Field(default=None, description="邮箱")
    is_active: bool | None = Field(default=None, description="是否激活")
    role: RoleEnum | None = Field(default=None, description="用户角色")


class PasswordReset(BaseModel):
    """重置密码请求模型（管理员操作）。

    Attributes:
        new_password: 新密码
    """

    new_password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="新密码",
    )
