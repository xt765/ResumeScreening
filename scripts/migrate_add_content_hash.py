"""数据库迁移脚本。

添加 content_hash 字段到 talent_info 表。
"""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.config import get_settings


async def migrate() -> None:
    """执行数据库迁移。"""
    settings = get_settings()
    
    # 创建数据库引擎
    engine = create_async_engine(
        settings.mysql.dsn,
        echo=True,
    )
    
    async_session = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    async with async_session() as session:
        # 检查字段是否已存在
        check_sql = text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'talent_info' 
            AND COLUMN_NAME = 'content_hash'
        """)
        result = await session.execute(check_sql)
        existing = result.fetchone()

        if existing:
            print("content_hash 字段已存在，跳过迁移")
            return

        # 添加 content_hash 字段
        alter_sql = text("""
            ALTER TABLE talent_info 
            ADD COLUMN content_hash VARCHAR(64) NULL 
            COMMENT '简历内容哈希（SHA256，用于去重）' 
            AFTER photo_url
        """)
        await session.execute(alter_sql)

        # 添加索引
        index_sql = text("""
            CREATE INDEX ix_talent_info_content_hash 
            ON talent_info(content_hash)
        """)
        await session.execute(index_sql)

        await session.commit()
        print("迁移完成：已添加 content_hash 字段和索引")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
