import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path
import urllib.error
import urllib.request


ENV_PATH = Path("/app/rag-java-internal/.env")


def read_env():
    values = {}
    for raw in ENV_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" not in raw or raw.strip().startswith("#"):
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def make_health_jwt(secret):
    now = int(datetime.now(timezone.utc).timestamp())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "loginId": "sys_user:0",
        "loginType": "login",
        "device": "SERVER",
        "tenantId": "000000",
        "userId": "0",
        "eff": now,
        "timeout": 300,
    }
    signing_input = "{}.{}".format(b64_json(header), b64_json(payload))
    signature = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return "{}.{}".format(signing_input, b64(signature))


def b64_json(value):
    return b64(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def b64(value):
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def main() -> None:
    env = read_env()
    secret = env.get("SA_TOKEN_JWT_SECRET", "")
    if not secret or secret == "change-me":
        raise RuntimeError("SA_TOKEN_JWT_SECRET is not configured")
    token = env.get("SA_TOKEN_HEALTH_JWT") or make_health_jwt(secret)
    request = urllib.request.Request(
        "http://127.0.0.1:18020/internal/rag/health",
        headers={"Authorization": "Bearer {}".format(token)},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            print(response.status)
            print(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(exc.code)
        print(exc.read().decode("utf-8"))


if __name__ == "__main__":
    main()
