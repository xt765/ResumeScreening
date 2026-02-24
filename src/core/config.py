"""核心配置模块。

使用 pydantic-settings 管理所有环境变量配置，支持：
- MySQL 数据库配置
- MinIO 对象存储配置
- Redis 缓存配置
- LLM API 配置（DeepSeek、DashScope）
- 应用运行配置
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class MySQLSettings(BaseSettings):
    """MySQL 数据库配置。

    Attributes:
        host: 数据库主机地址
        port: 数据库端口
        user: 数据库用户名
        password: 数据库密码
        database: 数据库名称
    """

    model_config = SettingsConfigDict(
        env_prefix="MYSQL_",
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="localhost", description="MySQL 主机地址")
    port: int = Field(default=3306, description="MySQL 端口")
    user: str = Field(default="root", description="MySQL 用户名")
    password: str = Field(default="", description="MySQL 密码")
    database: str = Field(default="resume_screening", description="数据库名称")
    use_sqlite: bool = Field(default=False, description="是否使用 SQLite（仅用于开发/测试）")

    @property
    def dsn(self) -> str:
        """生成 MySQL 连接字符串。

        Returns:
            MySQL 连接 DSN
        """
        if self.use_sqlite:
            print("Config: Using SQLite DSN")
            return "sqlite+aiosqlite:///./test.db"
            
        print(f"Config: Using MySQL DSN (host={self.host})")
        return (
            f"mysql+aiomysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        )


class MinIOSettings(BaseSettings):
    """MinIO 对象存储配置。

    Attributes:
        endpoint: MinIO 服务端点
        console_url: MinIO 控制台 URL
        access_key: 访问密钥
        secret_key: 密钥
        bucket: 存储桶名称
        secure: 是否使用 HTTPS
    """

    model_config = SettingsConfigDict(
        env_prefix="MINIO_",
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    endpoint: str = Field(default="localhost:9000", description="MinIO 端点")
    console_url: str = Field(default="http://localhost:9001", description="控制台 URL")
    access_key: str = Field(default="minioadmin", description="访问密钥")
    secret_key: str = Field(default="minioadmin", description="密钥")
    bucket: str = Field(default="resume-images", description="存储桶名称")
    secure: bool = Field(default=False, description="是否使用 HTTPS")


class RedisSettings(BaseSettings):
    """Redis 缓存配置。

    Attributes:
        host: Redis 主机地址
        port: Redis 端口
        password: Redis 密码
        db: Redis 数据库索引
    """

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="localhost", description="Redis 主机地址")
    port: int = Field(default=6379, description="Redis 端口")
    password: str = Field(default="", description="Redis 密码")
    db: int = Field(default=0, description="Redis 数据库索引")

    @property
    def dsn(self) -> str:
        """生成 Redis 连接字符串。

        Returns:
            Redis 连接 DSN
        """
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class ChromaSettings(BaseSettings):
    """ChromaDB 向量数据库配置。

    Attributes:
        persist_dir: 持久化存储目录
        collection: 默认集合名称
    """

    model_config = SettingsConfigDict(
        env_prefix="CHROMA_",
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    persist_dir: str = Field(default="data/chroma", description="ChromaDB 持久化目录")
    collection: str = Field(default="talent_resumes", description="默认集合名称")


class DeepSeekSettings(BaseSettings):
    """DeepSeek LLM API 配置。

    Attributes:
        api_key: API 密钥
        base_url: API 基础 URL
        model: 使用的模型名称
    """

    model_config = SettingsConfigDict(
        env_prefix="DS_",
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = Field(default="", description="DeepSeek API 密钥")
    base_url: str = Field(default="https://api.deepseek.com", description="API 基础 URL")
    model: str = Field(default="deepseek-chat", description="模型名称")


class DashScopeSettings(BaseSettings):
    """DashScope API 配置（用于 Embedding 服务）。

    Attributes:
        api_key: API 密钥
        base_url: API 基础 URL
        embedding_model: Embedding 模型名称
    """

    model_config = SettingsConfigDict(
        env_prefix="DASHSCOPE_",
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = Field(default="", description="DashScope API 密钥")
    base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="API 基础 URL",
    )
    embedding_model: str = Field(default="text-embedding-v3", description="Embedding 模型名称")


class AppSettings(BaseSettings):
    """应用运行配置。

    Attributes:
        debug: 调试模式
        log_level: 日志级别
        log_dir: 日志目录
        aes_key: AES 加密密钥（32字节）
        max_upload_size: 最大上传文件大小（字节）
        llm_timeout: LLM 调用超时时间（秒）
        llm_max_retries: LLM 调用最大重试次数
    """

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")
    log_dir: str = Field(default="logs", description="日志目录")
    aes_key: str = Field(
        default="resume-screening-aes-key-32bytes",
        description="AES 加密密钥",
    )
    max_upload_size: int = Field(default=10 * 1024 * 1024, description="最大上传文件大小（10MB）")
    llm_timeout: int = Field(default=30, description="LLM 调用超时时间（秒）")
    llm_max_retries: int = Field(default=3, description="LLM 调用最大重试次数")

    @field_validator("aes_key")
    @classmethod
    def validate_aes_key(cls, v: str) -> str:
        """验证 AES 密钥长度必须为 32 字节。

        Args:
            v: AES 密钥值

        Returns:
            验证后的 AES 密钥

        Raises:
            ValueError: 密钥长度不为 32 字节
        """
        if len(v.encode("utf-8")) != 32:
            raise ValueError("AES 密钥必须为 32 字节")
        return v


class JWTSettings(BaseSettings):
    """JWT 认证配置。

    Attributes:
        secret_key: JWT 密钥
        algorithm: JWT 算法
        access_token_expire_minutes: 访问令牌过期时间（分钟）
    """

    model_config = SettingsConfigDict(
        env_prefix="JWT_",
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    secret_key: str = Field(
        default="resume-screening-jwt-secret-key-32bytes!",
        description="JWT 密钥",
    )
    algorithm: str = Field(default="HS256", description="JWT 算法")
    access_token_expire_minutes: int = Field(
        default=1440,
        description="访问令牌过期时间（分钟），默认 24 小时",
    )


class Settings(BaseSettings):
    """应用总配置类。

    聚合所有子配置，提供统一的配置访问入口。

    Attributes:
        mysql: MySQL 数据库配置
        minio: MinIO 对象存储配置
        redis: Redis 缓存配置
        chroma: ChromaDB 向量数据库配置
        deepseek: DeepSeek LLM 配置
        dashscope: DashScope Embedding 配置
        app: 应用运行配置
        jwt: JWT 认证配置
    """

    mysql: MySQLSettings = Field(default_factory=MySQLSettings)
    minio: MinIOSettings = Field(default_factory=MinIOSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    chroma: ChromaSettings = Field(default_factory=ChromaSettings)
    deepseek: DeepSeekSettings = Field(default_factory=DeepSeekSettings)
    dashscope: DashScopeSettings = Field(default_factory=DashScopeSettings)
    app: AppSettings = Field(default_factory=AppSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)


@lru_cache
def get_settings() -> Settings:
    """获取配置实例（带缓存）。

    使用 lru_cache 确保配置只加载一次，提高性能。

    Returns:
        Settings 配置实例
    """
    return Settings()
