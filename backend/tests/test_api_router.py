from fastapi import FastAPI

from app.api.v1.router import api_router


def test_api_router_includes_backend_business_routes():
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")
    paths = set(app.openapi()["paths"])

    assert "/api/v1/readiness" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/chat/stream" in paths
    assert "/api/v1/documents/knowledge-bases" in paths
    assert "/api/v1/qa-pairs" in paths
    assert "/api/v1/retrieval/search" in paths
    assert "/api/v1/feedback/answers/{feedback_id}/cancel" in paths
    assert "/api/v1/settings/rag" in paths
    assert "/api/v1/evaluation/cases" in paths
    assert "/api/v1/files/{bucket}/{object_key}" in paths
