import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import Admin
from app.db.session import get_db


security = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: str
    user_id: str
    login_id: str
    tenant_id: str | None = None
    device: str | None = None
    login_type: str | None = None


async def get_current_user_from_sa_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    _: AsyncSession = Depends(get_db),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录，缺少 Authorization Header")

    settings = get_settings()
    if not settings.sa_token_jwt_secret or settings.sa_token_jwt_secret == "change-me":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Sa-Token JWT 密钥未配置")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.sa_token_jwt_secret,
            algorithms=[settings.sa_token_jwt_algorithm],
        )
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token 无效或已过期") from exc

    login_id = str(payload.get("loginId") or "").strip()
    user_id = str(payload.get("userId") or "").strip()
    if not user_id and ":" in login_id:
        user_id = login_id.rsplit(":", 1)[-1].strip()
    if not login_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token payload 缺少 loginId")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token payload 缺少 userId")

    _validate_sa_token_lifetime(payload)
    return CurrentUser(
        id=str(uuid5(NAMESPACE_URL, f"sa-token-user:{login_id}:{user_id}")),
        user_id=user_id,
        login_id=login_id,
        tenant_id=payload.get("tenantId"),
        device=payload.get("device"),
        login_type=payload.get("loginType"),
    )


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Admin | CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录，缺少 Authorization Header")

    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        subject = str(payload.get("sub") or "").strip()
        if subject:
            admin = await db.scalar(
                select(Admin).where(Admin.id == subject, Admin.is_active.is_(True))
            )
            if admin is not None:
                return admin
    except JWTError:
        pass

    return await get_current_user_from_sa_token(credentials, db)


def _validate_sa_token_lifetime(payload: dict) -> None:
    eff = payload.get("eff")
    timeout = payload.get("timeout")
    if eff is None or timeout is None:
        return
    try:
        issued_at = int(eff)
        ttl_seconds = int(timeout)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token 有效期字段格式错误") from exc
    if ttl_seconds < 0:
        return
    settings = get_settings()
    now = int(datetime.now(timezone.utc).timestamp())
    expires_at = issued_at + ttl_seconds + max(0, int(settings.sa_token_clock_skew_seconds))
    if now > expires_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token 已过期")


async def require_internal_service(
    x_rag_service_token: str | None = Header(default=None, alias="X-RAG-Service-Token"),
) -> None:
    settings = get_settings()
    expected = settings.rag_service_token
    if not expected or expected == "change-me":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG 服务 Token 未配置",
        )
    if not x_rag_service_token or not secrets.compare_digest(x_rag_service_token, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="RAG 服务 Token 无效")
