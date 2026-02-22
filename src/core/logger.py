"""日志配置模块。

配置 loguru 日志系统，支持：
- JSON 格式结构化输出
- 按日期轮转，保留 30 天
- 控制台和文件双输出
- 完整异常堆栈追踪
"""

from datetime import datetime
import json
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any

from loguru import logger

from src.core.config import get_settings

if TYPE_CHECKING:
    from loguru import Record


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


def json_format(record: "Record") -> str:
    """格式化日志记录为 JSON 格式。

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

    # 添加额外上下文信息
    if record.get("extra"):
        log_data["extra"] = record["extra"]

    # 添加异常信息
    if record["exception"]:
        log_data["exception"] = {
            "type": record["exception"].type.__name__ if record["exception"].type else None,
            "value": str(record["exception"].value) if record["exception"].value else None,
            "traceback": record["exception"].traceback if record["exception"].traceback else None,
        }

    return json.dumps(log_data, ensure_ascii=False, default=json_serializer) + "\n"


def console_format(record: "Record") -> str:
    """格式化控制台日志输出。

    使用彩色格式，便于开发调试。

    Args:
        record: loguru 日志记录

    Returns:
        格式化的日志字符串
    """
    # 定义颜色映射
    level_colors = {
        "TRACE": "<dim>",
        "DEBUG": "<cyan>",
        "INFO": "<green>",
        "SUCCESS": "<bold><green>",
        "WARNING": "<yellow>",
        "ERROR": "<red>",
        "CRITICAL": "<bold><red>",
    }

    color = level_colors.get(record["level"].name, "")
    end_color = "</>" if color else ""

    # 构建格式化字符串
    time_str = "<cyan>{time:YYYY-MM-DD HH:mm:ss}</cyan>"
    level_str = f"{color}{{level:8}}{end_color}"
    module_str = "<blue>{module}:{function}:{line}</blue>"
    message_str = "{message}"

    format_str = f"{time_str} | {level_str} | {module_str} - {message_str}"

    # 添加异常信息
    if record["exception"]:
        format_str += "\n{exception}"

    return format_str + "\n"


def setup_logger() -> None:
    """配置 loguru 日志系统。

    移除默认处理器，添加控制台和文件处理器。
    文件日志按日期轮转，保留 30 天。
    """
    settings = get_settings()

    # 移除默认处理器
    logger.remove()

    # 添加控制台处理器（彩色格式）
    logger.add(
        sink=sys.stdout,
        format=console_format,
        level=settings.app.log_level,
        colorize=True,
        enqueue=True,
    )

    # 确保日志目录存在
    log_dir = Path(settings.app.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 添加文件处理器（JSON 格式，按日轮转）
    log_file = log_dir / "app_{time:YYYY-MM-DD}.jsonl"
    logger.add(
        sink=str(log_file),
        format=json_format,
        level=settings.app.log_level,
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留 30 天
        compression="gz",  # 压缩旧日志
        encoding="utf-8",
        enqueue=True,
        serialize=False,
    )

    # 添加错误日志单独文件
    error_log_file = log_dir / "error_{time:YYYY-MM-DD}.jsonl"
    logger.add(
        sink=str(error_log_file),
        format=json_format,
        level="ERROR",
        rotation="00:00",
        retention="30 days",
        compression="gz",
        encoding="utf-8",
        enqueue=True,
        serialize=False,
    )

    logger.info("日志系统初始化完成", log_dir=str(log_dir))


def get_logger():
    """获取 logger 实例。

    如果日志系统未初始化，先进行初始化。

    Returns:
        loguru Logger 实例
    """
    # 检查是否已有处理器，没有则初始化
    if not logger._core.handlers:  # type: ignore
        setup_logger()
    return logger
