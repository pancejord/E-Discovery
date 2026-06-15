from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import AIAnswerRequest, AIAnswerResponse
from app.services.ai import answer_question

router = APIRouter()


@router.post("/answer", response_model=AIAnswerResponse)
def answer(request: AIAnswerRequest, db: Session = Depends(get_db)) -> AIAnswerResponse:
    return answer_question(db, request)
