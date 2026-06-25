from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import Actor, accessible_matter_ids, get_actor, require_matter_access
from app.database import get_db
from app.models.schemas import (
    BenchmarkCase,
    EvaluationMetric,
    EvaluationRunRequest,
    EvaluationRunResponse,
    EvaluationSummary,
    EvaluationTrendPoint,
    HallucinationCheckRequest,
    HallucinationCheckResponse,
)
from app.services.audit import record_audit_event
from app.services.evaluation import (
    check_answer_grounding,
    list_benchmarks,
    list_evaluation_metrics,
    list_evaluation_summaries,
    list_evaluation_trends,
    run_answer_evaluation,
    run_extraction_evaluation,
    run_retrieval_evaluation,
)

router = APIRouter()


@router.get("/benchmarks", response_model=list[BenchmarkCase])
def benchmarks(dataset_name: str | None = None) -> list[BenchmarkCase]:
    return list_benchmarks(dataset_name)


@router.get("/metrics", response_model=list[EvaluationMetric])
def list_metrics(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
    matter_id: int | None = None,
) -> list[EvaluationMetric]:
    require_matter_access(db, actor, matter_id)
    matter_ids = accessible_matter_ids(db, actor) if matter_id is None else None
    return list_evaluation_metrics(db, matter_id=matter_id, matter_ids=matter_ids)


@router.get("/summaries", response_model=list[EvaluationSummary])
def list_summaries(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
    matter_id: int | None = None,
) -> list[EvaluationSummary]:
    require_matter_access(db, actor, matter_id)
    matter_ids = accessible_matter_ids(db, actor) if matter_id is None else None
    return list_evaluation_summaries(db, matter_id=matter_id, matter_ids=matter_ids)


@router.get("/trends", response_model=list[EvaluationTrendPoint])
def list_trends(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
    matter_id: int | None = None,
    metric_name: str | None = None,
    limit: int = 200,
) -> list[EvaluationTrendPoint]:
    require_matter_access(db, actor, matter_id)
    matter_ids = accessible_matter_ids(db, actor) if matter_id is None else None
    return list_evaluation_trends(
        db,
        metric_name=metric_name,
        matter_id=matter_id,
        matter_ids=matter_ids,
        limit=min(max(limit, 1), 500),
    )


@router.post("/run", response_model=EvaluationRunResponse)
def run_evaluation(
    request: EvaluationRunRequest,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> EvaluationRunResponse:
    require_matter_access(db, actor, request.matter_id)
    matter_ids = accessible_matter_ids(db, actor) if request.matter_id is None else None
    if request.task_type == "answer":
        response = run_answer_evaluation(
            db,
            matter_id=request.matter_id,
            dataset_name=request.dataset_name,
            limit=request.limit,
            matter_ids=matter_ids,
        )
    elif request.task_type == "extraction":
        response = run_extraction_evaluation(
            db,
            matter_id=request.matter_id,
            dataset_name=request.dataset_name,
            limit=request.limit,
            matter_ids=matter_ids,
        )
    elif request.task_type == "all":
        retrieval_response = run_retrieval_evaluation(
            db,
            matter_id=request.matter_id,
            dataset_name=request.dataset_name,
            limit=request.limit,
            matter_ids=matter_ids,
        )
        answer_response = run_answer_evaluation(
            db,
            matter_id=request.matter_id,
            dataset_name=request.dataset_name,
            limit=request.limit,
            matter_ids=matter_ids,
        )
        extraction_response = run_extraction_evaluation(
            db,
            matter_id=request.matter_id,
            dataset_name=request.dataset_name,
            limit=request.limit,
            matter_ids=matter_ids,
        )
        response = EvaluationRunResponse(
            dataset_name=request.dataset_name,
            matter_id=request.matter_id,
            metrics=[*retrieval_response.metrics, *answer_response.metrics, *extraction_response.metrics],
        )
    else:
        response = run_retrieval_evaluation(
            db,
            matter_id=request.matter_id,
            dataset_name=request.dataset_name,
            limit=request.limit,
            matter_ids=matter_ids,
        )
    record_audit_event(
        db,
        action="evaluation.run",
        actor=actor.name,
        matter_id=request.matter_id,
        summary=f"Ran evaluation dataset {request.dataset_name}",
        details={"metric_count": len(response.metrics), "limit": request.limit, "task_type": request.task_type},
    )
    return response


@router.post("/check-answer", response_model=HallucinationCheckResponse)
def check_answer(
    request: HallucinationCheckRequest,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> HallucinationCheckResponse:
    response = check_answer_grounding(db, request.answer, request.citations)
    record_audit_event(
        db,
        action="evaluation.check_answer",
        actor=actor.name,
        summary="Checked answer grounding",
        details={
            "citation_count": response.citation_count,
            "valid_citation_count": response.valid_citation_count,
            "hallucination_risk_score": response.hallucination_risk_score,
        },
    )
    return response
