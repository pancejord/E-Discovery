from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import Actor, get_actor, require_matter_access
from app.database import get_db
from app.models.schemas import AIAnswerRequest, AIAnswerResponse
from app.services.audit import record_audit_event
from app.services.ai import answer_question

router = APIRouter()


@router.post("/answer", response_model=AIAnswerResponse)
def answer(
    request: AIAnswerRequest,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> AIAnswerResponse:
    require_matter_access(actor, request.matter_id)
    response = answer_question(db, request)
    record_audit_event(
        db,
        action="ai.answer",
        actor=actor.name,
        matter_id=request.matter_id,
        summary=f"Answered question: {request.question}",
        details={
            "provider": response.provider,
            "model": response.model,
            "provider_enabled": response.provider_enabled,
            "citations": response.citations,
            "source_count": len(response.sources),
            "hallucination_risk_score": response.grounding.hallucination_risk_score,
        },
    )
    return response
