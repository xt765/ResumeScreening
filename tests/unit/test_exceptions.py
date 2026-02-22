"""业务异常类测试模块。

测试系统中所有业务异常类：
- BaseAppException 基类
- StorageException 存储异常
- LLMException LLM 调用异常
- ParseException 解析异常
- ValidationException 验证异常
- WorkflowException 工作流异常
- DatabaseException 数据库异常
- CacheException 缓存异常
"""

from typing import Any

import pytest

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


# ==================== BaseAppException 测试 ====================


class TestBaseAppException:
    """BaseAppException 基类测试类。"""

    def test_create_with_message_only(self) -> None:
        """测试仅使用消息创建异常。"""
        exc = BaseAppException("测试异常消息")

        assert exc.message == "测试异常消息"
        assert exc.code == "UNKNOWN_ERROR"
        assert exc.details == {}

    def test_create_with_all_params(self) -> None:
        """测试使用所有参数创建异常。"""
        exc = BaseAppException(
            message="自定义异常",
            code="CUSTOM_ERROR",
            details={"key": "value", "count": 42},
        )

        assert exc.message == "自定义异常"
        assert exc.code == "CUSTOM_ERROR"
        assert exc.details["key"] == "value"
        assert exc.details["count"] == 42

    def test_to_dict_returns_correct_format(self) -> None:
        """测试 to_dict 返回正确格式。"""
        exc = BaseAppException(
            message="测试消息",
            code="TEST_CODE",
            details={"field": "name"},
        )

        result = exc.to_dict()

        assert isinstance(result, dict)
        assert result["code"] == "TEST_CODE"
        assert result["message"] == "测试消息"
        assert result["details"]["field"] == "name"

    def test_to_dict_with_empty_details(self) -> None:
        """测试 to_dict 处理空详情。"""
        exc = BaseAppException("简单异常")

        result = exc.to_dict()

        assert result["details"] == {}

    def test_str_representation(self) -> None:
        """测试字符串表示。"""
        exc = BaseAppException(
            message="错误消息",
            code="ERR001",
        )

        str_repr = str(exc)

        assert "[ERR001]" in str_repr
        assert "错误消息" in str_repr

    def test_exception_is_subclass_of_exception(self) -> None:
        """测试异常继承自 Exception。"""
        exc = BaseAppException("测试")

        assert isinstance(exc, Exception)

    def test_exception_can_be_raised_and_caught(self) -> None:
        """测试异常可以被抛出和捕获。"""
        with pytest.raises(BaseAppException) as exc_info:
            raise BaseAppException("可捕获的异常")

        assert str(exc_info.value) == "[UNKNOWN_ERROR] 可捕获的异常"

    def test_details_default_to_empty_dict(self) -> None:
        """测试 details 默认为空字典。"""
        exc = BaseAppException("测试")

        assert exc.details == {}
        assert isinstance(exc.details, dict)

    def test_details_not_shared_between_instances(self) -> None:
        """测试不同实例的 details 不共享。"""
        exc1 = BaseAppException("异常1", details={"key": "value1"})
        exc2 = BaseAppException("异常2", details={"key": "value2"})

        assert exc1.details["key"] == "value1"
        assert exc2.details["key"] == "value2"


# ==================== StorageException 测试 ====================


class TestStorageException:
    """StorageException 存储异常测试类。"""

    def test_create_with_message_only(self) -> None:
        """测试仅使用消息创建存储异常。"""
        exc = StorageException("存储失败")

        assert exc.message == "存储失败"
        assert exc.code == "STORAGE_ERROR"
        assert exc.details["storage_type"] == "unknown"

    def test_create_with_storage_type(self) -> None:
        """测试指定存储类型创建异常。"""
        exc = StorageException(
            message="MinIO 上传失败",
            storage_type="minio",
        )

        assert exc.details["storage_type"] == "minio"

    def test_create_with_all_params(self) -> None:
        """测试使用所有参数创建存储异常。"""
        exc = StorageException(
            message="文件上传失败",
            storage_type="minio",
            details={"bucket": "resumes", "file": "test.pdf"},
        )

        assert exc.message == "文件上传失败"
        assert exc.code == "STORAGE_ERROR"
        assert exc.details["storage_type"] == "minio"
        assert exc.details["bucket"] == "resumes"
        assert exc.details["file"] == "test.pdf"

    def test_inherits_from_base_app_exception(self) -> None:
        """测试继承自 BaseAppException。"""
        exc = StorageException("测试")

        assert isinstance(exc, BaseAppException)
        assert isinstance(exc, Exception)

    def test_str_representation(self) -> None:
        """测试字符串表示。"""
        exc = StorageException("上传失败", storage_type="minio")

        str_repr = str(exc)

        assert "[STORAGE_ERROR]" in str_repr
        assert "上传失败" in str_repr


