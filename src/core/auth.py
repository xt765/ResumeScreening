"""认证核心模块。

提供用户认证相关的核心功能：
- 密码哈希/验证 (bcrypt)
- JWT Token 生成/验证
- Token 黑名单管理 (Redis)
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt
from loguru import logger

from src.core.config import get_settings
from src.models.user import RoleEnum
from src.storage.redis_client import redis_client


def hash_password(password: str) -> str:
    """哈希密码。

    使用 bcrypt 算法对密码进行哈希处理。

    Args:
        password: 明文密码

    Returns:
        str: 哈希后的密码

    Example:
        >>> hashed = hash_password("123456")
        >>> # hashed: "$2b$12$..."
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码。

    验证明文密码是否与哈希密码匹配。

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        bool: 密码是否匹配
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(
    user_id: str,
    username: str,
    role: RoleEnum,
    expires_delta: timedelta | None = None,
) -> str:
    """创建访问令牌。

    生成 JWT 访问令牌。

    Args:
        user_id: 用户 ID
        username: 用户名
        role: 用户角色
        expires_delta: 过期时间增量，默认使用配置中的值

    Returns:
        str: JWT 访问令牌
    """
    settings = get_settings()

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.jwt.access_token_expire_minutes,
        )

    now = datetime.now(UTC)
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "username": username,
        "role": role.value,
        "exp": expire,
        "iat": now,
    }

    token = jwt.encode(
        payload,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )

    logger.debug(f"创建访问令牌: user_id={user_id}, expire={expire}")
    return token


def decode_access_token(token: str) -> dict[str, Any] | None:
    """解码访问令牌。

    解析 JWT 访问令牌，返回载荷数据。

    Args:
        token: JWT 访问令牌

    Returns:
        dict[str, Any] | None: 令牌载荷，解码失败返回 None
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning(f"令牌解码失败: {e}")
        return None


async def add_token_to_blacklist(token: str, expires_in: int) -> None:
    """将令牌添加到黑名单。

    将令牌添加到 Redis 黑名单，用于登出功能。

    Args:
        token: JWT 访问令牌
        expires_in: 过期时间（秒）
    """
    key = f"token_blacklist:{token}"
    await redis_client.set(key, "1", ex=expires_in)
    logger.debug(f"令牌已加入黑名单: {token[:20]}...")


async def is_token_blacklisted(token: str) -> bool:
    """检查令牌是否在黑名单中。

    Args:
        token: JWT 访问令牌

    Returns:
        bool: 令牌是否在黑名单中
    """
    key = f"token_blacklist:{token}"
    result = await redis_client.exists(key)
    return result > 0


def get_token_expire_seconds() -> int:
    """获取令牌过期时间（秒）。

    Returns:
        int: 过期时间（秒）
    """
    settings = get_settings()
    return settings.jwt.access_token_expire_minutes * 60


class AuthError(Exception):
    """认证错误异常。

    用于认证过程中的错误处理。

    Attributes:
        message: 错误消息
        code: 错误代码
    """

    def __init__(self, message: str, code: str = "AUTH_ERROR") -> None:
        """初始化认证错误。

        Args:
            message: 错误消息
            code: 错误代码
        """
        self.message = message
        self.code = code
        super().__init__(message)


class InvalidCredentialsError(AuthError):
    """无效凭据错误。"""

    def __init__(self) -> None:
        super().__init__("用户名或密码错误", "INVALID_CREDENTIALS")


class TokenExpiredError(AuthError):
    """令牌过期错误。"""

    def __init__(self) -> None:
        super().__init__("登录已过期，请重新登录", "TOKEN_EXPIRED")


class TokenInvalidError(AuthError):
    """无效令牌错误。"""

    def __init__(self) -> None:
        super().__init__("无效的访问令牌", "TOKEN_INVALID")


class TokenBlacklistedError(AuthError):
    """令牌已失效错误。"""

    def __init__(self) -> None:
        super().__init__("登录已失效，请重新登录", "TOKEN_BLACKLISTED")


class PermissionDeniedError(AuthError):
    """权限不足错误。"""

    def __init__(self, required_role: str = "admin") -> None:
        super().__init__(
            f"权限不足，需要 {required_role} 角色",
            "PERMISSION_DENIED",
        )


class UserNotFoundError(AuthError):
    """用户不存在错误。"""

    def __init__(self) -> None:
        super().__init__("用户不存在", "USER_NOT_FOUND")


class UserInactiveError(AuthError):
    """用户已禁用错误。"""

    def __init__(self) -> None:
        super().__init__("用户已被禁用", "USER_INACTIVE")
