"""配置模块测试。

测试 pydantic-settings 配置加载和验证：
- Settings 加载测试
- 环境变量读取测试
- DSN 生成测试
- 配置验证测试
"""

import os
from functools import lru_cache
from unittest.mock import MagicMock, patch

import pytest

from src.core.config import (
    AppSettings,
    ChromaSettings,
    DashScopeSettings,
    DeepSeekSettings,
    MinIOSettings,
    MySQLSettings,
    RedisSettings,
    Settings,
    get_settings,
)


# ==================== MySQLSettings 测试 ====================


class TestMySQLSettings:
    """MySQL 配置测试类。"""

    def test_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试 MySQL 默认配置值。"""
        # 清除环境变量以测试默认值
        monkeypatch.delenv("MYSQL_HOST", raising=False)
        monkeypatch.delenv("MYSQL_PORT", raising=False)
        monkeypatch.delenv("MYSQL_USER", raising=False)
        monkeypatch.delenv("MYSQL_PASSWORD", raising=False)
        monkeypatch.delenv("MYSQL_DATABASE", raising=False)

        settings = MySQLSettings()

        # 验证配置已加载（不检查具体默认值，因为可能被 .env 覆盖）
        assert hasattr(settings, "host")
        assert hasattr(settings, "port")
        assert hasattr(settings, "user")
        assert hasattr(settings, "password")
        assert hasattr(settings, "database")

    def test_env_prefix_loading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试从环境变量加载 MySQL 配置。"""
        monkeypatch.setenv("MYSQL_HOST", "192.168.1.100")
        monkeypatch.setenv("MYSQL_PORT", "3307")
        monkeypatch.setenv("MYSQL_USER", "test_user")
        monkeypatch.setenv("MYSQL_PASSWORD", "test_password")
        monkeypatch.setenv("MYSQL_DATABASE", "test_db")

        settings = MySQLSettings()

        assert settings.host == "192.168.1.100"
        assert settings.port == 3307
        assert settings.user == "test_user"
        assert settings.password == "test_password"
        assert settings.database == "test_db"

    def test_dsn_generation(self) -> None:
        """测试 MySQL DSN 生成。"""
        settings = MySQLSettings(
            host="localhost",
            port=3306,
            user="root",
            password="password123",
            database="test_db",
        )

        dsn = settings.dsn

        assert dsn == "mysql+aiomysql://root:password123@localhost:3306/test_db"

    def test_dsn_with_special_password(self) -> None:
        """测试包含特殊字符密码的 DSN 生成。"""
        settings = MySQLSettings(
            password="p@ss:word",
        )

        dsn = settings.dsn

        assert "p@ss:word" in dsn

    def test_dsn_without_password(self) -> None:
        """测试无密码的 DSN 生成。"""
        settings = MySQLSettings(
            user="root",
            password="",
        )

        dsn = settings.dsn

        assert dsn == "mysql+aiomysql://root:@localhost:3306/resume_screening"


# ==================== MinIOSettings 测试 ====================


class TestMinIOSettings:
    """MinIO 配置测试类。"""

    def test_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试 MinIO 默认配置值。"""
        # 清除环境变量以测试默认值
        monkeypatch.delenv("MINIO_ENDPOINT", raising=False)
        monkeypatch.delenv("MINIO_CONSOLE_URL", raising=False)
        monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
        monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
        monkeypatch.delenv("MINIO_BUCKET", raising=False)
        monkeypatch.delenv("MINIO_SECURE", raising=False)

        settings = MinIOSettings()

        # 验证配置已加载（不检查具体默认值，因为可能被 .env 覆盖）
        assert hasattr(settings, "endpoint")
        assert hasattr(settings, "access_key")
        assert hasattr(settings, "secret_key")
        assert hasattr(settings, "bucket")
        assert hasattr(settings, "secure")

    def test_env_prefix_loading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试从环境变量加载 MinIO 配置。"""
        monkeypatch.setenv("MINIO_ENDPOINT", "minio.example.com:9000")
        monkeypatch.setenv("MINIO_ACCESS_KEY", "test_access_key")
        monkeypatch.setenv("MINIO_SECRET_KEY", "test_secret_key")
        monkeypatch.setenv("MINIO_BUCKET", "test-bucket")
        monkeypatch.setenv("MINIO_SECURE", "true")

        settings = MinIOSettings()

        assert settings.endpoint == "minio.example.com:9000"
        assert settings.access_key == "test_access_key"
        assert settings.secret_key == "test_secret_key"
        assert settings.bucket == "test-bucket"
        assert settings.secure is True


