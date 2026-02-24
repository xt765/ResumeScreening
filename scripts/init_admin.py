"""初始化管理员账号脚本。

创建默认管理员账号：
- 用户名: xt765
- 密码: 123456
- 邮箱: xt765@foxmail.com

使用方法:
    uv run python scripts/init_admin.py
"""

import asyncio
import sys
import uuid
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import bcrypt
from sqlalchemy import text

from src.core.config import get_settings
from src.models import async_session_factory, init_db, Base, _async_engine

ADMIN_USERNAME = "xt765"
ADMIN_PASSWORD = "123456"
ADMIN_EMAIL = "xt765@foxmail.com"
ADMIN_NICKNAME = "系统管理员"


async def create_user_table() -> None:
    """创建用户表。"""
    from src.models import Base, _async_engine

    if _async_engine is None:
        raise RuntimeError("数据库未初始化")

    async with _async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def init_admin() -> None:
    """初始化管理员账号。"""
    import src.models

    settings = get_settings()

    print("=" * 50)
    print("初始化管理员账号")
    print("=" * 50)

    print(f"\n正在连接数据库: {settings.mysql.host}:{settings.mysql.port}/{settings.mysql.database}")

    init_db(settings.mysql.dsn)

    await create_user_table()

    password_hash = bcrypt.hashpw(
        ADMIN_PASSWORD.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")

    if src.models.async_session_factory is None:
        raise RuntimeError("会话工厂未初始化")

    async with src.models.async_session_factory() as session:
        result = await session.execute(
            text("SELECT id FROM user WHERE username = :username"),
            {"username": ADMIN_USERNAME},
        )
        if result.fetchone():
            print(f"\n管理员账号已存在: {ADMIN_USERNAME}")
            print("删除旧账号并重新创建...")
            await session.execute(
                text("DELETE FROM user WHERE username = :username"),
                {"username": ADMIN_USERNAME},
            )
            # Continue to insert

        # Generate UUID for SQLite compatibility
        user_id = str(uuid.uuid4())
        
        await session.execute(
            text("""
                INSERT INTO user (id, username, email, password_hash, nickname, role, is_first_login, is_active)
                VALUES (:id, :username, :email, :password_hash, :nickname, 'ADMIN', FALSE, TRUE)
            """),
            {
                "id": user_id,
                "username": ADMIN_USERNAME,
                "email": ADMIN_EMAIL,
                "password_hash": password_hash,
                "nickname": ADMIN_NICKNAME,
            },
        )
        await session.commit()

    print("\n" + "=" * 50)
    print("管理员账号创建成功！")
    print("=" * 50)
    print(f"  用户名: {ADMIN_USERNAME}")
    print(f"  密码:   {ADMIN_PASSWORD}")
    print(f"  邮箱:   {ADMIN_EMAIL}")
    print(f"  角色:   admin")
    print("=" * 50)
    print("\n请妥善保管管理员账号信息！")


if __name__ == "__main__":
    asyncio.run(init_admin())
