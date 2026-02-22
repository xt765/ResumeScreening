"""Redis 客户端封装模块。

提供异步缓存功能，包括字符串和 JSON 数据的缓存操作。
使用单例模式确保全局只有一个客户端实例。
"""

import json
from typing import Any

from loguru import logger
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError

from src.core.config import get_settings


class RedisClient:
    """Redis 客户端单例类。

    封装 Redis 异步操作，提供缓存功能。

    Attributes:
        _instance: 单例实例
        _initialized: 是否已初始化标志
        client: Redis 异步客户端实例
    """

    _instance: "RedisClient | None" = None
    _initialized: bool = False

    def __new__(cls) -> "RedisClient":
        """创建或返回单例实例。

        Returns:
            RedisClient: 单例实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化 Redis 客户端。

        从配置中读取连接信息并创建异步客户端实例。
        """
        if self._initialized:
            return

        settings = get_settings()
        self._host = settings.redis.host
        self._port = settings.redis.port
        self._password = settings.redis.password
        self._db = settings.redis.db

        logger.info(f"初始化 Redis 客户端: host={self._host}, port={self._port}, db={self._db}")

        # 创建连接池
        self._pool = ConnectionPool(
            host=self._host,
            port=self._port,
            password=self._password,
            db=self._db,
            decode_responses=True,
            max_connections=10,
        )

        self.client = Redis(connection_pool=self._pool)
        RedisClient._initialized = True

    async def test_connection(self) -> bool:
        """测试 Redis 连接是否正常。

        Returns:
            bool: 连接成功返回 True，否则返回 False
        """
        try:
            await self.client.ping()  # type: ignore[union-attr]
            logger.info("Redis 连接测试成功")
            return True
        except RedisError as e:
            logger.error(f"Redis 连接测试失败: {e}")
            return False

    async def set_cache(
        self,
        key: str,
        value: str,
        expire: int | None = None,
    ) -> bool:
        """设置字符串缓存。

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒），None 表示永不过期

        Returns:
            bool: 设置成功返回 True

        Raises:
            RedisError: Redis 操作错误
        """
        try:
            await self.client.set(key, value, ex=expire)
            logger.debug(f"设置缓存成功: key={key}, expire={expire}")
            return True
        except RedisError as e:
            logger.exception(f"设置缓存失败: key={key}, 错误: {e}")
            raise

    async def get_cache(self, key: str) -> str | None:
        """获取字符串缓存。

        Args:
            key: 缓存键

        Returns:
            str | None: 缓存值，不存在返回 None

        Raises:
            RedisError: Redis 操作错误
        """
        try:
            value = await self.client.get(key)
            if value is not None:
                logger.debug(f"获取缓存成功: key={key}")
            else:
                logger.debug(f"缓存不存在: key={key}")
            return value
        except RedisError as e:
            logger.exception(f"获取缓存失败: key={key}, 错误: {e}")
            raise

    async def delete_cache(self, key: str) -> bool:
        """删除缓存。

        Args:
            key: 缓存键

        Returns:
            bool: 删除成功返回 True

        Raises:
            RedisError: Redis 操作错误
        """
        try:
            await self.client.delete(key)
            logger.debug(f"删除缓存成功: key={key}")
            return True
        except RedisError as e:
            logger.exception(f"删除缓存失败: key={key}, 错误: {e}")
            raise

    async def set_json(
        self,
        key: str,
        value: dict[str, Any] | list[Any],
        expire: int | None = None,
    ) -> bool:
        """设置 JSON 缓存。

        Args:
            key: 缓存键
            value: 缓存值（字典或列表）
            expire: 过期时间（秒），None 表示永不过期

        Returns:
            bool: 设置成功返回 True

        Raises:
            RedisError: Redis 操作错误
        """
        try:
            json_str = json.dumps(value, ensure_ascii=False)
            await self.client.set(key, json_str, ex=expire)
            logger.debug(f"设置 JSON 缓存成功: key={key}, expire={expire}")
            return True
        except RedisError as e:
            logger.exception(f"设置 JSON 缓存失败: key={key}, 错误: {e}")
            raise

    async def get_json(
        self,
        key: str,
    ) -> dict[str, Any] | list[Any] | None:
        """获取 JSON 缓存。

        Args:
            key: 缓存键

        Returns:
            dict | list | None: 缓存值，不存在返回 None

        Raises:
            RedisError: Redis 操作错误
        """
        try:
            value = await self.client.get(key)
            if value is None:
                logger.debug(f"JSON 缓存不存在: key={key}")
                return None

            result = json.loads(value)
            logger.debug(f"获取 JSON 缓存成功: key={key}")
            return result
        except RedisError as e:
            logger.exception(f"获取 JSON 缓存失败: key={key}, 错误: {e}")
            raise

    async def exists(self, key: str) -> bool:
        """检查缓存键是否存在。

        Args:
            key: 缓存键

        Returns:
            bool: 存在返回 True，否则返回 False
        """
        try:
            result = await self.client.exists(key)
            return result > 0
        except RedisError as e:
            logger.exception(f"检查缓存键存在失败: key={key}, 错误: {e}")
            raise

    async def set_expire(self, key: str, expire: int) -> bool:
        """设置缓存过期时间。

        Args:
            key: 缓存键
            expire: 过期时间（秒）

        Returns:
            bool: 设置成功返回 True
        """
        try:
            result = await self.client.expire(key, expire)
            return result
        except RedisError as e:
            logger.exception(f"设置过期时间失败: key={key}, 错误: {e}")
            raise

    async def get_ttl(self, key: str) -> int:
        """获取缓存剩余过期时间。

        Args:
            key: 缓存键

        Returns:
            int: 剩余秒数，-1 表示永不过期，-2 表示不存在
        """
        try:
            ttl = await self.client.ttl(key)
            return ttl
        except RedisError as e:
            logger.exception(f"获取 TTL 失败: key={key}, 错误: {e}")
            raise

    async def close(self) -> None:
        """关闭 Redis 连接。

        释放连接池资源。
        """
        try:
            await self.client.close()
            await self._pool.disconnect()
            logger.info("Redis 连接已关闭")
        except RedisError as e:
            logger.exception(f"关闭 Redis 连接失败: {e}")

    async def rpush(self, key: str, value: str) -> int:
        """向列表右侧添加元素。

        Args:
            key: 列表键名。
            value: 要添加的值。

        Returns:
            int: 列表长度。

        Raises:
            RedisError: Redis 操作错误。
        """
        try:
            result = await self.client.rpush(key, value)
            logger.debug(f"RPUSH 成功: key={key}")
            return result
        except RedisError as e:
            logger.exception(f"RPUSH 失败: key={key}, 错误: {e}")
            raise

    async def lpop(self, key: str) -> str | None:
        """从列表左侧弹出元素。

        Args:
            key: 列表键名。

        Returns:
            str | None: 弹出的值，列表为空返回 None。

        Raises:
            RedisError: Redis 操作错误。
        """
        try:
            result = await self.client.lpop(key)
            logger.debug(f"LPOP 成功: key={key}")
            return result
        except RedisError as e:
            logger.exception(f"LPOP 失败: key={key}, 错误: {e}")
            raise

    async def lrange(self, key: str, start: int, stop: int) -> list[str]:
        """获取列表范围内的元素。

        Args:
            key: 列表键名。
            start: 起始索引。
            stop: 结束索引（-1 表示最后一个元素）。

        Returns:
            list[str]: 元素列表。

        Raises:
            RedisError: Redis 操作错误。
        """
        try:
            result = await self.client.lrange(key, start, stop)
            logger.debug(f"LRANGE 成功: key={key}, start={start}, stop={stop}")
            return result
        except RedisError as e:
            logger.exception(f"LRANGE 失败: key={key}, 错误: {e}")
            raise

    async def llen(self, key: str) -> int:
        """获取列表长度。

        Args:
            key: 列表键名。

        Returns:
            int: 列表长度。

        Raises:
            RedisError: Redis 操作错误。
        """
        try:
            result = await self.client.llen(key)
            logger.debug(f"LLEN 成功: key={key}, len={result}")
            return result
        except RedisError as e:
            logger.exception(f"LLEN 失败: key={key}, 错误: {e}")
            raise

    async def expire(self, key: str, seconds: int) -> bool:
        """设置键的过期时间。

        Args:
            key: 键名。
            seconds: 过期时间（秒）。

        Returns:
            bool: 设置成功返回 True。

        Raises:
            RedisError: Redis 操作错误。
        """
        try:
            result = await self.client.expire(key, seconds)
            logger.debug(f"EXPIRE 成功: key={key}, seconds={seconds}")
            return result
        except RedisError as e:
            logger.exception(f"EXPIRE 失败: key={key}, 错误: {e}")
            raise

    async def keys(self, pattern: str) -> list[str]:
        """查找匹配模式的所有键。

        Args:
            pattern: 匹配模式（如 "task:*"）。

        Returns:
            list[str]: 匹配的键列表。

        Raises:
            RedisError: Redis 操作错误。
        """
        try:
            result = await self.client.keys(pattern)
            logger.debug(f"KEYS 成功: pattern={pattern}, count={len(result)}")
            return result
        except RedisError as e:
            logger.exception(f"KEYS 失败: pattern={pattern}, 错误: {e}")
            raise


# 创建全局单例实例
redis_client = RedisClient()