# ==================== LLMException 测试 ====================


class TestLLMException:
    """LLMException LLM 异常测试类。"""

    def test_create_with_message_only(self) -> None:
        """测试仅使用消息创建 LLM 异常。"""
        exc = LLMException("LLM 调用失败")

        assert exc.message == "LLM 调用失败"
        assert exc.code == "LLM_ERROR"
        assert exc.details["provider"] == "unknown"
        assert exc.details["model"] == "unknown"

    def test_create_with_provider_and_model(self) -> None:
        """测试指定提供商和模型创建异常。"""
        exc = LLMException(
            message="API 超时",
            provider="deepseek",
            model="deepseek-chat",
        )

        assert exc.details["provider"] == "deepseek"
        assert exc.details["model"] == "deepseek-chat"

    def test_create_with_all_params(self) -> None:
        """测试使用所有参数创建 LLM 异常。"""
        exc = LLMException(
            message="Token 超限",
            provider="dashscope",
            model="qwen-max",
            details={"tokens_used": 10000, "limit": 8000},
        )

        assert exc.details["provider"] == "dashscope"
        assert exc.details["model"] == "qwen-max"
        assert exc.details["tokens_used"] == 10000

    def test_inherits_from_base_app_exception(self) -> None:
        """测试继承自 BaseAppException。"""
        exc = LLMException("测试")

        assert isinstance(exc, BaseAppException)

    def test_str_representation(self) -> None:
        """测试字符串表示。"""
        exc = LLMException("超时", provider="deepseek", model="deepseek-chat")

        str_repr = str(exc)

        assert "[LLM_ERROR]" in str_repr
        assert "超时" in str_repr


# ==================== ParseException 测试 ====================


class TestParseException:
    """ParseException 解析异常测试类。"""

    def test_create_with_message_only(self) -> None:
        """测试仅使用消息创建解析异常。"""
        exc = ParseException("解析失败")

        assert exc.message == "解析失败"
        assert exc.code == "PARSE_ERROR"
        assert exc.details["file_type"] == "unknown"
        assert exc.details["file_name"] == "unknown"

    def test_create_with_file_info(self) -> None:
        """测试指定文件信息创建异常。"""
        exc = ParseException(
            message="PDF 解析失败",
            file_type="pdf",
            file_name="resume.pdf",
        )

        assert exc.details["file_type"] == "pdf"
        assert exc.details["file_name"] == "resume.pdf"

    def test_create_with_all_params(self) -> None:
        """测试使用所有参数创建解析异常。"""
        exc = ParseException(
            message="Word 文档损坏",
            file_type="docx",
            file_name="test.docx",
            details={"page": 3, "error_code": "CORRUPTED"},
        )

        assert exc.details["file_type"] == "docx"
        assert exc.details["file_name"] == "test.docx"
        assert exc.details["page"] == 3
        assert exc.details["error_code"] == "CORRUPTED"

    def test_inherits_from_base_app_exception(self) -> None:
        """测试继承自 BaseAppException。"""
        exc = ParseException("测试")

        assert isinstance(exc, BaseAppException)

    def test_str_representation(self) -> None:
        """测试字符串表示。"""
        exc = ParseException("解析失败", file_type="pdf", file_name="test.pdf")

        str_repr = str(exc)

        assert "[PARSE_ERROR]" in str_repr
        assert "解析失败" in str_repr


# ==================== ValidationException 测试 ====================


class TestValidationException:
    """ValidationException 验证异常测试类。"""

    def test_create_with_message_only(self) -> None:
        """测试仅使用消息创建验证异常。"""
        exc = ValidationException("验证失败")

        assert exc.message == "验证失败"
        assert exc.code == "VALIDATION_ERROR"
        assert exc.details == {}

    def test_create_with_field_only(self) -> None:
        """测试仅指定字段创建异常。"""
        exc = ValidationException(
            message="字段验证失败",
            field="email",
        )

        assert exc.details["field"] == "email"
        assert "value" not in exc.details

    def test_create_with_field_and_value(self) -> None:
        """测试指定字段和值创建异常。"""
        exc = ValidationException(
            message="邮箱格式不正确",
            field="email",
            value="invalid-email",
        )

        assert exc.details["field"] == "email"
        assert exc.details["value"] == "invalid-email"

    def test_create_with_all_params(self) -> None:
        """测试使用所有参数创建验证异常。"""
        exc = ValidationException(
            message="参数超出范围",
            field="age",
            value=150,
            details={"min": 0, "max": 120},
        )

        assert exc.details["field"] == "age"
        assert exc.details["value"] == "150"  # 转换为字符串
        assert exc.details["min"] == 0
        assert exc.details["max"] == 120

    def test_value_is_converted_to_string(self) -> None:
        """测试值被转换为字符串。"""
        exc = ValidationException(
            message="测试",
            field="count",
            value=12345,
        )

        assert exc.details["value"] == "12345"
        assert isinstance(exc.details["value"], str)

    def test_value_none_is_not_included(self) -> None:
        """测试 None 值不被包含在详情中。"""
        exc = ValidationException(
            message="测试",
            field="name",
            value=None,
        )

        assert "value" not in exc.details

    def test_inherits_from_base_app_exception(self) -> None:
        """测试继承自 BaseAppException。"""
        exc = ValidationException("测试")

        assert isinstance(exc, BaseAppException)

    def test_str_representation(self) -> None:
        """测试字符串表示。"""
        exc = ValidationException("验证失败", field="name")

        str_repr = str(exc)

        assert "[VALIDATION_ERROR]" in str_repr
        assert "验证失败" in str_repr


