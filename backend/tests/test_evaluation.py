from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_evaluation_run_persists_retrieval_and_citation_metrics(client: TestClient) -> None:
    _upload_evaluation_documents(client)

    benchmarks_response = client.get("/api/evaluation/benchmarks")
    assert benchmarks_response.status_code == 200
    assert len(benchmarks_response.json()) >= 9

    retrieval_benchmarks_response = client.get(
        "/api/evaluation/benchmarks",
        params={"dataset_name": "phase6_synthetic_retrieval"},
    )
    assert retrieval_benchmarks_response.status_code == 200
    assert len(retrieval_benchmarks_response.json()) == 3

    run_response = client.post("/api/evaluation/run", json={"limit": 5})
    assert run_response.status_code == 200
    run = run_response.json()
    assert run["dataset_name"] == "phase6_synthetic_retrieval"
    assert len(run["metrics"]) == 12
    metric_names = {metric["metric_name"] for metric in run["metrics"]}
    assert {
        "retrieval_precision",
        "retrieval_recall",
        "citation_coverage",
        "benchmark_pass",
    } <= metric_names
    assert all(0 <= metric["metric_value"] <= 1 for metric in run["metrics"])

    metrics_response = client.get("/api/evaluation/metrics")
    assert metrics_response.status_code == 200
    assert len(metrics_response.json()) == 12


