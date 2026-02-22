"""AES 加密工具模块。

提供敏感数据的加密和解密功能，用于：
- 手机号加密存储
- 邮箱加密存储
- 其他敏感信息保护
"""

import base64
import contextlib
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.core.config import get_settings


def _get_fernet_key() -> bytes:
    """从配置生成 Fernet 兼容的密钥。

    使用 PBKDF2 从原始密钥派生 32 字节密钥。

    Returns:
        Fernet 兼容的 base64 编码密钥
    """
    settings = get_settings()
    # 使用固定的盐值（生产环境应使用随机盐并存储）
    salt = b"resume_screening_salt_v1"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend(),
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.app.aes_key.encode()))
    return key


def _get_fernet() -> Fernet:
    """获取 Fernet 实例。

    Returns:
        Fernet 加密实例
    """
    key = _get_fernet_key()
    return Fernet(key)


def encrypt_data(data: str) -> str:
    """加密字符串数据。

    使用 Fernet（AES-128-CBC）对称加密算法。

    Args:
        data: 待加密的明文字符串

    Returns:
        Base64 编码的加密字符串

    Example:
        >>> encrypted = encrypt_data("13800138000")
        >>> # encrypted: "gAAAAABm..."
    """
    if not data:
        return ""

    fernet = _get_fernet()
    encrypted_bytes = fernet.encrypt(data.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_data(encrypted_data: str) -> str:
    """解密字符串数据。

    Args:
        encrypted_data: 加密的字符串（Base64 编码）

    Returns:
        解密后的明文字符串

    Raises:
        ValueError: 解密失败时抛出

    Example:
        >>> decrypted = decrypt_data("gAAAAABm...")
        >>> # decrypted: "13800138000"
    """
    if not encrypted_data:
        return ""

    try:
        fernet = _get_fernet()
        decrypted_bytes = fernet.decrypt(encrypted_data.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"解密失败: {e}") from e


def encrypt_dict(data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    """加密字典中的指定字段。

    对字典中指定的敏感字段进行加密。

    Args:
        data: 原始数据字典
        fields: 需要加密的字段列表

    Returns:
        加密后的数据字典

    Example:
        >>> data = {"name": "张三", "phone": "13800138000"}
        >>> encrypted = encrypt_dict(data, ["phone"])
        >>> # encrypted["phone"] 为加密后的值
    """
    result = data.copy()
    for field in fields:
        if result.get(field):
            result[field] = encrypt_data(str(result[field]))
    return result


def decrypt_dict(data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    """解密字典中的指定字段。

    对字典中指定的加密字段进行解密。

    Args:
        data: 加密的数据字典
        fields: 需要解密的字段列表

    Returns:
        解密后的数据字典

    Example:
        >>> data = {"name": "张三", "phone": "gAAAAABm..."}
        >>> decrypted = decrypt_dict(data, ["phone"])
        >>> # decrypted["phone"] = "13800138000"
    """
    result = data.copy()
    for field in fields:
        if result.get(field):
            with contextlib.suppress(ValueError):
                result[field] = decrypt_data(str(result[field]))
    return result


def mask_phone(phone: str) -> str:
    """脱敏手机号。

    将手机号中间 4 位替换为星号。

    Args:
        phone: 手机号

    Returns:
        脱敏后的手机号

    Example:
        >>> mask_phone("13800138000")
        '138****8000'
    """
    if not phone or len(phone) < 7:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"


def mask_email(email: str) -> str:
    """脱敏邮箱地址。

    将邮箱用户名部分中间替换为星号。

    Args:
        email: 邮箱地址

    Returns:
        脱敏后的邮箱地址

    Example:
        >>> mask_email("example@domain.com")
        'e****e@domain.com'
    """
    if not email or "@" not in email:
        return email

    username, domain = email.split("@", 1)
    if len(username) <= 2:
        return f"{username[0]}***@{domain}"

    masked_username = f"{username[0]}****{username[-1]}"
    return f"{masked_username}@{domain}"
