"""迁移 Viewer 用户为 HR 角色。

将所有 viewer 角色的用户更新为 hr 角色。
"""

import asyncio

from sqlalchemy import text

import src.models as models
from src.core.config import get_settings


async def migrate_viewer_to_hr():
    """将所有 viewer 用户迁移为 hr 角色。"""
    settings = get_settings()
    models.init_db(settings.mysql.dsn)

    async with models.async_session_factory() as session:
        # 检查 viewer 用户数量
        result = await session.execute(
            text("SELECT COUNT(*) FROM user WHERE role = 'viewer'")
        )
        count = result.scalar()
        print(f"发现 {count} 个 Viewer 用户")

        if count > 0:
            # 更新 viewer 用户为 hr
            await session.execute(
                text("UPDATE user SET role = 'hr' WHERE role = 'viewer'")
            )
            await session.commit()
            print(f"已将 {count} 个 Viewer 用户迁移为 HR 角色")
        else:
            print("无需迁移")


if __name__ == "__main__":
    asyncio.run(migrate_viewer_to_hr())
