"""清空所有数据库脚本。

清空 MySQL、Redis、MinIO、ChromaDB 中的所有数据。
"""

import asyncio
from pathlib import Path

from loguru import logger

from src.core.config import get_settings
from src.models import Base
from src.storage.chroma_client import ChromaClient
from src.storage.minio_client import MinIOClient
from src.storage.redis_client import RedisClient
from sqlalchemy.ext.asyncio import create_async_engine


async def clear_mysql() -> None:
    """清空 MySQL 数据库。"""
    logger.info("开始清空 MySQL...")
    settings = get_settings()

    engine = create_async_engine(settings.mysql.dsn, echo=False)

    async with engine.begin() as conn:
        # 删除所有表
        await conn.run_sync(Base.metadata.drop_all)
        logger.success("MySQL 表已删除")

        # 重新创建所有表
        await conn.run_sync(Base.metadata.create_all)
        logger.success("MySQL 表已重建")

    await engine.dispose()


async def clear_redis() -> None:
    """清空 Redis 数据库。"""
    logger.info("开始清空 Redis...")
    redis_client = RedisClient()

    # 清空当前数据库
    await redis_client.client.flushdb()
    logger.success("Redis 已清空")

    await redis_client.close()


def clear_minio() -> None:
    """清空 MinIO 存储。"""
    logger.info("开始清空 MinIO...")
    minio_client = MinIOClient()

    bucket_name = minio_client.bucket_name

    # 列出并删除所有对象
    objects = minio_client.client.list_objects(bucket_name, recursive=True)
    for obj in objects:
        minio_client.client.remove_object(bucket_name, obj.object_name)
        logger.debug(f"已删除: {obj.object_name}")

    logger.success("MinIO 已清空")


def clear_chromadb() -> None:
    """清空 ChromaDB 向量数据库。"""
    logger.info("开始清空 ChromaDB...")
    chroma_client = ChromaClient()

    # 删除集合并重新创建
    try:
        chroma_client.client.delete_collection(chroma_client.collection_name)
        logger.success(f"ChromaDB 集合 {chroma_client.collection_name} 已删除")
    except Exception as e:
        logger.warning(f"删除集合时出错: {e}")

    # 重新创建集合
    chroma_client.get_collection(chroma_client.collection_name)
    logger.success("ChromaDB 集合已重建")


async def main() -> None:
    """执行清空所有数据库。"""
    logger.info("=" * 50)
    logger.info("开始清空所有数据库...")
    logger.info("=" * 50)

    # 清空 MySQL
    await clear_mysql()

    # 清空 Redis
    await clear_redis()

    # 清空 MinIO
    clear_minio()

    # 清空 ChromaDB
    clear_chromadb()

    logger.info("=" * 50)
    logger.success("所有数据库已清空完成！")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
