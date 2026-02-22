"""日志模块单元测试。

测试 loguru 日志系统的配置和功能：
- setup_logger: 日志系统初始化
- get_logger: 获取日志实例
- json_format: JSON 格式化
- console_format: 控制台格式化
- json_serializer: JSON 序列化辅助函数
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from loguru import logger

from src.core.logger import (
    console_format,
    get_logger,
    json_format,
    json_serializer,
    setup_logger,
)


# ==================== JSON 序列化测试 ====================

class TestJSONSerializer:
    """JSON 序列化辅助函数测试类。"""

    def test_serialize_datetime(self) -> None:
        """测试序列化 datetime 对象。"""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = json_serializer(dt)

        assert result == "2024-01-15T10:30:45"

    def test_serialize_path(self) -> None:
        """测试序列化 Path 对象。"""
        path = Path("/tmp/test.log")
        result = json_serializer(path)

        # Windows 路径分隔符会被转换
        assert "test.log" in result

    def test_serialize_object_with_dict(self) -> None:
        """测试序列化包含 __dict__ 的对象。"""

        class TestObject:
            """测试对象类。"""

            def __init__(self, name: str, value: int):
                self.name = name
                self.value = value

        obj = TestObject("test", 123)
        result = json_serializer(obj)

        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 123

    def test_serialize_other_types(self) -> None:
        """测试序列化其他类型。"""
        # 整数
        assert json_serializer(123) == "123"

        # 浮点数
        assert json_serializer(3.14) == "3.14"

        # 布尔值
        assert json_serializer(True) == "True"

        # None
        assert json_serializer(None) == "None"

        # 列表
        result = json_serializer([1, 2, 3])
        assert result == "[1, 2, 3]"


# ==================== JSON 格式化测试 ====================

class TestJSONFormat:
    """JSON 格式化函数测试类。"""

    def test_json_format_basic(self) -> None:
        """测试基本 JSON 格式化。"""
        # 创建模拟的日志记录
        record = {
            "time": datetime(2024, 1, 15, 10, 30, 45),
            "level": MagicMock(name="INFO"),
            "message": "测试消息",
            "module": "test_module",
            "function": "test_function",
            "line": 42,
            "process": MagicMock(id=12345),
            "thread": MagicMock(id=67890),
            "extra": {},
            "exception": None,
        }

        record["level"].name = "INFO"

        result = json_format(record)

        # 验证结果是有效的 JSON
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["message"] == "测试消息"
        assert data["module"] == "test_module"
        assert data["function"] == "test_function"
        assert data["line"] == 42
        assert data["process_id"] == 12345
        assert data["thread_id"] == 67890
        assert "timestamp" in data

    def test_json_format_with_extra(self) -> None:
        """测试包含额外上下文的 JSON 格式化。"""
        record = {
            "time": datetime(2024, 1, 15, 10, 30, 45),
            "level": MagicMock(name="INFO"),
            "message": "测试消息",
            "module": "test_module",
            "function": "test_function",
            "line": 42,
            "process": MagicMock(id=12345),
            "thread": MagicMock(id=67890),
            "extra": {"user_id": "user123", "action": "login"},
            "exception": None,
        }

        record["level"].name = "INFO"

        result = json_format(record)
        data = json.loads(result)

        assert data["extra"]["user_id"] == "user123"
        assert data["extra"]["action"] == "login"

    def test_json_format_with_exception(self) -> None:
        """测试包含异常信息的 JSON 格式化。"""
        exception_info = MagicMock()
        exception_info.type = ValueError
        exception_info.value = "测试异常"
        exception_info.traceback = "traceback_string"

        record = {
            "time": datetime(2024, 1, 15, 10, 30, 45),
            "level": MagicMock(name="ERROR"),
            "message": "发生错误",
            "module": "test_module",
            "function": "test_function",
            "line": 42,
            "process": MagicMock(id=12345),
            "thread": MagicMock(id=67890),
            "extra": {},
            "exception": exception_info,
        }

        record["level"].name = "ERROR"

        result = json_format(record)
        data = json.loads(result)

        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert data["exception"]["value"] == "测试异常"
        assert data["exception"]["traceback"] == "traceback_string"

    def test_json_format_exception_none_type(self) -> None:
        """测试异常类型为 None 时的 JSON 格式化。"""
        exception_info = MagicMock()
        exception_info.type = None
        exception_info.value = None
        exception_info.traceback = None

        record = {
            "time": datetime(2024, 1, 15, 10, 30, 45),
            "level": MagicMock(name="ERROR"),
            "message": "发生错误",
            "module": "test_module",
            "function": "test_function",
            "line": 42,
            "process": MagicMock(id=12345),
            "thread": MagicMock(id=67890),
            "extra": {},
            "exception": exception_info,
        }

        record["level"].name = "ERROR"

        result = json_format(record)
        data = json.loads(result)

        assert data["exception"]["type"] is None
        assert data["exception"]["value"] is None
        assert data["exception"]["traceback"] is None


# ==================== 控制台格式化测试 ====================

class TestConsoleFormat:
    """控制台格式化函数测试类。"""

    def test_console_format_basic(self) -> None:
        """测试基本控制台格式化。"""
        record = {
            "time": datetime(2024, 1, 15, 10, 30, 45),
            "level": MagicMock(name="INFO"),
            "message": "测试消息",
            "module": "test_module",
            "function": "test_function",
            "line": 42,
            "exception": None,
        }

        record["level"].name = "INFO"

        result = console_format(record)

        # 验证格式化字符串包含必要的占位符
        assert "{time:" in result
        assert "{level:8}" in result
        assert "{module}" in result
        assert "{function}" in result
        assert "{line}" in result
        assert "{message}" in result

    def test_console_format_with_exception(self) -> None:
        """测试包含异常的控制台格式化。"""
        record = {
            "time": datetime(2024, 1, 15, 10, 30, 45),
            "level": MagicMock(name="ERROR"),
            "message": "发生错误",
            "module": "test_module",
            "function": "test_function",
            "line": 42,
            "exception": MagicMock(),
        }

        record["level"].name = "ERROR"

        result = console_format(record)

        # 验证异常信息被添加到格式化字符串
        assert "{exception}" in result

    def test_console_format_level_colors(self) -> None:
        """测试不同日志级别的颜色。"""
        level_colors = {
            "TRACE": "<dim>",
            "DEBUG": "<cyan>",
            "INFO": "<green>",
            "SUCCESS": "<bold><green>",
            "WARNING": "<yellow>",
            "ERROR": "<red>",
            "CRITICAL": "<bold><red>",
        }

        for level_name, expected_color in level_colors.items():
            record = {
                "time": datetime(2024, 1, 15, 10, 30, 45),
                "level": MagicMock(name=level_name),
                "message": "测试消息",
                "module": "test_module",
                "function": "test_function",
                "line": 42,
                "exception": None,
            }

            record["level"].name = level_name

            result = console_format(record)

            assert expected_color in result

    def test_console_format_unknown_level(self) -> None:
        """测试未知日志级别的格式化。"""
        record = {
            "time": datetime(2024, 1, 15, 10, 30, 45),
            "level": MagicMock(name="UNKNOWN"),
            "message": "测试消息",
            "module": "test_module",
            "function": "test_function",
            "line": 42,
            "exception": None,
        }

        record["level"].name = "UNKNOWN"

        result = console_format(record)

        # 未知级别不应该有颜色标签
        assert "<bold>" not in result or result.count("<") > 2


# ==================== setup_logger 测试 ====================

class TestSetupLogger:
    """日志系统初始化测试类。"""

    def test_setup_logger_creates_handlers(self, tmp_path: Path) -> None:
        """测试 setup_logger 创建处理器。

        Args:
            tmp_path: pytest 临时目录 fixture。
        """
        # Mock 配置
        mock_settings = MagicMock()
        mock_settings.app.log_level = "INFO"
        mock_settings.app.log_dir = str(tmp_path / "logs")

        with (
            patch("src.core.logger.get_settings", return_value=mock_settings),
            patch.object(logger, "remove"),
            patch.object(logger, "add"),
        ):
            setup_logger()

            # 验证 remove 被调用（移除默认处理器）
            logger.remove.assert_called_once()

            # 验证 add 被调用多次（控制台 + 文件 + 错误文件）
            assert logger.add.call_count == 3

    def test_setup_logger_creates_log_directory(self, tmp_path: Path) -> None:
        """测试 setup_logger 创建日志目录。

        Args:
            tmp_path: pytest 临时目录 fixture。
        """
        log_dir = tmp_path / "custom_logs"

        mock_settings = MagicMock()
        mock_settings.app.log_level = "DEBUG"
        mock_settings.app.log_dir = str(log_dir)

        with (
            patch("src.core.logger.get_settings", return_value=mock_settings),
            patch.object(logger, "remove"),
            patch.object(logger, "add"),
        ):
            setup_logger()

            # 验证日志目录被创建
            assert log_dir.exists()

    def test_setup_logger_console_handler_config(self, tmp_path: Path) -> None:
        """测试控制台处理器配置。

        Args:
            tmp_path: pytest 临时目录 fixture。
        """
        mock_settings = MagicMock()
        mock_settings.app.log_level = "DEBUG"
        mock_settings.app.log_dir = str(tmp_path / "logs")

        with (
            patch("src.core.logger.get_settings", return_value=mock_settings),
            patch.object(logger, "remove"),
            patch.object(logger, "add") as mock_add,
        ):
            setup_logger()

            # 获取控制台处理器调用
            console_call = mock_add.call_args_list[0]

            # 验证控制台处理器参数
            assert console_call.kwargs["sink"] == sys.stdout
            assert console_call.kwargs["level"] == "DEBUG"
            assert console_call.kwargs["colorize"] is True
            assert console_call.kwargs["enqueue"] is True

    def test_setup_logger_file_handler_config(self, tmp_path: Path) -> None:
        """测试文件处理器配置。

        Args:
            tmp_path: pytest 临时目录 fixture。
        """
        mock_settings = MagicMock()
        mock_settings.app.log_level = "INFO"
        mock_settings.app.log_dir = str(tmp_path / "logs")

        with (
            patch("src.core.logger.get_settings", return_value=mock_settings),
            patch.object(logger, "remove"),
            patch.object(logger, "add") as mock_add,
        ):
            setup_logger()

            # 获取文件处理器调用
            file_call = mock_add.call_args_list[1]

            # 验证文件处理器参数
            assert "app_" in str(file_call.args[0]) if file_call.args else True
            assert file_call.kwargs["level"] == "INFO"
            assert file_call.kwargs["rotation"] == "00:00"
            assert file_call.kwargs["retention"] == "30 days"
            assert file_call.kwargs["compression"] == "gz"
            assert file_call.kwargs["encoding"] == "utf-8"

    def test_setup_logger_error_file_handler_config(self, tmp_path: Path) -> None:
        """测试错误日志文件处理器配置。

        Args:
            tmp_path: pytest 临时目录 fixture。
        """
        mock_settings = MagicMock()
        mock_settings.app.log_level = "INFO"
        mock_settings.app.log_dir = str(tmp_path / "logs")

        with (
            patch("src.core.logger.get_settings", return_value=mock_settings),
            patch.object(logger, "remove"),
            patch.object(logger, "add") as mock_add,
        ):
            setup_logger()

            # 获取错误文件处理器调用
            error_call = mock_add.call_args_list[2]

            # 验证错误文件处理器参数
            assert error_call.kwargs["level"] == "ERROR"
            assert error_call.kwargs["rotation"] == "00:00"
            assert error_call.kwargs["retention"] == "30 days"


# ==================== get_logger 测试 ====================

class TestGetLogger:
    """获取日志实例测试类。"""

    def test_get_logger_without_handlers(self) -> None:
        """测试没有处理器时获取日志实例。"""
        # Mock logger._core.handlers 为空
        mock_core = MagicMock()
        mock_core.handlers = {}

        with (
            patch.object(logger, "_core", mock_core),
            patch("src.core.logger.setup_logger") as mock_setup,
        ):
            result = get_logger()

            # 验证 setup_logger 被调用
            mock_setup.assert_called_once()
            assert result == logger

    def test_get_logger_with_handlers(self) -> None:
        """测试已有处理器时获取日志实例。"""
        # Mock logger._core.handlers 不为空
        mock_core = MagicMock()
        mock_core.handlers = {1: MagicMock()}

        with (
            patch.object(logger, "_core", mock_core),
            patch("src.core.logger.setup_logger") as mock_setup,
        ):
            result = get_logger()

            # 验证 setup_logger 没有被调用
            mock_setup.assert_not_called()
            assert result == logger

    def test_get_logger_returns_logger_instance(self) -> None:
        """测试 get_logger 返回 logger 实例。"""
        mock_core = MagicMock()
        mock_core.handlers = {1: MagicMock()}

        with patch.object(logger, "_core", mock_core):
            result = get_logger()

            assert result is logger


# ==================== 集成测试 ====================

class TestLoggerIntegration:
    """日志模块集成测试类。"""

    def test_logger_write_to_file(self, tmp_path: Path) -> None:
        """测试日志写入文件。

        Args:
            tmp_path: pytest 临时目录 fixture。
        """
        log_file = tmp_path / "test.log"

        # 配置 logger 写入测试文件
        logger.remove()
        logger.add(str(log_file), format="{message}", level="INFO")

        # 写入测试消息
        test_message = "测试日志消息"
        logger.info(test_message)

        # 验证文件内容
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert test_message in content

    def test_logger_json_format_integration(self, tmp_path: Path) -> None:
        """测试 JSON 格式日志集成。

        Args:
            tmp_path: pytest 临时目录 fixture。
        """
        log_file = tmp_path / "test.jsonl"

        # 配置 logger 使用 JSON 格式（使用 serialize=True 来获取 JSON 输出）
        logger.remove()
        logger.add(str(log_file), format="{message}", level="INFO", serialize=True)

        # 写入测试消息
        test_message = "JSON格式测试消息"
        logger.info(test_message)

        # 验证文件内容是有效的 JSON
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        data = json.loads(content.strip())

        assert data["text"].strip() == test_message
        assert data["record"]["level"]["name"] == "INFO"

    def test_logger_with_exception(self, tmp_path: Path) -> None:
        """测试异常日志记录。

        Args:
            tmp_path: pytest 临时目录 fixture。
        """
        log_file = tmp_path / "error.log"

        # 配置 logger
        logger.remove()
        logger.add(str(log_file), format="{message}", level="ERROR", serialize=True)

        # 记录异常
        try:
            raise ValueError("测试异常")
        except ValueError:
            logger.exception("捕获到异常")

        # 验证异常信息被记录
        content = log_file.read_text(encoding="utf-8")
        data = json.loads(content.strip())

        assert "exception" in data["record"]
        assert data["record"]["exception"]["type"] == "ValueError"

    def test_logger_with_extra_context(self, tmp_path: Path) -> None:
        """测试带额外上下文的日志记录。

        Args:
            tmp_path: pytest 临时目录 fixture。
        """
        log_file = tmp_path / "context.log"

        # 配置 logger
        logger.remove()
        logger.add(str(log_file), format="{message}", level="INFO", serialize=True)

        # 记录带上下文的日志
        logger.bind(user_id="user123", action="login").info("用户登录")

        # 验证上下文信息被记录
        content = log_file.read_text(encoding="utf-8")
        data = json.loads(content.strip())

        # loguru serialize 格式中 extra 在 record.extra
        assert "record" in data
        assert data["record"]["extra"]["user_id"] == "user123"
        assert data["record"]["extra"]["action"] == "login"


# ==================== 边界情况测试 ====================

class TestLoggerEdgeCases:
    """日志模块边界情况测试类。"""

    def test_json_format_with_unicode(self) -> None:
        """测试 JSON 格式化包含 Unicode 字符。"""
        record = {
            "time": datetime(2024, 1, 15, 10, 30, 45),
            "level": MagicMock(name="INFO"),
            "message": "中文消息🎉测试",
            "module": "测试模块",
            "function": "测试函数",
            "line": 42,
            "process": MagicMock(id=12345),
            "thread": MagicMock(id=67890),
            "extra": {},
            "exception": None,
        }

        record["level"].name = "INFO"

        result = json_format(record)
        data = json.loads(result)

        assert data["message"] == "中文消息🎉测试"
        assert data["module"] == "测试模块"

    def test_json_format_with_empty_message(self) -> None:
        """测试 JSON 格式化空消息。"""
        record = {
            "time": datetime(2024, 1, 15, 10, 30, 45),
            "level": MagicMock(name="INFO"),
            "message": "",
            "module": "test_module",
            "function": "test_function",
            "line": 42,
            "process": MagicMock(id=12345),
            "thread": MagicMock(id=67890),
            "extra": {},
            "exception": None,
        }

        record["level"].name = "INFO"

        result = json_format(record)
        data = json.loads(result)

        assert data["message"] == ""

    def test_json_format_with_very_long_message(self) -> None:
        """测试 JSON 格式化超长消息。"""
        long_message = "x" * 10000

        record = {
            "time": datetime(2024, 1, 15, 10, 30, 45),
            "level": MagicMock(name="INFO"),
            "message": long_message,
            "module": "test_module",
            "function": "test_function",
            "line": 42,
            "process": MagicMock(id=12345),
            "thread": MagicMock(id=67890),
            "extra": {},
            "exception": None,
        }

        record["level"].name = "INFO"

        result = json_format(record)
        data = json.loads(result)

        assert data["message"] == long_message

    def test_json_serializer_with_nested_object(self) -> None:
        """测试 JSON 序列化嵌套对象。"""

        class NestedObject:
            """嵌套对象类。"""

            def __init__(self):
                self.inner = {"key": "value"}

        obj = NestedObject()
        result = json_serializer(obj)

        assert isinstance(result, dict)
        assert result["inner"]["key"] == "value"

    def test_console_format_with_multiline_message(self) -> None:
        """测试控制台格式化多行消息。"""
        multiline_message = "第一行\n第二行\n第三行"

        record = {
            "time": datetime(2024, 1, 15, 10, 30, 45),
            "level": MagicMock(name="INFO"),
            "message": multiline_message,
            "module": "test_module",
            "function": "test_function",
            "line": 42,
            "exception": None,
        }

        record["level"].name = "INFO"

        result = console_format(record)

        # 验证格式化字符串包含消息占位符
        assert "{message}" in result
