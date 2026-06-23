from fastapi import APIRouter

from app.api.v1 import auth, chat, conversations, documents, evaluation, files, health, jobs, qa_pairs, retrieval, settings


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(files.router)
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(jobs.router)
api_router.include_router(qa_pairs.router)
api_router.include_router(conversations.router)
api_router.include_router(retrieval.router)
api_router.include_router(chat.router)
api_router.include_router(settings.router)
api_router.include_router(evaluation.router)
