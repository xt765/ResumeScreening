"""核心模块。

提供配置管理、日志系统、异常处理和加密工具。

Modules:
    config: 配置管理（pydantic-settings）
    logger: 日志系统（loguru）
    exceptions: 业务异常类
    security: AES 加密工具
"""

from src.core.config import (
    AppSettings,
    DashScopeSettings,
    DeepSeekSettings,
    MinIOSettings,
    MySQLSettings,
    RedisSettings,
    Settings,
    get_settings,
)
from src.core.exceptions import (
    BaseAppException,
    CacheException,
    DatabaseException,
    LLMException,
    ParseException,
    StorageException,
    ValidationException,
    WorkflowException,
)
from src.core.logger import get_logger, setup_logger
from src.core.security import (
    decrypt_data,
    decrypt_dict,
    encrypt_data,
    encrypt_dict,
    mask_email,
    mask_phone,
)

__all__ = [
    "AppSettings",
    # 异常
    "BaseAppException",
    "CacheException",
    "DashScopeSettings",
    "DatabaseException",
    "DeepSeekSettings",
    "LLMException",
    "MinIOSettings",
    "MySQLSettings",
    "ParseException",
    "RedisSettings",
    # 配置
    "Settings",
    "StorageException",
    "ValidationException",
    "WorkflowException",
    "decrypt_data",
    "decrypt_dict",
    # 加密
    "encrypt_data",
    "encrypt_dict",
    # 日志
    "get_logger",
    "get_settings",
    "mask_email",
    "mask_phone",
    "setup_logger",
]
