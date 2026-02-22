"""系统指标采集服务模块。

提供系统资源指标的采集和存储：
- CPU、内存、磁盘使用率采集
- Redis 存储历史指标
- 定时采集任务管理
"""

import asyncio
from datetime import datetime, timedelta
import time

from loguru import logger
import psutil

from src.schemas.monitor import MetricPoint, ResourceUsage
from src.storage.redis_client import redis_client


class MetricsService:
    """系统指标采集服务。

    采集系统资源使用情况并存储到 Redis。
    支持历史指标查询。

    Attributes:
        metrics_key: Redis 存储键名。
        retention_seconds: 指标保留时间（秒）。
        collect_interval: 采集间隔（秒）。
    """

    METRICS_KEY = "system:metrics:history"
    RETENTION_SECONDS = 3600
    COLLECT_INTERVAL = 10
    MAX_METRICS_POINTS = 360

    def __init__(self) -> None:
        """初始化指标服务。"""
        self._collect_task: asyncio.Task | None = None
        self._start_time = time.time()

    async def collect_metrics(self) -> ResourceUsage:
        """采集当前系统指标。

        Returns:
            ResourceUsage: 资源使用情况。
        """
        cpu_percent = await asyncio.to_thread(psutil.cpu_percent, 0.1)
        memory = await asyncio.to_thread(psutil.virtual_memory)
        disk = await asyncio.to_thread(psutil.disk_usage, "/")

        return ResourceUsage(
            cpu_percent=round(cpu_percent, 1),
            memory_percent=round(memory.percent, 1),
            memory_used_gb=round(memory.used / (1024**3), 2),
            memory_total_gb=round(memory.total / (1024**3), 2),
            disk_percent=round(disk.percent, 1),
            disk_used_gb=round(disk.used / (1024**3), 2),
            disk_total_gb=round(disk.total / (1024**3), 2),
        )

    async def store_metrics(self, metrics: ResourceUsage) -> None:
        """存储指标到 Redis。

        使用 Redis List 存储时间序列数据。

        Args:
            metrics: 资源使用情况。
        """
        try:
            point = MetricPoint(
                timestamp=datetime.now(),
                cpu_percent=metrics.cpu_percent,
                memory_percent=metrics.memory_percent,
                disk_percent=metrics.disk_percent,
            )

            point_data = point.model_dump_json()

            await redis_client.rpush(self.METRICS_KEY, point_data)

            current_len = await redis_client.llen(self.METRICS_KEY)
            if current_len > self.MAX_METRICS_POINTS:
                trim_count = current_len - self.MAX_METRICS_POINTS
                for _ in range(trim_count):
                    await redis_client.lpop(self.METRICS_KEY)

            await redis_client.expire(self.METRICS_KEY, self.RETENTION_SECONDS)

            logger.debug(f"存储指标: cpu={metrics.cpu_percent}%, memory={metrics.memory_percent}%")
        except Exception as e:
            logger.warning(f"存储指标失败: {e}")

    async def get_metrics_history(
        self,
        duration: int = 3600,
    ) -> list[MetricPoint]:
        """获取历史指标。

        Args:
            duration: 时间范围（秒）。

        Returns:
            指标数据点列表。
        """
        try:
            raw_data = await redis_client.lrange(self.METRICS_KEY, 0, -1)
            if not raw_data:
                return []

            points: list[MetricPoint] = []
            cutoff_time = datetime.now() - timedelta(seconds=duration)

            for item in raw_data:
                if isinstance(item, str):
                    try:
                        data = eval(item)
                        point = MetricPoint(**data)
                        if point.timestamp >= cutoff_time:
                            points.append(point)
                    except Exception:
                        continue

            points.sort(key=lambda x: x.timestamp)
            return points
        except Exception as e:
            logger.warning(f"获取历史指标失败: {e}")
            return []

    async def collect_and_store(self) -> ResourceUsage:
        """采集并存储指标。

        Returns:
            ResourceUsage: 采集的资源使用情况。
        """
        metrics = await self.collect_metrics()
        await self.store_metrics(metrics)
        return metrics

    async def start_collection(self) -> None:
        """启动定时采集任务。"""

        async def collect_loop() -> None:
            """采集循环。"""
            while True:
                try:
                    await self.collect_and_store()
                except Exception as e:
                    logger.warning(f"采集指标失败: {e}")
                await asyncio.sleep(self.COLLECT_INTERVAL)

        if self._collect_task is None or self._collect_task.done():
            self._collect_task = asyncio.create_task(collect_loop())
            logger.info("系统指标采集任务已启动")

    def stop_collection(self) -> None:
        """停止定时采集任务。"""
        if self._collect_task and not self._collect_task.done():
            self._collect_task.cancel()
            logger.info("系统指标采集任务已停止")

    def get_uptime_seconds(self) -> int:
        """获取服务运行时间。

        Returns:
            运行时间（秒）。
        """
        return int(time.time() - self._start_time)


metrics_service = MetricsService()


__all__ = ["MetricsService", "metrics_service"]
