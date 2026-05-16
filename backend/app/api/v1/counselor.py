"""Counselor assistance routes."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import require_counselor
from app.schemas.business import CounselorAssistRequest, CounselorAssistResponse
from app.services.business import User, store

router = APIRouter(prefix="/counselor", tags=["counselor"])


@router.post("/assistance", response_model=CounselorAssistResponse)
async def counselor_assistance(
    payload: CounselorAssistRequest,
    user: Annotated[User, Depends(require_counselor)],
) -> CounselorAssistResponse:
    """Generate counselor-facing draft assistance for a student concern."""
    resources = store.search_resources(payload.concern)
    concern = payload.concern.lower()
    risk_level = "urgent" if "suicide" in concern or "harm" in concern else "routine"
    if risk_level == "urgent":
        suggested = (
            "Escalate immediately using campus crisis protocol and verify the student's "
            "current safety, location, and emergency contact path."
        )
    else:
        suggested = (
            "Acknowledge the concern, ask one focused follow-up question, and offer a "
            "specific next step using the matched campus resource guidance."
        )
    store.record_audit(
        user.id,
        "counselor.assistance",
        "student",
        payload.student_id or "unknown",
        {"risk_level": risk_level},
    )
    return CounselorAssistResponse(
        suggested_response=suggested,
        risk_level=risk_level,
        resources=resources,
    )
