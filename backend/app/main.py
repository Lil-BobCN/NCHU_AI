"""FastAPI 应用入口：注册全局中间件、v1 路由和应用关闭时的资源清理。"""

from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.services.model_service import close_model_clients
from app.services.redis_service import close_redis_clients
from app.services.rerank_service import close_rerank_clients


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
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
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    return {"name": settings.app_name, "status": "ok"}
