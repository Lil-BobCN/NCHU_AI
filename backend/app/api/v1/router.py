"""
普通 API 路由聚合器。把健康检查、文档、问答、反馈、评测等管理接口统一挂载到 /api/v1。
"""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    chat,
    conversations,
    documents,
    evaluation,
    feedback,
    files,
    health,
    jobs,
    knowledge_bases,
    qa_pairs,
    retrieval,
    settings,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(conversations.router)
api_router.include_router(documents.router)
api_router.include_router(jobs.router)
api_router.include_router(knowledge_bases.router)
api_router.include_router(qa_pairs.router)
api_router.include_router(retrieval.router)
api_router.include_router(feedback.router)
api_router.include_router(settings.router)
api_router.include_router(evaluation.router)
api_router.include_router(files.router)