# ==================== WorkflowException 测试 ====================


class TestWorkflowException:
    """WorkflowException 工作流异常测试类。"""

    def test_create_with_message_only(self) -> None:
        """测试仅使用消息创建工作流异常。"""
        exc = WorkflowException("工作流执行失败")

        assert exc.message == "工作流执行失败"
        assert exc.code == "WORKFLOW_ERROR"
        assert exc.details["node"] == "unknown"
        assert exc.details["state"] == "unknown"

    def test_create_with_node_and_state(self) -> None:
        """测试指定节点和状态创建异常。"""
        exc = WorkflowException(
            message="节点执行超时",
            node="FilterNode",
            state="processing",
        )

        assert exc.details["node"] == "FilterNode"
        assert exc.details["state"] == "processing"

    def test_create_with_all_params(self) -> None:
        """测试使用所有参数创建工作流异常。"""
        exc = WorkflowException(
            message="状态转换失败",
            node="StoreNode",
            state="storing",
            details={"attempt": 3, "max_retries": 3},
        )

        assert exc.details["node"] == "StoreNode"
        assert exc.details["state"] == "storing"
        assert exc.details["attempt"] == 3

    def test_inherits_from_base_app_exception(self) -> None:
        """测试继承自 BaseAppException。"""
        exc = WorkflowException("测试")

        assert isinstance(exc, BaseAppException)

    def test_str_representation(self) -> None:
        """测试字符串表示。"""
        exc = WorkflowException("执行失败", node="ParseNode", state="parsing")

        str_repr = str(exc)

        assert "[WORKFLOW_ERROR]" in str_repr
        assert "执行失败" in str_repr


# ==================== DatabaseException 测试 ====================


class TestDatabaseException:
    """DatabaseException 数据库异常测试类。"""

    def test_create_with_message_only(self) -> None:
        """测试仅使用消息创建数据库异常。"""
        exc = DatabaseException("数据库操作失败")

        assert exc.message == "数据库操作失败"
        assert exc.code == "DATABASE_ERROR"
        assert exc.details["operation"] == "unknown"
        assert exc.details["table"] == "unknown"

    def test_create_with_operation_and_table(self) -> None:
        """测试指定操作和表创建异常。"""
        exc = DatabaseException(
            message="查询超时",
            operation="select",
            table="talent_info",
        )

        assert exc.details["operation"] == "select"
        assert exc.details["table"] == "talent_info"

    def test_create_with_all_params(self) -> None:
        """测试使用所有参数创建数据库异常。"""
        exc = DatabaseException(
            message="唯一约束冲突",
            operation="insert",
            table="screening_condition",
            details={"constraint": "uk_name", "value": "测试条件"},
        )

        assert exc.details["operation"] == "insert"
        assert exc.details["table"] == "screening_condition"
        assert exc.details["constraint"] == "uk_name"

    def test_inherits_from_base_app_exception(self) -> None:
        """测试继承自 BaseAppException。"""
        exc = DatabaseException("测试")

        assert isinstance(exc, BaseAppException)

    def test_str_representation(self) -> None:
        """测试字符串表示。"""
        exc = DatabaseException("连接失败", operation="connect", table="mysql")

        str_repr = str(exc)

        assert "[DATABASE_ERROR]" in str_repr
        assert "连接失败" in str_repr


# ==================== CacheException 测试 ====================


