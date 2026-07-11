"""管理员初始化脚本：根据环境变量创建首个后台管理员账号。"""

import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models import Admin
from app.db.session import AsyncSessionLocal


async def main() -> None:
    settings = get_settings()
    async with AsyncSessionLocal() as db:
        admin = await db.scalar(select(Admin).where(Admin.username == settings.admin_username))
        if admin:
            return
        db.add(
            Admin(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
                display_name="管理员",
            )
        )
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