def test_ai_answer_persists_answer_quality_metrics(client: TestClient) -> None:
    _upload_evaluation_documents(client)

    answer_response = client.post(
        "/api/ai/answer",
        json={"question": "What contract amount is tied to Rule 26?", "limit": 3},
    )
    assert answer_response.status_code == 200

    metrics_response = client.get("/api/evaluation/metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    metric_names = {metric["metric_name"] for metric in metrics}
    assert {
        "answer_citation_validity",
        "answer_unsupported_term_rate",
        "answer_hallucination_risk",
    } <= metric_names


def test_answer_benchmark_runner_scores_answer_and_negative_cases(client: TestClient) -> None:
    _upload_mixed_production_documents(client)

    run_response = client.post(
        "/api/evaluation/run",
        json={
            "dataset_name": "phase8_synthetic_mixed_production",
            "task_type": "answer",
            "limit": 5,
        },
    )

    assert run_response.status_code == 200
    run = run_response.json()
    assert run["dataset_name"] == "phase8_synthetic_mixed_production"
    assert len(run["metrics"]) == 12
    metric_names = {metric["metric_name"] for metric in run["metrics"]}
    assert {
        "answer_expected_term_coverage",
        "answer_citation_validity",
        "answer_unsupported_term_rate",
        "answer_hallucination_risk",
        "answer_no_answer_match",
        "answer_benchmark_pass",
    } <= metric_names

    negative_metrics = [metric for metric in run["metrics"] if metric["case_id"] == "negative-admission-liability"]
    assert any(
        metric["metric_name"] == "answer_no_answer_match" and metric["metric_value"] == 1.0
        for metric in negative_metrics
    )
    assert any(
        metric["metric_name"] == "answer_benchmark_pass" and metric["metric_value"] == 1.0
        for metric in negative_metrics
    )


def test_extraction_benchmark_runner_summaries_and_trends(client: TestClient) -> None:
    _upload_mixed_production_documents(client)

    run_response = client.post(
        "/api/evaluation/run",
        json={
            "dataset_name": "phase8_synthetic_mixed_production",
            "task_type": "extraction",
            "limit": 5,
        },
    )

    assert run_response.status_code == 200
    run = run_response.json()
    assert run["dataset_name"] == "phase8_synthetic_mixed_production"
    assert len(run["metrics"]) == 21
    metric_names = {metric["metric_name"] for metric in run["metrics"]}
    assert {
        "extraction_expected_term_coverage",
        "classification_match",
        "document_date_match",
        "entity_coverage",
        "relationship_coverage",
        "ocr_term_coverage",
        "extraction_benchmark_pass",
    } <= metric_names
    assert any(metric["details"]["owner"] == "quality" for metric in run["metrics"])
    assert any(metric["details"]["triage_notes"] for metric in run["metrics"])

    summaries_response = client.get("/api/evaluation/summaries")
    assert summaries_response.status_code == 200
    summaries = summaries_response.json()
    assert any(summary["metric_name"] == "extraction_benchmark_pass" for summary in summaries)

    trends_response = client.get("/api/evaluation/trends", params={"metric_name": "extraction_benchmark_pass"})
    assert trends_response.status_code == 200
    trends = trends_response.json()
    assert len(trends) == 3
    assert all(point["metric_name"] == "extraction_benchmark_pass" for point in trends)


def test_answer_grounding_flags_unsupported_terms(client: TestClient) -> None:
    _upload_evaluation_documents(client)
    search_response = client.post("/api/search", json={"query": "contract Rule 26 $12,500", "limit": 1})
    assert search_response.status_code == 200
    citation = search_response.json()["results"][0]["citation"]

    grounded_response = client.post(
        "/api/evaluation/check-answer",
        json={
            "answer": "Jane Smith signed a contract for 12,500 under Rule 26.",
            "citations": [citation],
        },
    )
    assert grounded_response.status_code == 200
    grounded = grounded_response.json()
    assert grounded["valid_citation_count"] == 1
    assert grounded["hallucination_risk_score"] < 0.5

    unsupported_response = client.post(
        "/api/evaluation/check-answer",
        json={
            "answer": "Jane Smith paid 99,999 in Paris.",
            "citations": [citation],
        },
    )
    assert unsupported_response.status_code == 200
    unsupported = unsupported_response.json()
    assert unsupported["valid_citation_count"] == 1
    assert "Paris" in unsupported["unsupported_terms"]
    assert unsupported["hallucination_risk_score"] > grounded["hallucination_risk_score"]


def _upload_evaluation_documents(client: TestClient) -> None:
    contract_text = (
        "Jane Smith and Acme Corp signed a contract for $12,500 on March 3, 2024 "
        "in New York under Rule 26."
    )
    contract_response = client.post(
        "/documents/upload",
        files={"file": ("evaluation-contract.txt", contract_text.encode("utf-8"), "text/plain")},
    )
    assert contract_response.status_code == 200

    email_response = client.post(
        "/documents/upload",
        files={
            "file": (
                "evaluation-email.eml",
                b"From: Jane Smith <jane@example.com>\r\n"
                b"To: John Doe <john@example.com>\r\n"
                b"Subject: Update\r\n\r\nJohn Doe received an update from Jane Smith.",
                "message/rfc822",
            )
        },
    )
    assert email_response.status_code == 200


def _upload_mixed_production_documents(client: TestClient) -> None:
    documents = [
        (
            "atlas-northwind-amendment.txt",
            b"Amendment No. 2 between Atlas Components and Northwind Systems sets a payment cap of $87,500 "
            b"for implementation support. Section 4.3 requires written notice before delay fees can be assessed.",
            "text/plain",
        ),
        (
            "delay-notice-email.eml",
            b"From: Maria Chen <maria.chen@example.com>\r\n"
            b"To: Daniel Ortiz <daniel.ortiz@example.com>\r\n"
            b"Date: Mon, 14 Apr 2025 09:12:00 -0400\r\n"
            b"Subject: Warehouse migration delay notice\r\n\r\n"
            b"Daniel, this is the delay notice for the warehouse migration. Northwind expects a two-week slip "
            b"but has not agreed to any fraud allegation.",
            "message/rfc822",
        ),
        (
            "invoice-1042.txt",
            b"Invoice INV-1042 includes a disputed line item for expedited review in the amount of $18,400. "
            b"Atlas marked the expedited review charge as disputed pending backup documentation.",
            "text/plain",
        ),
        (
            "rfp-response-007.txt",
            b"Response to Request for Production No. 7: Atlas will produce Maria Chen's Slack export for the "
            b"warehouse migration channel, subject to privilege review and agreed search terms.",
            "text/plain",
        ),
        (
            "legal-risk-memo.txt",
            b"Legal memo: The principal contractual risk is uncapped implementation delay fees if written notice "
            b"under Section 4.3 is deemed sufficient. The current record does not establish that Northwind admitted "
            b"liability for fraud.",
            "text/plain",
        ),
    ]
    for filename, content, content_type in documents:
        response = client.post(
            "/documents/upload",
            files={"file": (filename, content, content_type)},
        )
        assert response.status_code == 200
