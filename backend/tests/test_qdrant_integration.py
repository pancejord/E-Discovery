from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import Document
from app.models.chunk import DocumentChunk
from app.services.embeddings import embed_text
from app.services.search import search_chunks


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


def test_qdrant_failure_falls_back_to_local_search(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    _upload_qdrant_documents(client)
    monkeypatch.setattr(settings, "qdrant_enabled", True)

    def unavailable_qdrant(*args, **kwargs):
        raise RuntimeError("qdrant unavailable")

    monkeypatch.setattr("app.services.search.query_chunks", unavailable_qdrant)

    response = client.post("/api/search", json={"query": "Rule 26 contract", "limit": 5})

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "local"
    assert payload["results"]
    assert all(result["source"] == "local" for result in payload["results"])


def test_qdrant_search_accepts_accessible_matter_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_query_chunks(query_vector, matter_id=None, matter_ids=None, limit=10):
        captured["matter_id"] = matter_id
        captured["matter_ids"] = matter_ids
        return [{"chunk_id": 1, "score": 0.99}]

    monkeypatch.setattr("app.services.search.query_chunks", fake_query_chunks)

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = testing_session_local()
    try:
        document = Document(
            id=1,
            matter_id=7,
            original_filename="allowed.txt",
            stored_file_path="allowed.txt",
            file_type="txt",
            subject="Allowed",
            extracted_text="allowed Rule 26 text",
            processing_status="parsed",
        )
        db.add(document)
        db.add(
            DocumentChunk(
                id=1,
                document_id=1,
                chunk_index=0,
                text="allowed Rule 26 text",
                text_hash="hash",
                char_start=0,
                char_end=20,
                token_count=4,
                vector_id=str(uuid4()),
                embedding=embed_text("allowed Rule 26 text"),
            )
        )
        db.commit()

        results = search_chunks(db, "Rule 26", matter_ids=[7], backend="qdrant")
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

    assert captured == {"matter_id": None, "matter_ids": [7]}
    assert results[0].source == "qdrant"


def test_qdrant_indexes_and_hydrates_citation_results(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    qdrant_client = pytest.importorskip("qdrant_client")
    collection_name = f"test_document_chunks_{uuid4().hex}"
    qdrant = qdrant_client.QdrantClient(url=settings.qdrant_url, timeout=2)
    try:
        qdrant.get_collections()
    except Exception as error:
        pytest.skip(f"Qdrant is not available at {settings.qdrant_url}: {error}")

    monkeypatch.setattr(settings, "qdrant_enabled", True)
    monkeypatch.setattr(settings, "qdrant_collection", collection_name)
    try:
        _upload_qdrant_documents(client)
        count = qdrant.count(collection_name=collection_name, exact=True).count
        assert count >= 2

        search_response = client.post(
            "/api/search",
            json={"query": "Rule 26 contract amount", "limit": 3},
        )
        assert search_response.status_code == 200
        search_payload = search_response.json()
        assert search_payload["source"] == "qdrant"
        assert search_payload["results"][0]["citation"]

        evaluation_response = client.post("/api/evaluation/run", json={"limit": 3})
        assert evaluation_response.status_code == 200
        metric_names = {metric["metric_name"] for metric in evaluation_response.json()["metrics"]}
        assert {
            "qdrant_local_result_overlap",
            "qdrant_local_top_result_match",
            "qdrant_result_count_delta",
        } <= metric_names
    finally:
        try:
            qdrant.delete_collection(collection_name=collection_name)
        except Exception:
            pass


def _upload_qdrant_documents(client: TestClient) -> None:
    documents = [
        (
            "qdrant-contract.txt",
            b"Jane Smith and Acme Corp signed a contract for $12,500 in New York under Rule 26.",
        ),
        (
            "qdrant-email.txt",
            b"John Doe received an update from Jane Smith about the March 3, 2024 New York meeting.",
        ),
    ]
    for filename, content in documents:
        response = client.post(
            "/documents/upload",
            files={"file": (filename, content, "text/plain")},
        )
        assert response.status_code == 200
