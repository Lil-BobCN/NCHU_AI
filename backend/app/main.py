"""
FastAPI 应用入口。负责创建应用、配置 CORS、挂载普通 API 与 Java internal API，并在进程退出时关闭外部客户端。
"""

from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import internal
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.services.model_service import close_model_clients
from app.services.redis_service import close_redis_clients
from app.services.rerank_service import close_rerank_clients


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # 进程退出时统一关闭外部连接，避免 HTTP/Redis 客户端连接泄漏。
    for close in (close_rerank_clients, close_model_clients, close_redis_clients):
        with suppress(Exception):
            await close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 普通管理接口和 Java internal 接口分开挂载，避免 Java 对接路径与管理路径混淆。
app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(internal.router, prefix=settings.internal_api_prefix)


@app.get("/")
async def root():
    return {"name": settings.app_name, "status": "ok"}

