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
from app.models.schemas import AISource
from app.services.ai import build_grounded_prompt


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
    monkeypatch.setattr(settings, "ai_provider", "local")
    monkeypatch.setattr(settings, "ai_external_enabled", False)
    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_ai_answer_returns_cited_grounded_response(client: TestClient) -> None:
    upload_response = client.post(
        "/documents/upload",
        files={
            "file": (
                "ai-contract.txt",
                b"Jane Smith and Acme Corp signed a contract for $12,500 under Rule 26.",
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 200

    response = client.post(
        "/api/ai/answer",
        json={"question": "What did Jane Smith sign and under what rule?", "limit": 3},
    )

    assert response.status_code == 200
    answer = response.json()
    assert answer["provider"] == "local"
    assert answer["provider_enabled"] is True
    assert answer["sources"]
    assert answer["citations"]
    assert "ai-contract.txt#chunk-1" in answer["answer"]
    assert answer["grounding"]["valid_citation_count"] >= 1
    assert answer["grounding"]["hallucination_risk_score"] < 0.8


def test_ai_answer_handles_no_sources(client: TestClient) -> None:
    response = client.post("/api/ai/answer", json={"question": "What happened?", "limit": 3})

    assert response.status_code == 200
    answer = response.json()
    assert answer["answer"] == "The available documents do not establish an answer to this question."
    assert answer["sources"] == []
    assert answer["citations"] == []


def test_ai_answer_refuses_when_retrieved_sources_do_not_overlap_question(client: TestClient) -> None:
    upload_response = client.post(
        "/documents/upload",
        files={
            "file": (
                "ai-contract.txt",
                b"Jane Smith and Acme Corp signed a contract for $12,500 under Rule 26.",
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 200

    response = client.post(
        "/api/ai/answer",
        json={"question": "Did anyone admit liability for fraud in Paris?", "limit": 3},
    )

    assert response.status_code == 200
    answer = response.json()
    assert answer["answer"] == "The available documents do not establish an answer to this question."
    assert answer["citations"] == []


def test_ai_answer_modes_and_matter_policy_redaction(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "ai_external_enabled", True)
    monkeypatch.setattr(settings, "openai_api_key", None)

    matter_response = client.post(
        "/api/matters",
        json={
            "name": "AI policy matter",
            "ai_external_allowed": True,
            "ai_redaction_required": True,
            "ai_allowed_modes": ["chronology", "summary"],
        },
    )
    assert matter_response.status_code == 200
    matter_id = matter_response.json()["id"]

    upload_response = client.post(
        "/documents/upload",
        data={"matter_id": str(matter_id)},
        files={
            "file": (
                "ai-redaction.txt",
                b"On April 1, 2025, Jane Smith emailed jane.smith@example.com about a $88,400 contract payment.",
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 200

    response = client.post(
        "/api/ai/answer",
        json={
            "question": "Build a chronology for the contract payment involving jane.smith@example.com and $88,400.",
            "matter_id": matter_id,
            "answer_mode": "chronology",
            "limit": 3,
        },
    )

    assert response.status_code == 200
    answer = response.json()
    assert answer["answer_mode"] == "chronology"
    assert answer["provider"] == "openai"
    assert answer["redactions_applied"] is True
    assert answer["redaction_count"] >= 2
    assert answer["policy"]["external_allowed"] is True


def test_ai_external_provider_blocked_when_matter_policy_disallows(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "ai_external_enabled", True)
    monkeypatch.setattr(settings, "openai_api_key", None)

    matter_response = client.post("/api/matters", json={"name": "Local only matter"})
    assert matter_response.status_code == 200
    matter_id = matter_response.json()["id"]

    upload_response = client.post(
        "/documents/upload",
        data={"matter_id": str(matter_id)},
        files={"file": ("ai-local.txt", b"Jane Smith signed a contract under Rule 26.", "text/plain")},
    )
    assert upload_response.status_code == 200

    response = client.post(
        "/api/ai/answer",
        json={"question": "What did Jane Smith sign?", "matter_id": matter_id, "answer_mode": "summary", "limit": 3},
    )

    assert response.status_code == 200
    answer = response.json()
    assert answer["provider"] == "local"
    assert answer["policy"]["external_allowed"] is False
    assert answer["redactions_applied"] is False


def test_grounded_prompt_includes_citations_and_source_excerpts() -> None:
    prompt = build_grounded_prompt(
        "Who signed the contract?",
        [
            AISource(
                document_id=1,
                chunk_id=1,
                title="contract.txt",
                snippet="Jane Smith signed the contract.",
                score=0.9,
                citation="contract.txt#chunk-1:0-31",
            )
        ],
    )

    assert "Who signed the contract?" in prompt
    assert "Jane Smith signed the contract." in prompt
    assert "contract.txt#chunk-1:0-31" in prompt
