import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.evaluation import EvaluationRun
from app.models.schemas import (
    BenchmarkCase,
    EvaluationMetric,
    EvaluationRunResponse,
    HallucinationCheckResponse,
    SearchResult,
)
from app.services.search import search_chunks

BENCHMARK_DATASET_NAME = "phase6_synthetic_retrieval"
STOPWORDS = {
    "about",
    "after",
    "also",
    "and",
    "answer",
    "because",
    "before",
    "document",
    "documents",
    "from",
    "into",
    "that",
    "the",
    "their",
    "there",
    "this",
    "under",
    "with",
}
TERM_PATTERN = re.compile(r"\$?\b[A-Za-z0-9][A-Za-z0-9,.$%-]*\b")
CITATION_PATTERN = re.compile(r"^(?P<filename>.+)#chunk-(?P<chunk_index>\d+):(?P<start>\d+)-(?P<end>\d+)$")


@dataclass(frozen=True)
class CitationEvidence:
    is_valid: bool
    text: str = ""


DEFAULT_BENCHMARKS = [
    BenchmarkCase(
        id="contract-money-rule",
        dataset_name=BENCHMARK_DATASET_NAME,
        task_type="retrieval",
        query="contract dollar amount and Rule 26",
        expected_terms=["contract", "$12,500", "Rule 26"],
        minimum_citation_count=1,
    ),
    BenchmarkCase(
        id="email-communication",
        dataset_name=BENCHMARK_DATASET_NAME,
        task_type="retrieval",
        query="Jane Smith email John Doe update",
        expected_terms=["Jane Smith", "John Doe", "update"],
        minimum_citation_count=1,
    ),
    BenchmarkCase(
        id="timeline-date",
        dataset_name=BENCHMARK_DATASET_NAME,
        task_type="retrieval",
        query="March 3 2024 New York meeting",
        expected_terms=["March 3, 2024", "New York"],
        minimum_citation_count=1,
    ),
]


def list_benchmarks(dataset_name: str | None = None) -> list[BenchmarkCase]:
    if dataset_name is None:
        return DEFAULT_BENCHMARKS
    return [case for case in DEFAULT_BENCHMARKS if case.dataset_name == dataset_name]


def run_retrieval_evaluation(
    db: Session,
    matter_id: int | None = None,
    dataset_name: str = BENCHMARK_DATASET_NAME,
    limit: int = 10,
) -> EvaluationRunResponse:
    metrics = []
    for case in list_benchmarks(dataset_name):
        results = search_chunks(db, case.query, matter_id=matter_id, limit=limit)
        case_metrics = _evaluate_case(db, case, results, matter_id)
        metrics.extend(case_metrics)
        for metric in case_metrics:
            db.add(metric)

    if metrics:
        db.commit()
        for metric in metrics:
            db.refresh(metric)

    return EvaluationRunResponse(
        dataset_name=dataset_name,
        matter_id=matter_id,
        metrics=[_metric_schema(metric) for metric in metrics],
    )


def list_evaluation_metrics(db: Session, matter_id: int | None = None) -> list[EvaluationMetric]:
    statement = select(EvaluationRun).order_by(EvaluationRun.created_at.desc(), EvaluationRun.id.desc())
    if matter_id is not None:
        statement = statement.where(EvaluationRun.matter_id == matter_id)
    return [_metric_schema(metric) for metric in db.scalars(statement)]


def check_answer_grounding(db: Session, answer: str, citations: list[str]) -> HallucinationCheckResponse:
    evidence = [resolve_citation(db, citation) for citation in citations]
    evidence_text = " ".join(item.text for item in evidence if item.is_valid).lower()
    answer_terms = _important_terms(answer)
    supported_terms = sorted({term for term in answer_terms if term.lower() in evidence_text})
    unsupported_terms = sorted(set(answer_terms) - set(supported_terms))
    valid_citation_count = sum(1 for item in evidence if item.is_valid)
    unsupported_rate = len(unsupported_terms) / len(answer_terms) if answer_terms else 0.0
    citation_penalty = 0.0 if citations and valid_citation_count == len(citations) else 0.25
    risk_score = min(1.0, unsupported_rate + citation_penalty)

    return HallucinationCheckResponse(
        supported_terms=supported_terms,
        unsupported_terms=unsupported_terms,
        citation_count=len(citations),
        valid_citation_count=valid_citation_count,
        unsupported_term_rate=round(unsupported_rate, 4),
        hallucination_risk_score=round(risk_score, 4),
    )


