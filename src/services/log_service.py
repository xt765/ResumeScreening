"""日志查询服务模块。

提供日志文件的查询、筛选和导出功能：
- 读取 JSON 格式日志文件
- 支持时间范围、级别、关键词筛选
- 分页查询
- 导出为 JSON/CSV 格式
"""

import asyncio
import csv
from datetime import datetime
from io import StringIO
import json
from pathlib import Path
import re
from typing import Any

from loguru import logger

from src.core.config import get_settings


class LogService:
    """日志查询服务。

    提供日志文件的查询和导出功能。
    支持按时间、级别、关键词筛选。

    Attributes:
        log_dir: 日志文件目录。
    """

    def __init__(self, log_dir: Path | None = None) -> None:
        """初始化日志服务。

        Args:
            log_dir: 日志文件目录，默认从配置读取。
        """
        settings = get_settings()
        self.log_dir = log_dir or Path(settings.app.log_dir)

    def _get_log_files(
        self,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> list[Path]:
        """获取指定时间范围内的日志文件列表。

        Args:
            start_time: 开始时间。
            end_time: 结束时间。

        Returns:
            日志文件路径列表，按时间倒序排列。
        """
        if not self.log_dir.exists():
            return []

        log_files: list[Path] = []

        for file_path in self.log_dir.glob("app_*.jsonl"):
            match = re.search(r"app_(\d{4}-\d{2}-\d{2})\.jsonl", file_path.name)
            if match:
                file_date = datetime.strptime(match.group(1), "%Y-%m-%d").date()

                if start_time and file_date < start_time.date():
                    continue
                if end_time and file_date > end_time.date():
                    continue

                log_files.append(file_path)

        log_files.sort(key=lambda x: x.name, reverse=True)
        return log_files

    def _parse_log_line(self, line: str) -> dict[str, Any] | None:
        """解析单行 JSON 日志。

        Args:
            line: JSON 格式的日志行。

        Returns:
            解析后的日志字典，解析失败返回 None。
        """
        try:
            data = json.loads(line.strip())
            if "timestamp" in data and isinstance(data["timestamp"], str):
                data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            return data
        except json.JSONDecodeError:
            return None

    def _match_filters(
        self,
        log_entry: dict[str, Any],
        start_time: datetime | None,
        end_time: datetime | None,
        levels: list[str] | None,
        keyword: str | None,
    ) -> bool:
        """检查日志条目是否匹配筛选条件。

        Args:
            log_entry: 日志条目字典。
            start_time: 开始时间。
            end_time: 结束时间。
            levels: 日志级别列表。
            keyword: 搜索关键词。

        Returns:
            是否匹配所有筛选条件。
        """
        timestamp = log_entry.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        # 时间比较：确保时区一致
        if timestamp and start_time:
            # 将时间转换为无时区比较
            ts_naive = timestamp.replace(tzinfo=None) if timestamp.tzinfo else timestamp
            st_naive = start_time.replace(tzinfo=None) if start_time.tzinfo else start_time
            if ts_naive < st_naive:
                return False

        if timestamp and end_time:
            ts_naive = timestamp.replace(tzinfo=None) if timestamp.tzinfo else timestamp
            et_naive = end_time.replace(tzinfo=None) if end_time.tzinfo else end_time
            if ts_naive > et_naive:
                return False

        if levels:
            entry_level = log_entry.get("level", "")
            if entry_level not in levels:
                return False

        if keyword:
            message = log_entry.get("message", "")
            if keyword.lower() not in message.lower():
                extra = log_entry.get("extra", {})
                extra_str = json.dumps(extra) if extra else ""
                if keyword.lower() not in extra_str.lower():
                    return False

        return True

    async def query_logs(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        levels: list[str] | None = None,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 50,
        order: str = "desc",
    ) -> tuple[list[dict[str, Any]], int]:
        """查询日志条目。

        Args:
            start_time: 开始时间。
            end_time: 结束时间。
            levels: 日志级别列表。
            keyword: 搜索关键词。
            page: 页码（从 1 开始）。
            page_size: 每页记录数。
            order: 排序方式（asc=正序，desc=逆序）。

        Returns:
            元组：(日志条目列表, 总记录数)。
        """
        log_files = self._get_log_files(start_time, end_time)
        all_logs: list[dict[str, Any]] = []

        def read_file_sync(file_path: Path) -> list[dict[str, Any]]:
            """同步读取日志文件。

            Args:
                file_path: 日志文件路径。

            Returns:
                日志条目列表。
            """
            logs = []
            try:
                with file_path.open(encoding="utf-8") as f:
                    for line in f:
                        entry = self._parse_log_line(line)
                        if entry and self._match_filters(
                            entry, start_time, end_time, levels, keyword
                        ):
                            logs.append(entry)
            except Exception as e:
                logger.warning(f"读取日志文件失败: {file_path}, error={e}")
            return logs

        for file_path in log_files:
            file_logs = await asyncio.to_thread(read_file_sync, file_path)
            all_logs.extend(file_logs)

        all_logs.sort(
            key=lambda x: x.get("timestamp", datetime.min),
            reverse=(order == "desc"),
        )

        total = len(all_logs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_logs = all_logs[start_idx:end_idx]

        return page_logs, total

    async def export_logs(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        levels: list[str] | None = None,
        keyword: str | None = None,
        format: str = "json",
    ) -> str:
        """导出日志。

        Args:
            start_time: 开始时间。
            end_time: 结束时间。
            levels: 日志级别列表。
            keyword: 搜索关键词。
            format: 导出格式（json/csv）。

        Returns:
            导出的日志内容字符串。
        """
        logs, _ = await self.query_logs(
            start_time=start_time,
            end_time=end_time,
            levels=levels,
            keyword=keyword,
            page=1,
            page_size=10000,
        )

        if format == "csv":
            return self._export_csv(logs)
        return self._export_json(logs)

    def _export_json(self, logs: list[dict[str, Any]]) -> str:
        """导出为 JSON 格式。

        Args:
            logs: 日志条目列表。

        Returns:
            JSON 格式字符串。
        """

        def serialize_datetime(obj: Any) -> Any:
            """序列化 datetime 对象。

            Args:
                obj: 待序列化对象。

            Returns:
                序列化后的对象。
            """
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        return json.dumps(logs, ensure_ascii=False, default=serialize_datetime, indent=2)

    def _export_csv(self, logs: list[dict[str, Any]]) -> str:
        """导出为 CSV 格式。

        Args:
            logs: 日志条目列表。

        Returns:
            CSV 格式字符串。
        """
        if not logs:
            return ""

        output = StringIO()
        fieldnames = [
            "timestamp",
            "level",
            "message",
            "module",
            "function",
            "line",
            "process_id",
            "thread_id",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for log in logs:
            row = {}
            for field in fieldnames:
                value = log.get(field)
                if isinstance(value, datetime):
                    value = value.isoformat()
                row[field] = value
            writer.writerow(row)

        return output.getvalue()

    async def get_log_stats(self) -> dict[str, Any]:
        """获取日志统计信息。

        Returns:
            包含日志统计信息的字典。
        """
        log_files = self._get_log_files(None, None)
        total_size = 0
        oldest_date: datetime | None = None
        newest_date: datetime | None = None

        for file_path in log_files:
            try:
                total_size += file_path.stat().st_size
                match = re.search(r"app_(\d{4}-\d{2}-\d{2})\.jsonl", file_path.name)
                if match:
                    file_date = datetime.strptime(match.group(1), "%Y-%m-%d")
                    if oldest_date is None or file_date < oldest_date:
                        oldest_date = file_date
                    if newest_date is None or file_date > newest_date:
                        newest_date = file_date
            except Exception:
                continue

        return {
            "total_files": len(log_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_date": oldest_date.isoformat() if oldest_date else None,
            "newest_date": newest_date.isoformat() if newest_date else None,
        }


log_service = LogService()


__all__ = ["LogService", "log_service"]
