from fastapi import APIRouter

from app.models.schemas import EvaluationMetric

router = APIRouter()


@router.get("/metrics", response_model=list[EvaluationMetric])
def list_metrics() -> list[EvaluationMetric]:
    return []
