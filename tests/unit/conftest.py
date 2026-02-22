"""单元测试 Pytest 配置文件。

提供单元测试专用的 fixtures，避免导入 API 模块导致的循环导入问题。
"""

import asyncio
import importlib
import os
import sys
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest

# ==================== 事件循环配置 ====================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, Any]:
    """创建会话级别的事件循环。

    Returns:
        异步事件循环实例。
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ==================== 存储测试 Fixtures ====================


@pytest.fixture
def reset_minio_singleton() -> Generator[None, None, None]:
    """重置 MinIO 单例，确保使用真实服务。

    恢复原始的 Minio 类，重置单例实例。
    """
    # 恢复原始的 Minio 类（绕过 conftest.py 中的 mock）
    import minio
    from tests.conftest import _original_minio_class

    minio.Minio = _original_minio_class

    # 重置单例实例
    from src.storage import minio_client

    minio_client.MinIOClient._instance = None
    minio_client.MinIOClient._initialized = False

    # 清除配置缓存
    from src.core import config

    config.get_settings.cache_clear()

    # 重新加载模块以确保使用真实的 Minio 类
    importlib.reload(minio_client)

    yield

    # 测试结束后再次重置
    minio_client.MinIOClient._instance = None
    minio_client.MinIOClient._initialized = False
    config.get_settings.cache_clear()


@pytest.fixture
def reset_redis_singleton() -> Generator[None, None, None]:
    """重置 Redis 单例，确保使用真实服务。

    重置单例实例。
    """
    # 重置单例实例
    from src.storage import redis_client

    redis_client.RedisClient._instance = None
    redis_client.RedisClient._initialized = False

    # 清除配置缓存
    from src.core import config

    config.get_settings.cache_clear()

    yield

    # 测试结束后再次重置
    redis_client.RedisClient._instance = None
    redis_client.RedisClient._initialized = False
    config.get_settings.cache_clear()


@pytest.fixture
def reset_chroma_singleton() -> Generator[None, None, None]:
    """重置 ChromaDB 单例，确保使用真实服务。

    重置单例实例。
    """
    # 重置单例实例
    from src.storage import chroma_client

    chroma_client.ChromaClient._instance = None
    chroma_client.ChromaClient._initialized = False

    # 清除配置缓存
    from src.core import config

    config.get_settings.cache_clear()

    yield

    # 测试结束后再次重置
    chroma_client.ChromaClient._instance = None
    chroma_client.ChromaClient._initialized = False
    config.get_settings.cache_clear()


# ==================== 真实客户端 Fixtures ====================


@pytest.fixture
def real_minio_client(reset_minio_singleton: None) -> Generator[Any, None, None]:
    """创建使用真实服务配置的 MinIO 客户端。

    Args:
        reset_minio_singleton: 重置单例的 fixture

    Yields:
        MinIOClient: 真实的 MinIO 客户端实例
    """
    from src.storage.minio_client import MinIOClient

    client = MinIOClient()
    yield client


@pytest.fixture
def real_redis_client(reset_redis_singleton: None) -> Generator[Any, None, None]:
    """创建使用真实服务配置的 Redis 客户端。

    Args:
        reset_redis_singleton: 重置单例的 fixture

    Yields:
        RedisClient: 真实的 Redis 客户端实例
    """
    from src.storage.redis_client import RedisClient

    client = RedisClient()
    yield client


@pytest.fixture
def real_chroma_client(reset_chroma_singleton: None) -> Generator[Any, None, None]:
    """创建使用真实服务配置的 ChromaDB 客户端。

    Args:
        reset_chroma_singleton: 重置单例的 fixture

    Yields:
        ChromaClient: 真实的 ChromaDB 客户端实例
    """
    from src.storage.chroma_client import ChromaClient

    client = ChromaClient()
    yield client
