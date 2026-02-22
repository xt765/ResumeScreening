"""后台任务管理模块。

提供异步任务管理功能：
- 任务创建和执行
- 任务状态跟踪
- 进度更新通知
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Callable
from uuid import uuid4

from loguru import logger


class TaskStatusEnum(StrEnum):
    """任务状态枚举。

    Attributes:
        PENDING: 待处理
        RUNNING: 执行中
        COMPLETED: 已完成
        FAILED: 失败
        CANCELLED: 已取消
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskProgress:
    """任务进度信息。

    Attributes:
        current: 当前处理数量
        total: 总数量
        message: 进度消息
        percentage: 完成百分比
    """

    current: int = 0
    total: int = 0
    message: str = ""
    percentage: float = 0.0


@dataclass
class TaskInfo:
    """任务信息。

    Attributes:
        id: 任务 ID
        name: 任务名称
        status: 任务状态
        progress: 任务进度
        result: 任务结果
        error: 错误信息
        created_at: 创建时间
        started_at: 开始时间
        completed_at: 完成时间
        metadata: 任务元数据
    """

    id: str
    name: str
    status: TaskStatusEnum = TaskStatusEnum.PENDING
    progress: TaskProgress = field(default_factory=TaskProgress)
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式。

        Returns:
            dict[str, Any]: 任务信息字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "progress": {
                "current": self.progress.current,
                "total": self.progress.total,
                "message": self.progress.message,
                "percentage": self.progress.percentage,
            },
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }


class TaskManager:
    """任务管理器。

    管理后台任务的创建、执行和状态跟踪。

    Attributes:
        tasks: 任务字典
        callbacks: 进度更新回调列表
    """

    def __init__(self) -> None:
        """初始化任务管理器。"""
        self.tasks: dict[str, TaskInfo] = {}
        self.callbacks: list[Callable[[str, TaskInfo], None]] = []
        self._running_tasks: dict[str, asyncio.Task] = {}

    def register_callback(self, callback: Callable[[str, TaskInfo], None]) -> None:
        """注册进度更新回调。

        Args:
            callback: 回调函数，接收任务 ID 和任务信息
        """
        self.callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[str, TaskInfo], None]) -> None:
        """注销进度更新回调。

        Args:
            callback: 要注销的回调函数
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    async def _notify_callbacks(self, task_id: str, task_info: TaskInfo) -> None:
        """通知所有回调。

        Args:
            task_id: 任务 ID
            task_info: 任务信息
        """
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task_id, task_info)
                else:
                    callback(task_id, task_info)
            except Exception as e:
                logger.warning(f"回调执行失败: {e}")

    def create_task(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> TaskInfo:
        """创建新任务。

        Args:
            name: 任务名称
            metadata: 任务元数据

        Returns:
            TaskInfo: 创建的任务信息
        """
        task_id = str(uuid4())
        task_info = TaskInfo(
            id=task_id,
            name=name,
            metadata=metadata or {},
        )
        self.tasks[task_id] = task_info
        logger.info(f"创建任务: id={task_id}, name={name}")
        return task_info

    async def update_progress(
        self,
        task_id: str,
        current: int,
        total: int,
        message: str = "",
    ) -> None:
        """更新任务进度。

        Args:
            task_id: 任务 ID
            current: 当前处理数量
            total: 总数量
            message: 进度消息
        """
        if task_id not in self.tasks:
            logger.warning(f"任务不存在: {task_id}")
            return

        task = self.tasks[task_id]
        task.progress.current = current
        task.progress.total = total
        task.progress.message = message
        task.progress.percentage = (current / total * 100) if total > 0 else 0

        await self._notify_callbacks(task_id, task)

    async def start_task(
        self,
        task_id: str,
        coro: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """启动任务执行。

        Args:
            task_id: 任务 ID
            coro: 异步协程函数
            args: 位置参数
            kwargs: 关键字参数
        """
        if task_id not in self.tasks:
            logger.warning(f"任务不存在: {task_id}")
            return

        task = self.tasks[task_id]
        task.status = TaskStatusEnum.RUNNING
        task.started_at = datetime.now()

        await self._notify_callbacks(task_id, task)

        async def run_task() -> None:
            """执行任务。"""
            try:
                result = await coro(*args, **kwargs)
                task.status = TaskStatusEnum.COMPLETED
                task.result = result or {}
                task.completed_at = datetime.now()
                logger.success(f"任务完成: id={task_id}")
            except asyncio.CancelledError:
                task.status = TaskStatusEnum.CANCELLED
                task.completed_at = datetime.now()
                logger.info(f"任务取消: id={task_id}")
            except Exception as e:
                task.status = TaskStatusEnum.FAILED
                task.error = str(e)
                task.completed_at = datetime.now()
                logger.exception(f"任务失败: id={task_id}, error={e}")
            finally:
                await self._notify_callbacks(task_id, task)
                if task_id in self._running_tasks:
                    del self._running_tasks[task_id]

        self._running_tasks[task_id] = asyncio.create_task(run_task())

    def get_task(self, task_id: str) -> TaskInfo | None:
        """获取任务信息。

        Args:
            task_id: 任务 ID

        Returns:
            TaskInfo | None: 任务信息，不存在返回 None
        """
        return self.tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """取消任务。

        Args:
            task_id: 任务 ID

        Returns:
            bool: 是否成功取消
        """
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            return True
        return False

    def list_tasks(
        self,
        status: TaskStatusEnum | None = None,
        limit: int = 100,
    ) -> list[TaskInfo]:
        """列出任务。

        Args:
            status: 过滤状态
            limit: 返回数量限制

        Returns:
            list[TaskInfo]: 任务列表
        """
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    def cleanup_completed_tasks(self, max_age_hours: int = 24) -> int:
        """清理已完成的任务。

        Args:
            max_age_hours: 最大保留时间（小时）

        Returns:
            int: 清理的任务数量
        """
        now = datetime.now()
        to_remove = []

        for task_id, task in self.tasks.items():
            if task.status in [
                TaskStatusEnum.COMPLETED,
                TaskStatusEnum.FAILED,
                TaskStatusEnum.CANCELLED,
            ]:
                if task.completed_at:
                    age_hours = (now - task.completed_at).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        to_remove.append(task_id)

        for task_id in to_remove:
            del self.tasks[task_id]

        if to_remove:
            logger.info(f"清理已完成任务: count={len(to_remove)}")

        return len(to_remove)


# 全局任务管理器实例
task_manager = TaskManager()


__all__ = ["TaskManager", "TaskInfo", "TaskProgress", "TaskStatusEnum", "task_manager"]