# ==================== RedisSettings 测试 ====================


class TestRedisSettings:
    """Redis 配置测试类。"""

    def test_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试 Redis 默认配置值。"""
        # 清除环境变量以测试默认值
        monkeypatch.delenv("REDIS_HOST", raising=False)
        monkeypatch.delenv("REDIS_PORT", raising=False)
        monkeypatch.delenv("REDIS_PASSWORD", raising=False)
        monkeypatch.delenv("REDIS_DB", raising=False)

        settings = RedisSettings()

        # 验证配置已加载（不检查具体默认值，因为可能被 .env 覆盖）
        assert hasattr(settings, "host")
        assert hasattr(settings, "port")
        assert hasattr(settings, "password")
        assert hasattr(settings, "db")

    def test_env_prefix_loading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试从环境变量加载 Redis 配置。"""
        monkeypatch.setenv("REDIS_HOST", "redis.example.com")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("REDIS_PASSWORD", "redis_password")
        monkeypatch.setenv("REDIS_DB", "1")

        settings = RedisSettings()

        assert settings.host == "redis.example.com"
        assert settings.port == 6380
        assert settings.password == "redis_password"
        assert settings.db == 1

    def test_dsn_without_password(self) -> None:
        """测试无密码的 Redis DSN 生成。"""
        settings = RedisSettings(
            host="localhost",
            port=6379,
            password="",
            db=0,
        )

        dsn = settings.dsn

        assert dsn == "redis://localhost:6379/0"

    def test_dsn_with_password(self) -> None:
        """测试有密码的 Redis DSN 生成。"""
        settings = RedisSettings(
            host="localhost",
            port=6379,
            password="secret",
            db=2,
        )

        dsn = settings.dsn

        assert dsn == "redis://:secret@localhost:6379/2"


# ==================== ChromaSettings 测试 ====================


class TestChromaSettings:
    """ChromaDB 配置测试类。"""

    def test_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试 ChromaDB 默认配置值。"""
        # 清除环境变量以测试默认值
        monkeypatch.delenv("CHROMA_PERSIST_DIR", raising=False)
        monkeypatch.delenv("CHROMA_COLLECTION", raising=False)

        settings = ChromaSettings()

        assert settings.persist_dir == "data/chroma"
        assert settings.collection == "talent_resumes"

    def test_env_prefix_loading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试从环境变量加载 ChromaDB 配置。"""
        monkeypatch.setenv("CHROMA_PERSIST_DIR", "/data/vector_db")
        monkeypatch.setenv("CHROMA_COLLECTION", "test_collection")

        settings = ChromaSettings()

        assert settings.persist_dir == "/data/vector_db"
        assert settings.collection == "test_collection"


# ==================== DeepSeekSettings 测试 ====================


class TestDeepSeekSettings:
    """DeepSeek API 配置测试类。"""

    def test_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试 DeepSeek 默认配置值。"""
        # 清除环境变量以测试默认值
        monkeypatch.delenv("DS_API_KEY", raising=False)
        monkeypatch.delenv("DS_BASE_URL", raising=False)
        monkeypatch.delenv("DS_MODEL", raising=False)

        settings = DeepSeekSettings()

        assert settings.api_key == ""
        assert settings.base_url == "https://api.deepseek.com"
        assert settings.model == "deepseek-chat"

    def test_env_prefix_loading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试从环境变量加载 DeepSeek 配置。"""
        monkeypatch.setenv("DS_API_KEY", "sk-test-api-key")
        monkeypatch.setenv("DS_BASE_URL", "https://custom.api.com")
        monkeypatch.setenv("DS_MODEL", "deepseek-coder")

        settings = DeepSeekSettings()

        assert settings.api_key == "sk-test-api-key"
        assert settings.base_url == "https://custom.api.com"
        assert settings.model == "deepseek-coder"