class TestCacheException:
    """CacheException 缓存异常测试类。"""

    def test_create_with_message_only(self) -> None:
        """测试仅使用消息创建缓存异常。"""
        exc = CacheException("缓存操作失败")

        assert exc.message == "缓存操作失败"
        assert exc.code == "CACHE_ERROR"
        assert exc.details["operation"] == "unknown"
        assert "key" not in exc.details

    def test_create_with_operation_only(self) -> None:
        """测试仅指定操作创建异常。"""
        exc = CacheException(
            message="缓存读取失败",
            operation="get",
        )

        assert exc.details["operation"] == "get"
        assert "key" not in exc.details

    def test_create_with_operation_and_key(self) -> None:
        """测试指定操作和键创建异常。"""
        exc = CacheException(
            message="缓存键不存在",
            operation="get",
            key="talent:123",
        )

        assert exc.details["operation"] == "get"
        assert exc.details["key"] == "talent:123"

    def test_create_with_all_params(self) -> None:
        """测试使用所有参数创建缓存异常。"""
        exc = CacheException(
            message="缓存序列化失败",
            operation="set",
            key="result:456",
            details={"data_type": "complex_object"},
        )

        assert exc.details["operation"] == "set"
        assert exc.details["key"] == "result:456"
        assert exc.details["data_type"] == "complex_object"

    def test_key_none_is_not_included(self) -> None:
        """测试 None 键不被包含在详情中。"""
        exc = CacheException(
            message="测试",
            operation="delete",
            key=None,
        )

        assert "key" not in exc.details

    def test_inherits_from_base_app_exception(self) -> None:
        """测试继承自 BaseAppException。"""
        exc = CacheException("测试")

        assert isinstance(exc, BaseAppException)

    def test_str_representation(self) -> None:
        """测试字符串表示。"""
        exc = CacheException("操作失败", operation="set", key="test:123")

        str_repr = str(exc)

        assert "[CACHE_ERROR]" in str_repr
        assert "操作失败" in str_repr


# ==================== 异常继承关系测试 ====================


class TestExceptionInheritance:
    """异常继承关系测试类。"""

    def test_all_exceptions_inherit_from_base(self) -> None:
        """测试所有异常继承自 BaseAppException。"""
        exceptions = [
            StorageException("test"),
            LLMException("test"),
            ParseException("test"),
            ValidationException("test"),
            WorkflowException("test"),
            DatabaseException("test"),
            CacheException("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, BaseAppException)
            assert isinstance(exc, Exception)

    def test_can_catch_all_with_base_exception(self) -> None:
        """测试可以使用 BaseAppException 捕获所有业务异常。"""
        exceptions_to_raise = [
            StorageException("存储错误"),
            LLMException("LLM 错误"),
            ParseException("解析错误"),
            ValidationException("验证错误"),
            WorkflowException("工作流错误"),
            DatabaseException("数据库错误"),
            CacheException("缓存错误"),
        ]

        for exc in exceptions_to_raise:
            with pytest.raises(BaseAppException):
                raise exc

    def test_exception_codes_are_unique(self) -> None:
        """测试各异常类的错误代码唯一。"""
        codes = [
            StorageException("test").code,
            LLMException("test").code,
            ParseException("test").code,
            ValidationException("test").code,
            WorkflowException("test").code,
            DatabaseException("test").code,
            CacheException("test").code,
        ]

        assert len(codes) == len(set(codes))


# ==================== 边界情况测试 ====================


class TestExceptionEdgeCases:
    """异常边界情况测试类。"""

    def test_exception_with_empty_message(self) -> None:
        """测试空消息异常。"""
        exc = BaseAppException("")

        assert exc.message == ""
        assert str(exc) == "[UNKNOWN_ERROR] "

    def test_exception_with_very_long_message(self) -> None:
        """测试超长消息异常。"""
        long_message = "这是一个非常长的错误消息" * 100
        exc = BaseAppException(long_message)

        assert exc.message == long_message
        assert len(exc.message) == len(long_message)

    def test_exception_with_special_characters_in_message(self) -> None:
        """测试消息包含特殊字符。"""
        special_message = "错误: 文件名包含特殊字符 <>&\"'"
        exc = BaseAppException(special_message)

        assert exc.message == special_message

    def test_exception_with_nested_details(self) -> None:
        """测试嵌套详情。"""
        nested_details: dict[str, Any] = {
            "level1": {
                "level2": {
                    "level3": "value",
                },
            },
            "list": [1, 2, 3],
        }
        exc = BaseAppException(
            message="嵌套详情测试",
            details=nested_details,
        )

        assert exc.details["level1"]["level2"]["level3"] == "value"
        assert exc.details["list"] == [1, 2, 3]

    def test_exception_with_unicode_details(self) -> None:
        """测试 Unicode 详情。"""
        exc = BaseAppException(
            message="Unicode 测试",
            details={"中文": "值", "emoji": "🎉"},
        )

        assert exc.details["中文"] == "值"
        assert exc.details["emoji"] == "🎉"

    def test_to_dict_can_be_json_serialized(self) -> None:
        """测试 to_dict 结果可 JSON 序列化。"""
        import json

        exc = ValidationException(
            message="测试",
            field="name",
            value="测试值",
            details={"count": 123},
        )

        result = exc.to_dict()

        # 应该可以序列化
        json_str = json.dumps(result, ensure_ascii=False)
        parsed = json.loads(json_str)

        assert parsed["code"] == "VALIDATION_ERROR"
        assert parsed["message"] == "测试"
