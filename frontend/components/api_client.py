"""API 请求客户端模块。

提供与后端 FastAPI 服务交互的 HTTP 客户端封装，支持异步请求、
自动重试、超时处理和完善的错误处理机制。
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
import os
from typing import Any

import httpx
from loguru import logger
import streamlit as st


class APIError(Exception):
    """API 错误异常类。

    用于封装 API 请求过程中的各类错误信息。

    Attributes:
        status_code: HTTP 状态码
        message: 错误消息
        detail: 详细错误信息
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        detail: str | None = None,
    ) -> None:
        """初始化 API 错误。

        Args:
            message: 错误消息
            status_code: HTTP 状态码
            detail: 详细错误信息
        """
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail
        self.message = message


class RetryStrategy(Enum):
    """重试策略枚举。"""

    NONE = "none"  # 不重试
    LINEAR = "linear"  # 线性重试
    EXPONENTIAL = "exponential"  # 指数退避重试


@dataclass
class RetryConfig:
    """重试配置类。

    Attributes:
        max_retries: 最大重试次数
        strategy: 重试策略
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        retryable_status_codes: 可重试的状态码列表
    """

    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay: float = 1.0
    max_delay: float = 30.0
    retryable_status_codes: tuple[int, ...] = (408, 429, 500, 502, 503, 504)


