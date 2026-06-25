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

    yield TestClient(app)

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_analytics_dashboard_uses_ingested_documents(client: TestClient) -> None:
    db = next(app.dependency_overrides[get_db]())
    matter = Matter(name="Analytics Matter", client_name="Acme Corp", matter_number="ANA-001")
    custodian = Custodian(full_name="Jane Smith", email="jane@example.com")
    db.add_all([matter, custodian])
    db.commit()
    db.refresh(matter)
    db.refresh(custodian)
    db.close()

    contract_text = (
        "Jane Smith and Acme Corp signed a contract for $12,500 on March 3, 2024 "
        "under Rule 26."
    )
    contract_response = client.post(
        "/documents/upload",
        data={"matter_id": str(matter.id), "custodian_id": str(custodian.id)},
        files={"file": ("analytics-contract.txt", contract_text.encode("utf-8"), "text/plain")},
    )
    assert contract_response.status_code == 200

    email_response = client.post(
        "/documents/upload",
        data={"matter_id": str(matter.id), "custodian_id": str(custodian.id)},
        files={
            "file": (
                "analytics-email.eml",
                b"From: Jane Smith <jane@example.com>\r\n"
                b"To: John Doe <john@example.com>\r\n"
                b"Date: Tue, 05 Mar 2024 12:00:00 -0500\r\n"
                b"Subject: Update\r\n\r\nAcme Corp update.",
                "message/rfc822",
            )
        },
    )
    assert email_response.status_code == 200

    response = client.get("/api/analytics/dashboard", params={"matter_id": matter.id})

    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["snapshot"]["document_count"] == 2
    assert dashboard["snapshot"]["entity_count"] > 0
    assert dashboard["snapshot"]["relationship_count"] > 0
    assert dashboard["snapshot"]["file_type_counts"] == {"txt": 1, "eml": 1}
    assert dashboard["snapshot"]["custodian_counts"] == {"Jane Smith": 2}
    assert dashboard["file_type_distribution"] == [
        {"label": "txt", "count": 1},
        {"label": "eml", "count": 1},
    ]
    assert any(bucket["label"] == "contract" for bucket in dashboard["document_type_distribution"])
    assert any(bucket["label"] == "PERSON" for bucket in dashboard["entity_type_distribution"])
    assert any(bucket["label"] == "communicated_with" for bucket in dashboard["relationship_type_distribution"])
    assert any(point["date"] == "2024-03-05" for point in dashboard["document_timeline"])
    assert dashboard["top_custodians"] == [{"label": "Jane Smith", "count": 2}]
    assert any(
        pair["source_entity_name"] == "Jane Smith"
        and pair["target_entity_name"] == "John Doe"
        and pair["message_count"] == 1
        for pair in dashboard["communication_pairs"]
    )

    filtered_response = client.get(
        "/api/analytics/dashboard",
        params={"matter_id": matter.id, "custodian_id": custodian.id, "date_from": "2024-03-05", "date_to": "2024-03-05"},
    )
    assert filtered_response.status_code == 200
    filtered = filtered_response.json()
    assert filtered["snapshot"]["document_count"] == 1
    assert filtered["file_type_distribution"] == [{"label": "eml", "count": 1}]

    export_response = client.get(
        "/api/analytics/export.csv",
        params={"matter_id": matter.id, "custodian_id": custodian.id},
    )
    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("text/csv")
    assert "communication_pair" in export_response.text


def test_analytics_snapshot_returns_counts(client: TestClient) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("snapshot.txt", b"Jane Smith met Acme Corp.", "text/plain")},
    )
    assert response.status_code == 200

    snapshot_response = client.get("/api/analytics/snapshot")

    assert snapshot_response.status_code == 200
    snapshot = snapshot_response.json()
    assert snapshot["document_count"] == 1
    assert snapshot["entity_count"] > 0
    assert snapshot["file_type_counts"] == {"txt": 1}
