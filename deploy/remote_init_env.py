"""
远程部署初始化辅助脚本。用于准备或检查远程部署所需环境配置。
"""

from pathlib import Path
import secrets
from typing import Dict
from urllib.parse import quote, urlparse


PROJECT_DIR = Path("/app/rag-java-internal")
SOURCE_ENV = Path("/app/.env")
TARGET_ENV = PROJECT_DIR / ".env"
DEFAULT_DEV_TOKEN = "local-dev-rag-service-token-change-before-production"


def read_env(path: Path) -> Dict[str, str]:
    values = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def resolve_database_url(source: Dict[str, str], current: Dict[str, str]) -> str:
    for values in (current, source):
        for key in ("DATABASE_URL", "RAG_DATABASE_URL", "PYTHON_DATABASE_URL"):
            if values.get(key) and not is_legacy_internal_database_url(values[key]):
                return to_asyncpg_url(values[key])
        for key in ("SPRING_DATASOURCE_URL", "SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL"):
            if values.get(key):
                return jdbc_to_asyncpg_url(
                    values[key],
                    values.get("SPRING_DATASOURCE_USERNAME") or values.get("POSTGRES_USER", "postgres"),
                    values.get("SPRING_DATASOURCE_PASSWORD") or values.get("POSTGRES_PASSWORD", ""),
                )
    host = current.get("POSTGRES_HOST") or source.get("POSTGRES_HOST") or "host.docker.internal"
    port = current.get("POSTGRES_PORT") or source.get("POSTGRES_PORT") or "5432"
    database = current.get("POSTGRES_DB") or source.get("POSTGRES_DB") or "ruoyi-ai"
    username = current.get("POSTGRES_USER") or source.get("POSTGRES_USER") or "postgres"
    password = current.get("POSTGRES_PASSWORD") or source.get("POSTGRES_PASSWORD") or ""
    auth = quote(username, safe="")
    if password:
        auth = f"{auth}:{quote(password, safe='')}"
    return f"postgresql+asyncpg://{auth}@{host}:{port}/{database}"


def is_legacy_internal_database_url(value: str) -> bool:
    parsed = urlparse(value.replace("postgresql+asyncpg://", "postgresql://", 1))
    return (
        parsed.hostname == "postgres"
        and (parsed.port in (None, 5432))
        and parsed.username == "rag"
        and parsed.path.lstrip("/") == "rag"
    )


def resolve_minio_endpoint(source: Dict[str, str], current: Dict[str, str]) -> str:
    for values in (source, current):
        endpoint = values.get("MINIO_ENDPOINT", "")
        if endpoint and endpoint != "minio:9000":
            return normalize_host_endpoint(endpoint)
    return "host.docker.internal:9000"


def normalize_host_endpoint(value: str) -> str:
    endpoint = remove_prefix(remove_prefix(value, "http://"), "https://")
    if endpoint in {"127.0.0.1:9000", "localhost:9000", "0.0.0.0:9000", "minio:9000"}:
        return "host.docker.internal:9000"
    return endpoint


def resolve_minio_value(key: str, source: Dict[str, str], current: Dict[str, str], default: str = "") -> str:
    current_value = current.get(key, "")
    source_value = source.get(key, "")
    if current_value and current_value not in {"minioadmin", "http://47.100.216.222:19004", "http://localhost:9004"}:
        return current_value
    return source_value or current_value or default


def to_asyncpg_url(value: str) -> str:
    if value.startswith("postgresql+asyncpg://"):
        return value
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+asyncpg://", 1)
    if value.startswith("jdbc:postgresql://"):
        return jdbc_to_asyncpg_url(value, "", "")
    return value


def jdbc_to_asyncpg_url(value: str, username: str, password: str) -> str:
    url = remove_prefix(value, "jdbc:")
    parsed = urlparse(url)
    database = parsed.path.lstrip("/")
    auth = quote(username or "postgres", safe="")
    if password:
        auth = f"{auth}:{quote(password, safe='')}"
    return f"postgresql+asyncpg://{auth}@{parsed.hostname}:{parsed.port or 5432}/{database}"


