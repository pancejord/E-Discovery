from collections.abc import Generator
import hashlib
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.auth import hash_api_key
from app.database import Base, get_db
from app.main import app
from app.models import Role, User


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

    monkeypatch.setattr(settings, "auth_enabled", False)
    monkeypatch.setattr(settings, "auth_bearer_enabled", False)
    monkeypatch.setattr(settings, "api_keys", None)
    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_matter_and_custodian_management_create_audit_events(client: TestClient) -> None:
    matter_response = client.post(
        "/api/matters",
        json={"name": "Acme v. Smith", "matter_number": "ACME-2026"},
    )
    assert matter_response.status_code == 200
    matter = matter_response.json()

    custodian_response = client.post(
        "/api/custodians",
        json={"full_name": "Jane Smith", "email": "jane@example.com"},
    )
    assert custodian_response.status_code == 200

    list_response = client.get("/api/matters")
    assert list_response.status_code == 200
    assert list_response.json()[0]["name"] == "Acme v. Smith"

    audit_response = client.get("/api/audit", params={"matter_id": matter["id"]})
    assert audit_response.status_code == 200
    actions = {event["action"] for event in audit_response.json()}
    assert "matter.create" in actions


def test_api_key_auth_can_be_enabled(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    db = next(app.dependency_overrides[get_db]())
    role = Role(name="admin", is_admin=True)
    db.add(role)
    db.commit()
    db.refresh(role)
    db.add(
        User(
            email="admin@example.com",
            display_name="Admin",
            api_key_hash=hash_api_key("secret-key"),
            role_id=role.id,
        )
    )
    db.commit()
    db.close()

    monkeypatch.setattr(settings, "auth_enabled", True)

    unauthorized = client.get("/api/matters")
    assert unauthorized.status_code == 401

    authorized = client.get("/api/matters", headers={"X-API-Key": "secret-key"})
    assert authorized.status_code == 200


def test_bearer_auth_adds_user_and_request_context_to_audit(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    db = next(app.dependency_overrides[get_db]())
    role = Role(name="admin", is_admin=True)
    db.add(role)
    db.commit()
    db.refresh(role)
    db.add(
        User(
            email="tenant-admin@example.com",
            display_name="Tenant Admin",
            api_key_hash=hash_api_key("bearer-secret"),
            role_id=role.id,
            organization="Acme Legal",
            tenant_id="tenant-acme",
        )
    )
    db.commit()
    db.close()

    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_bearer_enabled", True)

    response = client.get(
        "/api/matters",
        headers={
            "Authorization": "Bearer bearer-secret",
            "X-Request-ID": "trace-123",
            "User-Agent": "pytest-audit-agent",
        },
    )
    assert response.status_code == 200

    audit_response = client.get(
        "/api/audit",
        headers={"Authorization": "Bearer bearer-secret"},
        params={"action": "matter.list", "request_id": "trace-123"},
    )
    assert audit_response.status_code == 200
    event = audit_response.json()[0]
    assert event["actor"] == "tenant-admin@example.com"
    assert event["request_id"] == "trace-123"
    assert event["route"] == "/api/matters"
    assert event["method"] == "GET"
    assert event["user_agent"] == "pytest-audit-agent"
    assert event["details"]["actor_context"]["tenant_id"] == "tenant-acme"
    assert event["details"]["actor_context"]["organization"] == "Acme Legal"
    assert event["details"]["actor_context"]["auth_scheme"] == "bearer"

    completed_response = client.get(
        "/api/audit",
        headers={"Authorization": "Bearer bearer-secret"},
        params={"action": "request.completed", "request_id": "trace-123"},
    )
    assert completed_response.status_code == 200
    assert completed_response.json()[0]["response_status"] == 200


def test_audit_export_manifest_matches_payload(client: TestClient) -> None:
    client.post("/api/matters", json={"name": "Manifest Matter", "matter_number": "MAN-1"})

    response = client.get("/api/audit/export", params={"format": "csv"})

    assert response.status_code == 200
    manifest = json.loads(response.headers["X-Audit-Export-Manifest"])
    assert manifest["format"] == "csv"
    assert manifest["event_count"] >= 1
    assert manifest["sha256"] == hashlib.sha256(response.content).hexdigest()
    assert manifest["byte_count"] == len(response.content)
