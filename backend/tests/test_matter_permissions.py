from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import hash_api_key
from app.core.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import Document, Matter, MatterMembership, Role, User


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
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

    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", None)
    app.dependency_overrides[get_db] = override_get_db

    seed_authz(testing_session_local)
    yield TestClient(app)

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def seed_authz(testing_session_local: sessionmaker[Session]) -> None:
    db = testing_session_local()
    reviewer_role = Role(name="reviewer", is_admin=False)
    admin_role = Role(name="admin", is_admin=True)
    matter_a = Matter(name="Allowed Matter", matter_number="A-1")
    matter_b = Matter(name="Denied Matter", matter_number="B-1")
    db.add_all([reviewer_role, admin_role, matter_a, matter_b])
    db.commit()
    for row in [reviewer_role, admin_role, matter_a, matter_b]:
        db.refresh(row)

    reviewer = User(
        email="reviewer@example.com",
        display_name="Reviewer",
        api_key_hash=hash_api_key("reviewer-key"),
        role_id=reviewer_role.id,
    )
    admin = User(
        email="admin@example.com",
        display_name="Admin",
        api_key_hash=hash_api_key("admin-key"),
        role_id=admin_role.id,
    )
    db.add_all([reviewer, admin])
    db.commit()
    db.refresh(reviewer)
    db.add(MatterMembership(user_id=reviewer.id, matter_id=matter_a.id, role="reviewer"))
    db.add_all(
        [
            Document(
                matter_id=matter_a.id,
                original_filename="allowed.txt",
                stored_file_path="allowed.txt",
                file_type="txt",
                extracted_text="allowed contract text",
                processing_status="parsed",
            ),
            Document(
                matter_id=matter_b.id,
                original_filename="denied.txt",
                stored_file_path="denied.txt",
                file_type="txt",
                extracted_text="denied privileged text",
                processing_status="parsed",
            ),
        ]
    )
    db.commit()
    db.close()


def test_reviewer_only_lists_assigned_matters(client: TestClient) -> None:
    response = client.get("/api/matters", headers={"X-API-Key": "reviewer-key"})

    assert response.status_code == 200
    assert [matter["name"] for matter in response.json()] == ["Allowed Matter"]


def test_cross_matter_document_read_is_denied_and_audited(client: TestClient) -> None:
    allowed_documents = client.get("/api/documents", headers={"X-API-Key": "reviewer-key"})
    assert allowed_documents.status_code == 200
    assert [document["original_filename"] for document in allowed_documents.json()] == ["allowed.txt"]

    denied_response = client.get("/api/documents/2", headers={"X-API-Key": "reviewer-key"})
    assert denied_response.status_code == 403

    audit_response = client.get("/api/audit", headers={"X-API-Key": "admin-key"}, params={"action": "permission.denied"})
    assert audit_response.status_code == 200
    assert audit_response.json()[0]["matter_id"] == 2


def test_unscoped_search_and_analytics_are_limited_to_memberships(client: TestClient) -> None:
    search_response = client.post(
        "/api/search",
        headers={"X-API-Key": "reviewer-key"},
        json={"query": "denied privileged", "limit": 5},
    )
    assert search_response.status_code == 200
    assert search_response.json()["results"] == []

    analytics_response = client.get("/api/analytics/dashboard", headers={"X-API-Key": "reviewer-key"})
    assert analytics_response.status_code == 200
    assert analytics_response.json()["snapshot"]["document_count"] == 1


def test_audit_export_supports_filters(client: TestClient) -> None:
    client.get("/api/matters", headers={"X-API-Key": "reviewer-key"})

    csv_response = client.get(
        "/api/audit/export",
        headers={"X-API-Key": "admin-key"},
        params={"action": "matter.list", "format": "csv"},
    )
    assert csv_response.status_code == 200
    assert "matter.list" in csv_response.text

    json_response = client.get(
        "/api/audit/export",
        headers={"X-API-Key": "admin-key"},
        params={"action": "matter.list", "format": "json"},
    )
    assert json_response.status_code == 200
    assert json_response.json()[0]["action"] == "matter.list"
