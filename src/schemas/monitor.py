"""监控模块数据模型定义。

提供系统监控相关的数据模型：
- 日志查询模型
- 系统健康状态模型
- 资源指标模型
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """日志条目模型。

    表示单条日志记录的完整信息。

    Attributes:
        timestamp: 日志时间戳。
        level: 日志级别。
        message: 日志消息内容。
        module: 产生日志的模块名。
        function: 产生日志的函数名。
        line: 产生日志的代码行号。
        process_id: 进程 ID。
        thread_id: 线程 ID。
        extra: 额外的上下文信息。
        exception: 异常信息（如果有）。
    """

    timestamp: datetime = Field(..., description="日志时间戳")
    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息内容")
    module: str = Field(..., description="产生日志的模块名")
    function: str = Field(..., description="产生日志的函数名")
    line: int = Field(..., description="产生日志的代码行号")
    process_id: int = Field(..., description="进程 ID")
    thread_id: int = Field(..., description="线程 ID")
    extra: dict[str, Any] | None = Field(default=None, description="额外的上下文信息")
    exception: dict[str, Any] | None = Field(default=None, description="异常信息")


class LogQueryParams(BaseModel):
    """日志查询参数模型。

    用于日志查询接口的参数验证。

    Attributes:
        start_time: 开始时间。
        end_time: 结束时间。
        levels: 日志级别列表。
        keyword: 搜索关键词。
        page: 页码（从 1 开始）。
        page_size: 每页记录数。
    """

    start_time: datetime | None = Field(default=None, description="开始时间")
    end_time: datetime | None = Field(default=None, description="结束时间")
    levels: list[str] | None = Field(default=None, description="日志级别列表")
    keyword: str | None = Field(default=None, description="搜索关键词")
    page: int = Field(default=1, ge=1, description="页码（从 1 开始）")
    page_size: int = Field(default=50, ge=1, le=200, description="每页记录数")


class ServiceStatus(BaseModel):
    """服务状态模型。

    表示单个服务的健康状态。

    Attributes:
        name: 服务名称。
        status: 服务状态（healthy/unhealthy/degraded）。
        latency_ms: 响应延迟（毫秒）。
        message: 状态消息。
        details: 详细信息。
    """

    name: str = Field(..., description="服务名称")
    status: Literal["healthy", "unhealthy", "degraded"] = Field(..., description="服务状态")
    latency_ms: float | None = Field(default=None, description="响应延迟（毫秒）")
    message: str | None = Field(default=None, description="状态消息")
    details: dict[str, Any] | None = Field(default=None, description="详细信息")


class ResourceUsage(BaseModel):
    """资源使用率模型。

    表示系统资源的使用情况。

    Attributes:
        cpu_percent: CPU 使用率百分比。
        memory_percent: 内存使用率百分比。
        memory_used_gb: 已使用内存（GB）。
        memory_total_gb: 总内存（GB）。
        disk_percent: 磁盘使用率百分比。
        disk_used_gb: 已使用磁盘（GB）。
        disk_total_gb: 总磁盘（GB）。
    """

    cpu_percent: float = Field(..., ge=0, le=100, description="CPU 使用率百分比")
    memory_percent: float = Field(..., ge=0, le=100, description="内存使用率百分比")
    memory_used_gb: float = Field(..., ge=0, description="已使用内存（GB）")
    memory_total_gb: float = Field(..., ge=0, description="总内存（GB）")
    disk_percent: float = Field(..., ge=0, le=100, description="磁盘使用率百分比")
    disk_used_gb: float = Field(..., ge=0, description="已使用磁盘（GB）")
    disk_total_gb: float = Field(..., ge=0, description="总磁盘（GB）")


class SystemHealth(BaseModel):
    """系统健康状态模型。

    表示整个系统的健康状态概览。

    Attributes:
        status: 整体状态（healthy/unhealthy/degraded）。
        services: 各服务状态列表。
        resources: 资源使用情况。
        uptime_seconds: 系统运行时间（秒）。
        last_check: 最后检查时间。
    """

    status: Literal["healthy", "unhealthy", "degraded"] = Field(..., description="整体状态")
    services: list[ServiceStatus] = Field(..., description="各服务状态列表")
    resources: ResourceUsage = Field(..., description="资源使用情况")
    uptime_seconds: int = Field(..., ge=0, description="系统运行时间（秒）")
    last_check: datetime = Field(..., description="最后检查时间")


class MetricPoint(BaseModel):
    """指标数据点模型。

    表示某个时间点的资源指标。

    Attributes:
        timestamp: 时间戳。
        cpu_percent: CPU 使用率。
        memory_percent: 内存使用率。
        disk_percent: 磁盘使用率。
    """

    timestamp: datetime = Field(..., description="时间戳")
    cpu_percent: float = Field(..., ge=0, le=100, description="CPU 使用率")
    memory_percent: float = Field(..., ge=0, le=100, description="内存使用率")
    disk_percent: float = Field(..., ge=0, le=100, description="磁盘使用率")


__all__ = [
    "LogEntry",
    "LogQueryParams",
    "MetricPoint",
    "ResourceUsage",
    "ServiceStatus",
    "SystemHealth",
]