def remove_prefix(value: str, prefix: str) -> str:
    return value[len(prefix) :] if value.startswith(prefix) else value


def main() -> None:
    source = read_env(SOURCE_ENV)
    current = read_env(TARGET_ENV)
    token = current.get("RAG_SERVICE_TOKEN", "")
    if not token or token == DEFAULT_DEV_TOKEN:
        token = secrets.token_urlsafe(32)

    values = {
        "APP_NAME": "Java Internal RAG Service",
        "INTERNAL_API_PREFIX": "/internal/rag",
        "RAG_SERVICE_TOKEN": token,
        "SA_TOKEN_JWT_SECRET": current.get(
            "SA_TOKEN_JWT_SECRET",
            source.get("SA_TOKEN_JWT_SECRET", "change-me"),
        ),
        "SA_TOKEN_JWT_ALGORITHM": current.get("SA_TOKEN_JWT_ALGORITHM", source.get("SA_TOKEN_JWT_ALGORITHM", "HS256")),
        "APP_PUBLIC_BASE_URL": "http://47.100.216.222:18020",
        "DATABASE_URL": resolve_database_url(source, current),
        "REDIS_URL": "redis://redis:6379/0",
        "MINIO_ENDPOINT": resolve_minio_endpoint(source, current),
        "MINIO_ACCESS_KEY": resolve_minio_value("MINIO_ACCESS_KEY", source, current),
        "MINIO_SECRET_KEY": resolve_minio_value("MINIO_SECRET_KEY", source, current),
        "MINIO_SECURE": resolve_minio_value("MINIO_SECURE", source, current, "false"),
        "MINIO_PUBLIC_BASE_URL": resolve_minio_value(
            "MINIO_PUBLIC_BASE_URL",
            source,
            current,
            "http://47.100.216.222:9000",
        ),
        "MINIO_DOCUMENTS_BUCKET": "rag-documents",
        "MINIO_PARSED_BUCKET": "rag-parsed",
        "MINIO_PREVIEW_BUCKET": "rag-preview",
        "DEEPSEEK_API_KEY": source.get("DEEPSEEK_API_KEY", ""),
        "CHAT_MODEL": source.get("CHAT_MODEL", "deepseek-v4-flash"),
        "EMBEDDING_API_KEY": source.get("EMBEDDING_API_KEY", source.get("DEEPSEEK_API_KEY", "")),
        "EMBEDDING_MODEL": source.get("EMBEDDING_MODEL", "text-embedding-v4"),
        "EMBEDDING_DIMENSION": "1024",
        "RERANK_API_KEY": source.get("RERANK_API_KEY", ""),
        "RERANK_MODEL": source.get("RERANK_MODEL", "qwen3-vl-rerank"),
        "RERANK_ENABLED": "true",
        "CHUNK_SIZE": "800",
        "CHUNK_OVERLAP": "120",
        "VECTOR_TOP_K": "30",
        "KEYWORD_TOP_K": "30",
        "QA_TOP_K": "10",
        "RERANK_TOP_K": "5",
        "OCR_ENABLED": "false",
        "OCR_LANG": "ch",
        "OCR_USE_GPU": "false",
        "WEB_CONCURRENCY": "2",
    }
    TARGET_ENV.write_text(
        "\n".join(f"{key}={value}" for key, value in values.items()) + "\n",
        encoding="utf-8",
    )
    TARGET_ENV.chmod(0o600)
    configured = {
        key: bool(values.get(key))
        for key in ("DATABASE_URL", "SA_TOKEN_JWT_SECRET", "DEEPSEEK_API_KEY", "EMBEDDING_API_KEY", "RERANK_API_KEY")
    }
    print(configured)


if __name__ == "__main__":
    main()
