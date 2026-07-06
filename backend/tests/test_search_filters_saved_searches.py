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
from app.models import Custodian, Matter


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

    seed_workspace(testing_session_local)
    yield TestClient(app)

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def seed_workspace(testing_session_local: sessionmaker[Session]) -> None:
    db = testing_session_local()
    matter = Matter(name="Atlas v. Northwind", matter_number="A-2026")
    maria = Custodian(full_name="Maria Chen", email="maria@example.com")
    daniel = Custodian(full_name="Daniel Ortiz", email="daniel@example.com")
    db.add_all([matter, maria, daniel])
    db.commit()
    db.close()


def test_search_supports_metadata_filters(client: TestClient) -> None:
    matter_id, maria_id, daniel_id = _ids(client)
    _upload(
        client,
        "contract.txt",
        "March 3, 2024 contract with Acme includes Rule 26 production obligations.",
        matter_id,
        maria_id,
    )
    _upload(
        client,
        "memo.txt",
        "Legal memo dated April 15, 2025. Acme reviewed privilege and delay fees.",
        matter_id,
        daniel_id,
    )

    response = client.post(
        "/api/search",
        json={
            "query": "Acme",
            "matter_id": matter_id,
            "custodian_id": daniel_id,
            "document_type": "legal_memo",
            "file_type": "txt",
            "processing_status": "parsed",
            "date_from": "2025-04-01T00:00:00",
            "date_to": "2025-04-30T23:59:59",
            "limit": 5,
        },
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["title"] == "memo.txt"


def test_saved_search_create_run_and_audit(client: TestClient) -> None:
    matter_id, maria_id, _ = _ids(client)
    _upload(
        client,
        "contract.txt",
        "March 3, 2024 contract with Acme includes Rule 26 production obligations.",
        matter_id,
        maria_id,
    )

    create_response = client.post(
        "/api/search/saved",
        json={
            "name": "Contracts by Maria",
            "query": "contract Rule 26",
            "matter_id": matter_id,
            "custodian_id": maria_id,
            "document_type": "contract",
            "file_type": "txt",
            "processing_status": "parsed",
            "limit": 5,
        },
    )

    assert create_response.status_code == 200
    saved = create_response.json()
    assert saved["name"] == "Contracts by Maria"
    assert saved["filters"]["custodian_id"] == maria_id

    list_response = client.get("/api/search/saved", params={"matter_id": matter_id})
    assert list_response.status_code == 200
    assert [row["name"] for row in list_response.json()] == ["Contracts by Maria"]

    run_response = client.post(f"/api/search/saved/{saved['id']}/run")
    assert run_response.status_code == 200
    assert run_response.json()["results"][0]["title"] == "contract.txt"

    audit_response = client.get("/api/audit", params={"matter_id": matter_id})
    actions = {event["action"] for event in audit_response.json()}
    assert {"saved_search.create", "saved_search.run"} <= actions


def test_review_coding_filters_boolean_search_and_saved_search_updates(client: TestClient) -> None:
    matter_id, maria_id, daniel_id = _ids(client)
    _upload(
        client,
        "hot-contract.txt",
        "Project Falcon contract contains exact phrase special indemnity and privilege review notes.",
        matter_id,
        maria_id,
    )
    _upload(
        client,
        "cold-contract.txt",
        "Project Falcon contract contains routine schedule language and no indemnity issue.",
        matter_id,
        daniel_id,
    )
    documents = client.get("/api/documents", params={"matter_id": matter_id}).json()
    hot = next(document for document in documents if document["original_filename"] == "hot-contract.txt")

    coding_response = client.patch(
        f"/api/documents/{hot['id']}/coding",
        json={
            "tags": ["hot", "key"],
            "issue_codes": ["privilege"],
            "privilege_flag": True,
            "review_status": "responsive",
            "notes": "Needs partner review.",
        },
    )
    assert coding_response.status_code == 200
    assert coding_response.json()["tags"] == ["hot", "key"]

    search_response = client.post(
        "/api/search",
        json={
            "query": '"special indemnity" NOT routine',
            "matter_id": matter_id,
            "tag": "hot",
            "issue_code": "privilege",
            "privilege_flag": True,
            "review_status": "responsive",
            "sort_by": "date",
            "limit": 10,
        },
    )
    assert search_response.status_code == 200
    results = search_response.json()["results"]
    assert [result["title"] for result in results] == ["hot-contract.txt"]
    assert results[0]["diagnostics"]["phrase_matches"] == ["special indemnity"]
    assert results[0]["diagnostics"]["excluded_terms"] == ["routine"]

    create_response = client.post(
        "/api/search/saved",
        json={"name": "Hot docs", "query": "Falcon", "matter_id": matter_id, "tag": "hot", "limit": 5},
    )
    assert create_response.status_code == 200
    saved_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/search/saved/{saved_id}",
        json={"name": "Shared hot docs", "query": '"special indemnity"', "is_shared": True, "review_status": "responsive"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "Shared hot docs"
    assert updated["is_shared"] is True
    assert updated["filters"]["review_status"] == "responsive"

    delete_response = client.delete(f"/api/search/saved/{saved_id}")
    assert delete_response.status_code == 204

    audit_response = client.get("/api/audit", params={"matter_id": matter_id})
    actions = {event["action"] for event in audit_response.json()}
    assert {"document.coding_update", "saved_search.update", "saved_search.delete"} <= actions


def _ids(client: TestClient) -> tuple[int, int, int]:
    matter_id = client.get("/api/matters").json()[0]["id"]
    custodians = client.get("/api/custodians").json()
    return matter_id, custodians[0]["id"], custodians[1]["id"]


def _upload(client: TestClient, filename: str, text: str, matter_id: int, custodian_id: int) -> None:
    response = client.post(
        "/documents/upload",
        data={"matter_id": str(matter_id), "custodian_id": str(custodian_id)},
        files={"file": (filename, text.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 200
