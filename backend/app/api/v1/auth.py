"""
本地管理员认证接口。提供登录和当前用户查询，Java internal API 不依赖该登录流程。
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.responses import ok
from app.core.security import create_access_token, verify_password
from app.db.models import Admin
from app.db.session import get_db


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    admin = await db.scalar(
        select(Admin).where(Admin.username == payload.username, Admin.is_active.is_(True))
    )
    if admin is None or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    await db.execute(
        update(Admin)
        .where(Admin.id == admin.id)
        .values(last_login_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return ok(
        {
            "access_token": create_access_token(str(admin.id)),
            "token_type": "bearer",
            "expires_in": 86400,
            "admin": {
                "id": str(admin.id),
                "username": admin.username,
                "display_name": admin.display_name,
            },
        }
    )


@router.get("/me")
async def me(admin: Admin = Depends(get_current_admin)):
    if not hasattr(admin, "username"):
        return ok(
            {
                "id": str(admin.id),
                "username": getattr(admin, "login_id", str(admin.id)),
                "display_name": getattr(admin, "user_id", str(admin.id)),
                "user_id": getattr(admin, "user_id", str(admin.id)),
                "login_id": getattr(admin, "login_id", str(admin.id)),
            }
        )
    return ok(
        {
            "id": str(admin.id),
            "username": admin.username,
            "display_name": admin.display_name,
        }
    )
