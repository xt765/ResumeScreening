"""数据库初始化脚本。

创建数据库和表结构。
"""

import asyncio

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import get_settings
from src.models.base import Base
from src.models import TalentInfo, ScreeningCondition


def create_database() -> None:
    """创建数据库（如果不存在）。"""
    settings = get_settings()

    # 使用同步引擎连接 MySQL（不指定数据库）
    sync_dsn = (
        f"mysql+pymysql://{settings.mysql.user}:{settings.mysql.password}"
        f"@{settings.mysql.host}:{settings.mysql.port}"
    )

    engine = create_engine(sync_dsn, isolation_level="AUTOCOMMIT")

    with engine.connect() as conn:
        # 检查数据库是否存在
        result = conn.execute(
            text(f"SHOW DATABASES LIKE '{settings.mysql.database}'")
        )
        exists = result.fetchone() is not None

        if not exists:
            # 创建数据库
            conn.execute(
                text(f"CREATE DATABASE {settings.mysql.database} "
                     f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            )
            print(f"✅ 数据库 '{settings.mysql.database}' 创建成功")
        else:
            print(f"ℹ️ 数据库 '{settings.mysql.database}' 已存在")

    engine.dispose()


def create_tables() -> None:
    """创建所有表。"""
    settings = get_settings()

    # 使用同步引擎创建表
    sync_dsn = (
        f"mysql+pymysql://{settings.mysql.user}:{settings.mysql.password}"
        f"@{settings.mysql.host}:{settings.mysql.port}/{settings.mysql.database}"
    )

    engine = create_engine(sync_dsn)

    # 创建所有表
    Base.metadata.create_all(engine)
    print("✅ 数据表创建成功")

    # 显示创建的表
    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]
        print(f"📋 当前表: {', '.join(tables)}")

    engine.dispose()


def main() -> None:
    """主函数。"""
    print("🚀 开始初始化数据库...")

    # 创建数据库
    create_database()

    # 创建表
    create_tables()

    print("\n✨ 数据库初始化完成！")


if __name__ == "__main__":
    main()
