from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import (
    BenchmarkCase,
    EvaluationMetric,
    EvaluationRunRequest,
    EvaluationRunResponse,
    HallucinationCheckRequest,
    HallucinationCheckResponse,
)
from app.services.evaluation import (
    check_answer_grounding,
    list_benchmarks,
    list_evaluation_metrics,
    run_retrieval_evaluation,
)

router = APIRouter()


@router.get("/benchmarks", response_model=list[BenchmarkCase])
def benchmarks(dataset_name: str | None = None) -> list[BenchmarkCase]:
    return list_benchmarks(dataset_name)


@router.get("/metrics", response_model=list[EvaluationMetric])
def list_metrics(
    db: Session = Depends(get_db),
    matter_id: int | None = None,
) -> list[EvaluationMetric]:
    return list_evaluation_metrics(db, matter_id=matter_id)


@router.post("/run", response_model=EvaluationRunResponse)
def run_evaluation(
    request: EvaluationRunRequest,
    db: Session = Depends(get_db),
) -> EvaluationRunResponse:
    return run_retrieval_evaluation(
        db,
        matter_id=request.matter_id,
        dataset_name=request.dataset_name,
        limit=request.limit,
    )


@router.post("/check-answer", response_model=HallucinationCheckResponse)
def check_answer(
    request: HallucinationCheckRequest,
    db: Session = Depends(get_db),
) -> HallucinationCheckResponse:
    return check_answer_grounding(db, request.answer, request.citations)