def resolve_citation(db: Session, citation: str | None) -> CitationEvidence:
    if not citation:
        return CitationEvidence(is_valid=False)
    match = CITATION_PATTERN.match(citation)
    if match is None:
        return CitationEvidence(is_valid=False)

    filename = match.group("filename")
    chunk_index = int(match.group("chunk_index")) - 1
    statement = (
        select(DocumentChunk)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(Document.original_filename == filename, DocumentChunk.chunk_index == chunk_index)
    )
    chunk = db.scalar(statement)
    if chunk is None:
        return CitationEvidence(is_valid=False)
    return CitationEvidence(is_valid=True, text=chunk.text)


def _evaluate_case(
    db: Session,
    case: BenchmarkCase,
    results: list[SearchResult],
    matter_id: int | None,
) -> list[EvaluationRun]:
    retrieved_text = " ".join(f"{result.title} {result.snippet} {result.citation or ''}" for result in results).lower()
    relevant_results = [result for result in results if _result_matches_expected_terms(result, case.expected_terms)]
    found_terms = [term for term in case.expected_terms if term.lower() in retrieved_text]
    valid_citations = [result for result in results if resolve_citation(db, result.citation).is_valid]

    precision = len(relevant_results) / len(results) if results else 0.0
    recall = len(found_terms) / len(case.expected_terms) if case.expected_terms else 1.0
    citation_coverage = len(valid_citations) / len(results) if results else 0.0
    pass_rate = 1.0 if precision > 0 and recall >= 0.5 and len(valid_citations) >= case.minimum_citation_count else 0.0

    details = {
        "query": case.query,
        "expected_terms": case.expected_terms,
        "found_terms": found_terms,
        "result_count": len(results),
        "valid_citation_count": len(valid_citations),
    }
    metric_values = {
        "retrieval_precision": precision,
        "retrieval_recall": recall,
        "citation_coverage": citation_coverage,
        "benchmark_pass": pass_rate,
    }
    return [
        _metric_record(case, matter_id, metric_name, metric_value, details)
        for metric_name, metric_value in metric_values.items()
    ]


def _result_matches_expected_terms(result: SearchResult, expected_terms: list[str]) -> bool:
    text = f"{result.title} {result.snippet} {result.citation or ''}".lower()
    return any(term.lower() in text for term in expected_terms)


def _metric_record(
    case: BenchmarkCase,
    matter_id: int | None,
    metric_name: str,
    metric_value: float,
    details: dict,
) -> EvaluationRun:
    return EvaluationRun(
        matter_id=matter_id,
        dataset_name=case.dataset_name,
        case_id=case.id,
        task_type=case.task_type,
        metric_name=metric_name,
        metric_value=round(metric_value, 4),
        details=details,
    )


def _metric_schema(metric: EvaluationRun) -> EvaluationMetric:
    return EvaluationMetric(
        id=metric.id,
        matter_id=metric.matter_id,
        dataset_name=metric.dataset_name,
        case_id=metric.case_id,
        task_type=metric.task_type,
        metric_name=metric.metric_name,
        metric_value=metric.metric_value,
        created_at=metric.created_at,
    )


def _important_terms(text: str) -> list[str]:
    text_without_citations = re.sub(r"\[[^\]]+\]", " ", text)
    terms = []
    for raw_term in TERM_PATTERN.findall(text_without_citations):
        term = raw_term.strip(".,;:()[]{}\"'")
        if len(term) < 3:
            continue
        if term.lower() in STOPWORDS:
            continue
        terms.append(term)
    return terms
