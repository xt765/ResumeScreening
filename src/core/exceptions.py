"""业务异常类定义模块。

定义系统中所有业务异常类，支持：
- 统一的异常基类
- 异常代码和消息管理
- 完整的异常上下文信息
"""

from typing import Any


class BaseAppException(Exception):
    """应用基础异常类。

    所有业务异常的基类，提供统一的异常接口。

    Attributes:
        code: 异常代码
        message: 异常消息
        details: 异常详情
    """

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        """初始化异常。

        Args:
            message: 异常消息
            code: 异常代码，默认为 UNKNOWN_ERROR
            details: 异常详情字典
        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """将异常转换为字典格式。

        Returns:
            包含异常信息的字典
        """
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        """返回异常的字符串表示。

        Returns:
            异常字符串
        """
        return f"[{self.code}] {self.message}"


class StorageException(BaseAppException):
    """存储异常类。

    用于存储相关操作失败时的异常。

    Examples:
        - MinIO 文件上传失败
        - MinIO 文件下载失败
        - 存储桶不存在
    """

    def __init__(
        self,
        message: str,
        storage_type: str = "unknown",
        details: dict[str, Any] | None = None,
    ) -> None:
        """初始化存储异常。

        Args:
            message: 异常消息
            storage_type: 存储类型（minio, mysql, redis, chromadb）
            details: 异常详情
        """
        super().__init__(
            message=message,
            code="STORAGE_ERROR",
            details={"storage_type": storage_type, **(details or {})},
        )


class LLMException(BaseAppException):
    """LLM 调用异常类。

    用于 LLM API 调用失败时的异常。

    Examples:
        - API 密钥无效
        - 超时
        - 响应解析失败
        - 模型不可用
    """

    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        model: str = "unknown",
        details: dict[str, Any] | None = None,
    ) -> None:
        """初始化 LLM 异常。

        Args:
            message: 异常消息
            provider: LLM 提供商（deepseek, dashscope）
            model: 模型名称
            details: 异常详情
        """
        super().__init__(
            message=message,
            code="LLM_ERROR",
            details={
                "provider": provider,
                "model": model,
                **(details or {}),
            },
        )


class ParseException(BaseAppException):
    """解析异常类。

    用于文档解析失败时的异常。

    Examples:
        - PDF 解析失败
        - Word 解析失败
        - 文件格式不支持
        - 文件损坏
    """

    def __init__(
        self,
        message: str,
        file_type: str = "unknown",
        file_name: str = "unknown",
        details: dict[str, Any] | None = None,
    ) -> None:
        """初始化解析异常。

        Args:
            message: 异常消息
            file_type: 文件类型（pdf, docx）
            file_name: 文件名
            details: 异常详情
        """
        super().__init__(
            message=message,
            code="PARSE_ERROR",
            details={
                "file_type": file_type,
                "file_name": file_name,
                **(details or {}),
            },
        )


class ValidationException(BaseAppException):
    """验证异常类。

    用于数据验证失败时的异常。

    Examples:
        - 参数验证失败
        - 文件大小超限
        - 文件类型不支持
        - 必填字段缺失
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """初始化验证异常。

        Args:
            message: 异常消息
            field: 验证失败的字段名
            value: 验证失败的值
            details: 异常详情
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = str(value)

        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=error_details,
        )


class WorkflowException(BaseAppException):
    """工作流异常类。

    用于 LangGraph 工作流执行失败时的异常。

    Examples:
        - 节点执行失败
        - 状态转换失败
        - 工作流超时
        - 依赖服务不可用
    """

    def __init__(
        self,
        message: str,
        node: str = "unknown",
        state: str = "unknown",
        details: dict[str, Any] | None = None,
    ) -> None:
        """初始化工作流异常。

        Args:
            message: 异常消息
            node: 失败的节点名称
            state: 当前工作流状态
            details: 异常详情
        """
        super().__init__(
            message=message,
            code="WORKFLOW_ERROR",
            details={
                "node": node,
                "state": state,
                **(details or {}),
            },
        )


class DatabaseException(BaseAppException):
    """数据库异常类。

    用于数据库操作失败时的异常。

    Examples:
        - 连接失败
        - 查询超时
        - 唯一约束冲突
        - 外键约束失败
    """

    def __init__(
        self,
        message: str,
        operation: str = "unknown",
        table: str = "unknown",
        details: dict[str, Any] | None = None,
    ) -> None:
        """初始化数据库异常。

        Args:
            message: 异常消息
            operation: 操作类型（insert, update, delete, select）
            table: 相关表名
            details: 异常详情
        """
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details={
                "operation": operation,
                "table": table,
                **(details or {}),
            },
        )


class CacheException(BaseAppException):
    """缓存异常类。

    用于 Redis 缓存操作失败时的异常。

    Examples:
        - 连接失败
        - 序列化失败
        - 缓存过期
    """

    def __init__(
        self,
        message: str,
        operation: str = "unknown",
        key: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """初始化缓存异常。

        Args:
            message: 异常消息
            operation: 操作类型（get, set, delete）
            key: 缓存键
            details: 异常详情
        """
        error_details = {"operation": operation, **(details or {})}
        if key:
            error_details["key"] = key

        super().__init__(
            message=message,
            code="CACHE_ERROR",
            details=error_details,
        )
