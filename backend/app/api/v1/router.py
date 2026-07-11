"""v1 路由聚合入口：集中挂载认证、文档、问答、检索、评估等业务路由。"""

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
api_router.include_router(files.router)
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(knowledge_bases.router)
api_router.include_router(jobs.router)
api_router.include_router(qa_pairs.router)
api_router.include_router(conversations.router)
api_router.include_router(retrieval.router)
api_router.include_router(chat.router)
api_router.include_router(settings.router)
api_router.include_router(evaluation.router)
api_router.include_router(feedback.router)
