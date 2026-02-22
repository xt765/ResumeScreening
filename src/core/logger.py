"""日志配置模块。

配置 loguru 日志系统，支持：
- JSON 格式结构化输出
- 按日期轮转，保留 30 天
- 控制台和文件双输出
- 完整异常堆栈追踪
"""

import json
from datetime import datetime
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any, TextIO

from loguru import logger

from src.core.config import get_settings

if TYPE_CHECKING:
    from loguru import Record, Message


def json_serializer(obj: Any) -> Any:
    """JSON 序列化辅助函数。

    处理非标准 JSON 类型的对象。

    Args:
        obj: 待序列化对象

    Returns:
        可 JSON 序列化的对象
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def format_json_record(record: "Record") -> str:
    """格式化日志记录为 JSON 字符串。

    Args:
        record: loguru 日志记录

    Returns:
        JSON 格式的日志字符串
    """
    log_data: dict[str, Any] = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
        "process_id": record["process"].id,
        "thread_id": record["thread"].id,
    }

    if record.get("extra"):
        log_data["extra"] = record["extra"]

    if record["exception"]:
        log_data["exception"] = {
            "type": record["exception"].type.__name__ if record["exception"].type else None,
            "value": str(record["exception"].value) if record["exception"].value else None,
            "traceback": record["exception"].traceback if record["exception"].traceback else None,
        }

    return json.dumps(log_data, ensure_ascii=False, default=json_serializer)


class JsonFileSink:
    """JSON 文件日志 sink。

    自定义 sink 类，避免 loguru 格式字符串问题。
    """

    def __init__(self, file_path: Path):
        """初始化 sink。

        Args:
            file_path: 日志文件路径
        """
        self.file_path = file_path
        self._file: TextIO | None = None

    def write(self, message: "Message") -> None:
        """写入日志消息。

        Args:
            message: loguru 日志消息
        """
        if self._file is None:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self._file = open(self.file_path, "a", encoding="utf-8")

        json_str = format_json_record(message.record)
        self._file.write(json_str + "\n")
        self._file.flush()

    def stop(self) -> None:
        """停止 sink，关闭文件。"""
        if self._file:
            self._file.close()
            self._file = None


def console_format(record: "Record") -> str:
    """格式化控制台日志输出。

    使用彩色格式，便于开发调试。

    Args:
        record: loguru 日志记录

    Returns:
        格式化的日志字符串
    """
    level_colors = {
        "TRACE": "<dim>",
        "DEBUG": "<cyan>",
        "INFO": "<green>",
        "SUCCESS": "<green><bold>",
        "WARNING": "<yellow>",
        "ERROR": "<red>",
        "CRITICAL": "<red><bold>",
    }

    color = level_colors.get(record["level"].name, "")
    end_color = "</>" * color.count("<") if color else ""

    time_str = "<cyan>{time:YYYY-MM-DD HH:mm:ss}</cyan>"
    level_str = f"{color}{{level:8}}{end_color}"
    module_str = "<blue>{module}:{function}:{line}</blue>"
    message_str = "{message}"

    format_str = f"{time_str} | {level_str} | {module_str} - {message_str}"

    if record["exception"]:
        format_str += "\n{exception}"

    return format_str + "\n"


def setup_logger() -> None:
    """配置 loguru 日志系统。

    移除默认处理器，添加控制台和文件处理器。
    文件日志按日期轮转，保留 30 天。
    """
    settings = get_settings()

    logger.remove()

    logger.add(
        sink=sys.stdout,
        format=console_format,
        level=settings.app.log_level,
        colorize=True,
        enqueue=True,
    )

    log_dir = Path(settings.app.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"app_{today}.jsonl"
    logger.add(
        sink=JsonFileSink(log_file),
        level=settings.app.log_level,
        enqueue=True,
    )

    error_log_file = log_dir / f"error_{today}.jsonl"
    logger.add(
        sink=JsonFileSink(error_log_file),
        level="ERROR",
        enqueue=True,
    )

    logger.info("日志系统初始化完成", log_dir=str(log_dir))


def get_logger():
    """获取 logger 实例。

    如果日志系统未初始化，先进行初始化。

    Returns:
        loguru Logger 实例
    """
    if not logger._core.handlers:
        setup_logger()
    return logger