class APIClient:
    """API 请求客户端类。

    封装所有与后端 API 的交互逻辑，提供统一的请求方法，
    支持自动重试、超时处理和完善的错误处理。

    Attributes:
        base_url: API 基础地址
        timeout: 请求超时时间
        retry_config: 重试配置
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """初始化 API 客户端。

        Args:
            base_url: API 基础地址，默认从环境变量 API_BASE_URL 读取
            timeout: 请求超时时间（秒）
            retry_config: 重试配置
        """
        self.base_url = base_url or os.getenv("API_BASE_URL", "http://localhost:8000")
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self._client: httpx.AsyncClient | None = None

    def _get_headers(self) -> dict[str, str]:
        """获取请求头。

        Returns:
            请求头字典
        """
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _calculate_delay(self, attempt: int) -> float:
        """计算重试延迟时间。

        Args:
            attempt: 当前重试次数

        Returns:
            延迟时间（秒）
        """
        if self.retry_config.strategy == RetryStrategy.LINEAR:
            delay = self.retry_config.base_delay * attempt
        elif self.retry_config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.retry_config.base_delay * (2 ** (attempt - 1))
        else:
            delay = 0

        return min(delay, self.retry_config.max_delay)

    async def _execute_with_retry(
        self,
        request_func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """执行请求并支持自动重试。

        Args:
            request_func: 请求函数
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            响应数据

        Raises:
            APIError: API 请求失败
        """
        last_error: Exception | None = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                response = await request_func(*args, **kwargs)
                return self._handle_response(response)
            except APIError as e:
                last_error = e

                # 检查是否应该重试
                if (
                    e.status_code in self.retry_config.retryable_status_codes
                    and attempt < self.retry_config.max_retries
                ):
                    delay = self._calculate_delay(attempt + 1)
                    logger.warning(
                        f"API 请求失败，{delay:.1f}秒后重试 "
                        f"(尝试 {attempt + 1}/{self.retry_config.max_retries}): {e.message}"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise last_error from None
            except httpx.TimeoutException as e:
                last_error = APIError("请求超时，请检查网络连接", detail=str(e))
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_delay(attempt + 1)
                    logger.warning(
                        f"请求超时，{delay:.1f}秒后重试 "
                        f"(尝试 {attempt + 1}/{self.retry_config.max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise last_error from None
            except httpx.ConnectError as e:
                last_error = APIError(
                    "无法连接到服务器，请确认 API 服务是否正常运行",
                    detail=str(e),
                )
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_delay(attempt + 1)
                    logger.warning(
                        f"连接失败，{delay:.1f}秒后重试 "
                        f"(尝试 {attempt + 1}/{self.retry_config.max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise last_error from None
            except Exception as e:
                last_error = APIError(f"请求发生未知错误: {e}", detail=str(e))
                raise last_error from None

        raise last_error or APIError("请求失败")

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """处理响应结果。

        Args:
            response: HTTP 响应对象

        Returns:
            解析后的响应数据

        Raises:
            APIError: 请求失败时抛出异常
        """
        if response.status_code >= 400:
            error_detail = "请求失败"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", error_detail)
            except Exception:
                error_detail = response.text or error_detail

            logger.error(f"API 错误 ({response.status_code}): {error_detail}")
            raise APIError(
                f"API 错误 ({response.status_code}): {error_detail}",
                status_code=response.status_code,
                detail=error_detail,
            )

        try:
            return response.json()
        except Exception:
            return {"raw": response.text}

    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """发送 GET 请求。

        Args:
            endpoint: API 端点路径
            params: 查询参数

        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"

        async def _request() -> httpx.Response:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                return await client.get(
                    url,
                    params=params,
                    headers=self._get_headers(),
                )

        return await self._execute_with_retry(_request)

    async def post(
        self,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """发送 POST 请求。

        Args:
            endpoint: API 端点路径
            json_data: JSON 请求体
            data: 表单数据

        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"

        async def _request() -> httpx.Response:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                return await client.post(
                    url,
                    json=json_data,
                    data=data,
                    headers=self._get_headers(),
                )

        return await self._execute_with_retry(_request)

    async def put(
        self,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """发送 PUT 请求。

        Args:
            endpoint: API 端点路径
            json_data: JSON 请求体

        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"

        async def _request() -> httpx.Response:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                return await client.put(
                    url,
                    json=json_data,
                    headers=self._get_headers(),
                )

        return await self._execute_with_retry(_request)

    async def delete(self, endpoint: str) -> dict[str, Any]:
        """发送 DELETE 请求。

        Args:
            endpoint: API 端点路径

        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"

        async def _request() -> httpx.Response:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                return await client.delete(
                    url,
                    headers=self._get_headers(),
                )

        return await self._execute_with_retry(_request)

    async def upload_file(
        self,
        endpoint: str,
        file_content: bytes,
        filename: str,
        additional_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """上传文件。

        Args:
            endpoint: API 端点路径
            file_content: 文件内容
            filename: 文件名
            additional_data: 额外的表单数据

        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"
        files = {"file": (filename, file_content)}

        async def _request() -> httpx.Response:
            async with httpx.AsyncClient(timeout=self.timeout * 2) as client:
                return await client.post(
                    url,
                    files=files,
                    data=additional_data,
                )

        return await self._execute_with_retry(_request)


class ConditionAPI:
    """筛选条件 API 类。

    提供筛选条件相关的 API 操作。
    """

    def __init__(self, client: APIClient) -> None:
        """初始化筛选条件 API。

        Args:
            client: API 客户端实例
        """
        self.client = client
        self.prefix = "/api/v1/conditions"

    async def list(
        self,
        name: str | None = None,
        statuses: list[str] | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """获取筛选条件列表。

        Args:
            name: 条件名称（模糊匹配）
            statuses: 状态列表
            page: 页码
            page_size: 每页数量

        Returns:
            分页数据
        """
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if name:
            params["name"] = name
        if statuses:
            params["statuses"] = statuses
        return await self.client.get(self.prefix, params=params)

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """创建筛选条件。

        Args:
            data: 筛选条件数据

        Returns:
            创建结果
        """
        return await self.client.post(self.prefix, json_data=data)

    async def update(self, condition_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """更新筛选条件。

        Args:
            condition_id: 条件 ID
            data: 更新数据

        Returns:
            更新结果
        """
        return await self.client.put(f"{self.prefix}/{condition_id}", json_data=data)

    async def delete(self, condition_id: str) -> dict[str, Any]:
        """删除筛选条件。

        Args:
            condition_id: 条件 ID

        Returns:
            删除结果
        """
        return await self.client.delete(f"{self.prefix}/{condition_id}")


class TalentAPI:
    """人才管理 API 类。

    提供人才相关的 API 操作。
    """

    def __init__(self, client: APIClient) -> None:
        """初始化人才 API。

        Args:
            client: API 客户端实例
        """
        self.client = client
        self.prefix = "/api/v1/talents"

    async def list(
        self,
        name: str | None = None,
        major: str | None = None,
        school: str | None = None,
        screening_date_start: str | None = None,
        screening_date_end: str | None = None,
        screening_status: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """获取人才列表。

        Args:
            name: 姓名（模糊匹配）
            major: 专业（模糊匹配）
            school: 院校（模糊匹配）
            screening_date_start: 选拔日期起始
            screening_date_end: 选拔日期截止
            screening_status: 筛选状态
            page: 页码
            page_size: 每页数量

        Returns:
            分页数据
        """
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if name:
            params["name"] = name
        if major:
            params["major"] = major
        if school:
            params["school"] = school
        if screening_date_start:
            params["screening_date_start"] = screening_date_start
        if screening_date_end:
            params["screening_date_end"] = screening_date_end
        if screening_status:
            params["screening_status"] = screening_status
        return await self.client.get(self.prefix, params=params)

    async def get(self, talent_id: str) -> dict[str, Any]:
        """获取人才详情。

        Args:
            talent_id: 人才 ID

        Returns:
            人才详情
        """
        return await self.client.get(f"{self.prefix}/{talent_id}")

    async def upload_screen(
        self,
        file_content: bytes,
        filename: str,
        condition_id: str | None = None,
    ) -> dict[str, Any]:
        """上传简历并执行智能筛选。

        Args:
            file_content: 文件内容
            filename: 文件名
            condition_id: 筛选条件 ID

        Returns:
            筛选结果
        """
        additional_data: dict[str, Any] = {}
        if condition_id:
            additional_data["condition_id"] = condition_id
        return await self.client.upload_file(
            f"{self.prefix}/upload-screen",
            file_content,
            filename,
            additional_data,
        )

    async def vectorize(self, talent_id: str) -> dict[str, Any]:
        """向量化指定人才。

        Args:
            talent_id: 人才 ID

        Returns:
            向量化结果
        """
        return await self.client.post(f"{self.prefix}/{talent_id}/vectorize")

    async def batch_vectorize(
        self,
        screening_status: str = "qualified",
        limit: int = 100,
    ) -> dict[str, Any]:
        """批量向量化人才。

        Args:
            screening_status: 筛选状态
            limit: 批量处理数量上限

        Returns:
            批量向量化结果
        """
        params = {"screening_status": screening_status, "limit": limit}
        return await self.client.post(f"{self.prefix}/batch-vectorize", json_data=params)


class AnalysisAPI:
    """数据分析 API 类。

    提供数据分析相关的 API 操作。
    """

    def __init__(self, client: APIClient) -> None:
        """初始化分析 API。

        Args:
            client: API 客户端实例
        """
        self.client = client
        self.prefix = "/api/v1/analysis"

    async def query(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """执行 RAG 智能查询。

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 元数据过滤条件

        Returns:
            查询结果
        """
        data: dict[str, Any] = {"query": query, "top_k": top_k}
        if filters:
            data["filters"] = filters
        return await self.client.post(f"{self.prefix}/query", json_data=data)

    async def statistics(self) -> dict[str, Any]:
        """获取统计数据。

        Returns:
            统计数据
        """
        return await self.client.get(f"{self.prefix}/statistics")


# 创建全局 API 客户端实例
@st.cache_resource
def get_api_client() -> APIClient:
    """获取 API 客户端实例（带缓存）。

    Returns:
        API 客户端实例
    """
    retry_config = RetryConfig(
        max_retries=3,
        strategy=RetryStrategy.EXPONENTIAL,
        base_delay=1.0,
        max_delay=30.0,
    )
    return APIClient(retry_config=retry_config)


def get_condition_api() -> ConditionAPI:
    """获取筛选条件 API 实例。

    Returns:
        筛选条件 API 实例
    """
    return ConditionAPI(get_api_client())


def get_talent_api() -> TalentAPI:
    """获取人才 API 实例。

    Returns:
        人才 API 实例
    """
    return TalentAPI(get_api_client())


def get_analysis_api() -> AnalysisAPI:
    """获取分析 API 实例。

    Returns:
        分析 API 实例
    """
    return AnalysisAPI(get_api_client())


__all__ = [
    "APIClient",
    "APIError",
    "AnalysisAPI",
    "ConditionAPI",
    "RetryConfig",
    "RetryStrategy",
    "TalentAPI",
    "get_analysis_api",
    "get_api_client",
    "get_condition_api",
    "get_talent_api",
]
