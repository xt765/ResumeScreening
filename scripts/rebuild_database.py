"""数据库重建脚本。

删除并重建所有表。
"""

import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import get_settings
from src.models import Base


async def rebuild_database() -> None:
    """重建数据库表。"""
    settings = get_settings()

    # 创建数据库引擎
    engine = create_async_engine(
        settings.mysql.dsn,
        echo=True,
    )

    async with engine.begin() as conn:
        # 删除所有表
        print("正在删除所有表...")
        await conn.run_sync(Base.metadata.drop_all)
        print("所有表已删除")

        # 创建所有表
        print("正在创建所有表...")
        await conn.run_sync(Base.metadata.create_all)
        print("所有表已创建")

    await engine.dispose()
    print("数据库重建完成！")


if __name__ == "__main__":
    asyncio.run(rebuild_database())