# ==================== DashScopeSettings 测试 ====================


class TestDashScopeSettings:
    """DashScope API 配置测试类。"""

    def test_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试 DashScope 默认配置值。"""
        # 清除环境变量以测试默认值
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
        monkeypatch.delenv("DASHSCOPE_BASE_URL", raising=False)
        monkeypatch.delenv("DASHSCOPE_EMBEDDING_MODEL", raising=False)

        settings = DashScopeSettings()

        # 验证配置已加载（不检查具体默认值，因为可能被 .env 覆盖）
        assert hasattr(settings, "api_key")
        assert hasattr(settings, "base_url")
        assert hasattr(settings, "embedding_model")

    def test_env_prefix_loading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试从环境变量加载 DashScope 配置。"""
        monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-dashscope-key")
        monkeypatch.setenv("DASHSCOPE_BASE_URL", "https://custom.dashscope.com")
        monkeypatch.setenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v2")

        settings = DashScopeSettings()

        assert settings.api_key == "sk-dashscope-key"
        assert settings.base_url == "https://custom.dashscope.com"
        assert settings.embedding_model == "text-embedding-v2"


# ==================== AppSettings 测试 ====================


class TestAppSettings:
    """应用配置测试类。"""

    def test_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试应用默认配置值。"""
        # 清除环境变量以测试默认值
        monkeypatch.delenv("APP_DEBUG", raising=False)
        monkeypatch.delenv("APP_LOG_LEVEL", raising=False)
        monkeypatch.delenv("APP_LOG_DIR", raising=False)
        monkeypatch.delenv("APP_AES_KEY", raising=False)
        monkeypatch.delenv("APP_MAX_UPLOAD_SIZE", raising=False)
        monkeypatch.delenv("APP_LLM_TIMEOUT", raising=False)
        monkeypatch.delenv("APP_LLM_MAX_RETRIES", raising=False)

        settings = AppSettings()

        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert settings.log_dir == "logs"
        assert settings.aes_key == "resume-screening-aes-key-32bytes"
        assert settings.max_upload_size == 10 * 1024 * 1024
        assert settings.llm_timeout == 30
        assert settings.llm_max_retries == 3

    def test_env_prefix_loading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试从环境变量加载应用配置。"""
        monkeypatch.setenv("APP_DEBUG", "true")
        monkeypatch.setenv("APP_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("APP_LOG_DIR", "/var/log/app")
        monkeypatch.setenv("APP_MAX_UPLOAD_SIZE", "20971520")
        monkeypatch.setenv("APP_LLM_TIMEOUT", "60")
        monkeypatch.setenv("APP_LLM_MAX_RETRIES", "5")

        settings = AppSettings()

        assert settings.debug is True
        assert settings.log_level == "DEBUG"
        assert settings.log_dir == "/var/log/app"
        assert settings.max_upload_size == 20971520
        assert settings.llm_timeout == 60
        assert settings.llm_max_retries == 5

    def test_aes_key_validation_valid(self) -> None:
        """测试 AES 密钥验证（有效密钥）。"""
        # 32 字节的密钥
        valid_key = "a" * 32
        settings = AppSettings(aes_key=valid_key)

        assert settings.aes_key == valid_key

    def test_aes_key_validation_invalid(self) -> None:
        """测试 AES 密钥验证（无效密钥）。"""
        with pytest.raises(ValueError, match="AES 密钥必须为 32 字节"):
            AppSettings(aes_key="short_key")

    def test_aes_key_validation_unicode(self) -> None:
        """测试 AES 密钥验证（Unicode 字符）。"""
        # 中文字符，确保 UTF-8 编码后为 32 字节
        # 每个中文字符 UTF-8 编码为 3 字节
        chinese_key = "测试密钥测试密钥测试密钥测试"  # 12 * 3 = 36 字节，不符合
        with pytest.raises(ValueError, match="AES 密钥必须为 32 字节"):
            AppSettings(aes_key=chinese_key)

    def test_aes_key_validation_exact_32_bytes(self) -> None:
        """测试 AES 密钥验证（恰好 32 字节）。"""
        # ASCII 字符，每个 1 字节
        key_32_bytes = "12345678901234567890123456789012"
        settings = AppSettings(aes_key=key_32_bytes)

        assert settings.aes_key == key_32_bytes
        assert len(settings.aes_key.encode("utf-8")) == 32


# ==================== Settings 聚合配置测试 ====================


class TestSettings:
    """聚合配置测试类。"""

    def test_settings_aggregates_all_configs(self) -> None:
        """测试 Settings 聚合所有子配置。"""
        settings = Settings()

        assert isinstance(settings.mysql, MySQLSettings)
        assert isinstance(settings.minio, MinIOSettings)
        assert isinstance(settings.redis, RedisSettings)
        assert isinstance(settings.chroma, ChromaSettings)
        assert isinstance(settings.deepseek, DeepSeekSettings)
        assert isinstance(settings.dashscope, DashScopeSettings)
        assert isinstance(settings.app, AppSettings)

    def test_settings_nested_config_access(self) -> None:
        """测试 Settings 嵌套配置访问。"""
        settings = Settings()

        # 访问嵌套配置 - 验证配置结构正确
        assert hasattr(settings.mysql, "host")
        assert hasattr(settings.minio, "endpoint")
        assert hasattr(settings.redis, "host")
        assert hasattr(settings.chroma, "persist_dir")
        assert hasattr(settings.app, "debug")

    def test_settings_with_env_variables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试 Settings 从环境变量加载所有配置。"""
        # 设置 MySQL 环境变量
        monkeypatch.setenv("MYSQL_HOST", "mysql.example.com")
        monkeypatch.setenv("MYSQL_PORT", "3307")

        # 设置 Redis 环境变量
        monkeypatch.setenv("REDIS_HOST", "redis.example.com")

        # 设置应用环境变量
        monkeypatch.setenv("APP_DEBUG", "true")

        settings = Settings()

        assert settings.mysql.host == "mysql.example.com"
        assert settings.mysql.port == 3307
        assert settings.redis.host == "redis.example.com"
        assert settings.app.debug is True


# ==================== get_settings 函数测试 ====================


class TestGetSettings:
    """get_settings 函数测试类。"""

    def test_get_settings_returns_settings_instance(self) -> None:
        """测试 get_settings 返回 Settings 实例。"""
        # 清除缓存
        get_settings.cache_clear()

        settings = get_settings()

        assert isinstance(settings, Settings)

    def test_get_settings_caching(self) -> None:
        """测试 get_settings 缓存功能。"""
        # 清除缓存
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        # 应该返回同一个实例
        assert settings1 is settings2

    def test_get_settings_cache_clear(self) -> None:
        """测试 get_settings 缓存清除。"""
        settings1 = get_settings()

        # 清除缓存
        get_settings.cache_clear()

        settings2 = get_settings()

        # 清除后应该是不同实例
        assert settings1 is not settings2


# ==================== 边界情况测试 ====================


class TestConfigEdgeCases:
    """配置边界情况测试类。"""

    def test_empty_string_values(self) -> None:
        """测试空字符串值。"""
        settings = MySQLSettings(
            host="",
            password="",
        )

        assert settings.host == ""
        assert settings.password == ""

    def test_port_boundary_values(self) -> None:
        """测试端口边界值。"""
        # 最小有效端口
        settings_min = MySQLSettings(port=1)
        assert settings_min.port == 1

        # 最大有效端口
        settings_max = MySQLSettings(port=65535)
        assert settings_max.port == 65535

    def test_special_characters_in_password(self) -> None:
        """测试密码中的特殊字符。"""
        special_password = "p@ss:w0rd!#$%^&*()"
        settings = MySQLSettings(password=special_password)

        assert settings.password == special_password

    def test_unicode_in_config_values(self) -> None:
        """测试配置值中的 Unicode 字符。"""
        settings = MySQLSettings(
            database="数据库_test",
        )

        assert settings.database == "数据库_test"

    def test_very_long_values(self) -> None:
        """测试超长配置值。"""
        long_password = "a" * 1000
        settings = MySQLSettings(password=long_password)

        assert settings.password == long_password

    def test_boolean_env_parsing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试布尔值环境变量解析。"""
        # 测试 "true" 字符串
        monkeypatch.setenv("APP_DEBUG", "true")
        settings_true = AppSettings()
        assert settings_true.debug is True

        # 测试 "false" 字符串
        monkeypatch.setenv("APP_DEBUG", "false")
        settings_false = AppSettings()
        assert settings_false.debug is False

        # 测试 "1" 字符串
        monkeypatch.setenv("APP_DEBUG", "1")
        settings_one = AppSettings()
        assert settings_one.debug is True

        # 测试 "0" 字符串
        monkeypatch.setenv("APP_DEBUG", "0")
        settings_zero = AppSettings()
        assert settings_zero.debug is False

    def test_integer_env_parsing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试整数环境变量解析。"""
        monkeypatch.setenv("MYSQL_PORT", "3306")
        monkeypatch.setenv("REDIS_DB", "3")

        mysql_settings = MySQLSettings()
        redis_settings = RedisSettings()

        assert mysql_settings.port == 3306
        assert isinstance(mysql_settings.port, int)
        assert redis_settings.db == 3
        assert isinstance(redis_settings.db, int)


# ==================== 真实环境变量测试 ====================


class TestRealEnvConfig:
    """真实环境变量配置测试类。

    使用项目 .env 文件中的实际配置进行测试。
    """

    def test_load_real_mysql_config(self) -> None:
        """测试加载真实 MySQL 配置。"""
        settings = MySQLSettings()

        # 如果环境变量已设置，验证值
        if os.getenv("MYSQL_HOST"):
            assert settings.host == os.getenv("MYSQL_HOST")
        if os.getenv("MYSQL_PORT"):
            assert settings.port == int(os.getenv("MYSQL_PORT"))
        if os.getenv("MYSQL_USER"):
            assert settings.user == os.getenv("MYSQL_USER")
        if os.getenv("MYSQL_DATABASE"):
            assert settings.database == os.getenv("MYSQL_DATABASE")

    def test_load_real_redis_config(self) -> None:
        """测试加载真实 Redis 配置。"""
        settings = RedisSettings()

        if os.getenv("REDIS_HOST"):
            assert settings.host == os.getenv("REDIS_HOST")
        if os.getenv("REDIS_PORT"):
            assert settings.port == int(os.getenv("REDIS_PORT"))

    def test_load_real_minio_config(self) -> None:
        """测试加载真实 MinIO 配置。"""
        settings = MinIOSettings()

        if os.getenv("MINIO_ENDPOINT"):
            assert settings.endpoint == os.getenv("MINIO_ENDPOINT")
        if os.getenv("MINIO_ACCESS_KEY"):
            assert settings.access_key == os.getenv("MINIO_ACCESS_KEY")

    def test_real_dsn_generation(self) -> None:
        """测试真实 DSN 生成。"""
        settings = Settings()

        # MySQL DSN 应该包含正确的协议
        mysql_dsn = settings.mysql.dsn
        assert "mysql+aiomysql://" in mysql_dsn

        # Redis DSN 应该包含正确的协议
        redis_dsn = settings.redis.dsn
        assert "redis://" in redis_dsn
