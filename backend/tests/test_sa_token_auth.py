from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import unittest

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api import deps  # noqa: E402
from app.core.config import get_settings  # noqa: E402


class SaTokenAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_secret = os.environ.get("SA_TOKEN_JWT_SECRET")
        os.environ["SA_TOKEN_JWT_SECRET"] = "unit-test-secret"
        get_settings.cache_clear()

    def tearDown(self) -> None:
        if self.previous_secret is None:
            os.environ.pop("SA_TOKEN_JWT_SECRET", None)
        else:
            os.environ["SA_TOKEN_JWT_SECRET"] = self.previous_secret
        get_settings.cache_clear()

    def test_sa_token_payload_is_accepted(self) -> None:
        token = self._token(timeout=604800)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        user = asyncio.run(deps.get_current_user_from_sa_token(credentials, None))

        self.assertNotEqual(user.id, "1")
        self.assertEqual(user.user_id, "1")
        self.assertEqual(user.login_id, "sys_user:1")
        self.assertEqual(user.tenant_id, "000000")

    def test_expired_sa_token_is_rejected(self) -> None:
        token = self._token(eff=1, timeout=1)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(deps.get_current_user_from_sa_token(credentials, None))

        self.assertEqual(ctx.exception.status_code, 401)

    def _token(self, eff: int | None = None, timeout: int = 604800) -> str:
        now = int(datetime.now(timezone.utc).timestamp())
        payload = {
            "loginId": "sys_user:1",
            "loginType": "login",
            "device": "PC",
            "tenantId": "000000",
            "userId": "1",
            "eff": now if eff is None else eff,
            "timeout": timeout,
        }
        return jwt.encode(payload, "unit-test-secret", algorithm="HS256")


if __name__ == "__main__":
    unittest.main()
