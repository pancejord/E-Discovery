from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.database import Base, get_db
from app.main import app


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
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", "secret-key")

    unauthorized = client.get("/api/matters")
    assert unauthorized.status_code == 401

    authorized = client.get("/api/matters", headers={"X-API-Key": "secret-key"})
    assert authorized.status_code == 200
