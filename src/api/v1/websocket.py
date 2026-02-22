"""WebSocket 端点模块。

提供实时通信功能：
- 任务进度推送
- 连接管理
"""

import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from src.core.tasks import TaskInfo, TaskStatusEnum, task_manager

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """WebSocket 连接管理器。

    管理所有活跃的 WebSocket 连接。

    Attributes:
        active_connections: 活跃连接列表
    """

    def __init__(self) -> None:
        """初始化连接管理器。"""
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """接受新连接。

        Args:
            websocket: WebSocket 连接实例
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket 连接建立，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """断开连接。

        Args:
            websocket: WebSocket 连接实例
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket 连接断开，当前连接数: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        """发送个人消息。

        Args:
            message: 消息内容
            websocket: 目标 WebSocket 连接
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"发送消息失败: {e}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        """广播消息到所有连接。

        Args:
            message: 消息内容
        """
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"广播消息失败: {e}")

    async def send_task_update(self, task_id: str, task_info: TaskInfo) -> None:
        """发送任务更新消息。

        Args:
            task_id: 任务 ID
            task_info: 任务信息
        """
        message = {
            "type": "task_update",
            "task_id": task_id,
            "data": task_info.to_dict(),
        }
        await self.broadcast(message)


# 全局连接管理器
manager = ConnectionManager()


async def task_callback(task_id: str, task_info: TaskInfo) -> None:
    """任务更新回调函数。

    当任务状态或进度更新时，通过 WebSocket 推送消息。

    Args:
        task_id: 任务 ID
        task_info: 任务信息
    """
    await manager.send_task_update(task_id, task_info)


# 注册任务回调
task_manager.register_callback(task_callback)


@router.websocket("/ws/tasks")
async def websocket_tasks(websocket: WebSocket) -> None:
    """任务进度 WebSocket 端点。

    客户端连接后可接收任务进度更新。

    消息格式:
        {
            "type": "task_update",
            "task_id": "xxx",
            "data": { ... }
        }

    客户端可发送:
        - {"type": "subscribe", "task_id": "xxx"} - 订阅特定任务
        - {"type": "unsubscribe", "task_id": "xxx"} - 取消订阅
        - {"type": "ping"} - 心跳检测
    """
    await manager.connect(websocket)
    subscribed_tasks: set[str] = set()

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

                elif msg_type == "subscribe":
                    task_id = message.get("task_id")
                    if task_id:
                        subscribed_tasks.add(task_id)
                        task = await task_manager.get_task(task_id)
                        if task:
                            await manager.send_personal_message(
                                {"type": "task_update", "task_id": task_id, "data": task.to_dict()},
                                websocket,
                            )
                        await websocket.send_json({"type": "subscribed", "task_id": task_id})

                elif msg_type == "unsubscribe":
                    task_id = message.get("task_id")
                    if task_id and task_id in subscribed_tasks:
                        subscribed_tasks.remove(task_id)
                        await websocket.send_json({"type": "unsubscribed", "task_id": task_id})

                elif msg_type == "list_tasks":
                    from contextlib import suppress

                    status_filter = message.get("status")
                    status_enum = None
                    if status_filter:
                        with suppress(ValueError):
                            status_enum = TaskStatusEnum(status_filter)
                    tasks = await task_manager.list_tasks(status=status_enum)
                    await websocket.send_json(
                        {
                            "type": "task_list",
                            "data": [t.to_dict() for t in tasks],
                        }
                    )

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "无效的 JSON 格式"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.exception(f"WebSocket 异常: {e}")
        manager.disconnect(websocket)


__all__ = ["manager", "router"]
