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


def test_upload_list_detail_and_delete_document(client: TestClient) -> None:
    document_text = (
        "Jane Smith and Acme Corp signed a contract for $12,500 on March 3, 2024 "
        "under Rule 26."
    )
    response = client.post(
        "/documents/upload",
        files={"file": ("contract.txt", document_text.encode("utf-8"), "text/plain")},
    )

    assert response.status_code == 200
    uploaded = response.json()
    assert uploaded["original_filename"] == "contract.txt"
    assert uploaded["file_type"] == "txt"
    assert uploaded["processing_status"] == "parsed"
    stored_path = Path(uploaded["stored_file_path"])
    assert stored_path.exists()

    list_response = client.get("/documents")
    assert list_response.status_code == 200
    documents = list_response.json()
    assert len(documents) == 1
    assert documents[0]["id"] == uploaded["id"]

    detail_response = client.get(f"/documents/{uploaded['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["stored_file_path"] == str(stored_path)
    assert detail["extracted_text"] == document_text
    assert detail["document_type"] == "contract"
    assert detail["chunks"]
    assert any(mention["entity_name"] == "Acme Corp" for mention in detail["entity_mentions"])
    assert any(relationship["relationship_type"] == "mentioned_with" for relationship in detail["relationships"])

    search_response = client.post("/api/search", json={"query": "contract", "limit": 5})
    assert search_response.status_code == 200
    search_results = search_response.json()["results"]
    assert len(search_results) == 1
    assert search_results[0]["document_id"] == uploaded["id"]
    assert "contract" in search_results[0]["snippet"].lower()
    assert search_results[0]["citation"].startswith("contract.txt#chunk-1")

    entities_response = client.get("/api/entities")
    assert entities_response.status_code == 200
    entity_types = {entity["entity_type"] for entity in entities_response.json()}
    assert {"PERSON", "ORGANIZATION", "MONEY", "DATE", "LEGAL_REFERENCE"} <= entity_types

    acme_response = client.get("/api/entities", params={"q": "acme"})
    assert acme_response.status_code == 200
    acme = acme_response.json()[0]
    assert acme["name"] == "Acme Corp"
    assert acme["mention_count"] == 1

    acme_detail_response = client.get(f"/api/entities/{acme['id']}")
    assert acme_detail_response.status_code == 200
    acme_detail = acme_detail_response.json()
    assert acme_detail["mentions"][0]["citation"].startswith("contract.txt#chunk-1")

    relationships_response = client.get(f"/api/entities/{acme['id']}/relationships")
    assert relationships_response.status_code == 200
    assert any(
        relationship["relationship_type"] == "mentioned_with"
        for relationship in relationships_response.json()
    )

    delete_response = client.delete(f"/documents/{uploaded['id']}")
    assert delete_response.status_code == 204
    assert not stored_path.exists()


def test_upload_accepts_existing_matter_and_custodian(client: TestClient) -> None:
    db = next(app.dependency_overrides[get_db]())
    matter = Matter(name="Acme v. Smith", client_name="Acme Corp", matter_number="ACME-001")
    custodian = Custodian(full_name="Jane Reviewer", email="jane@example.com")
    db.add_all([matter, custodian])
    db.commit()
    db.refresh(matter)
    db.refresh(custodian)
    db.close()

    response = client.post(
        "/documents/upload",
        data={"matter_id": str(matter.id), "custodian_id": str(custodian.id)},
        files={
            "file": (
                "email.eml",
                b"From: Jane Smith <jane@example.com>\r\n"
                b"To: John Doe <john@example.com>\r\n"
                b"Subject: Test\r\n\r\nBody",
                "message/rfc822",
            )
        },
    )

    assert response.status_code == 200
    detail_response = client.get(f"/documents/{response.json()['id']}")
    detail = detail_response.json()
    assert detail["matter_id"] == matter.id
    assert detail["custodian_id"] == custodian.id
    assert detail["subject"] == "Test"
    assert detail["document_type"] == "email"

    jane_response = client.get("/api/entities", params={"matter_id": matter.id, "q": "jane smith"})
    assert jane_response.status_code == 200
    jane = jane_response.json()[0]
    relationship_response = client.get(f"/api/entities/{jane['id']}/relationships")
    assert relationship_response.status_code == 200
    assert any(
        relationship["relationship_type"] == "communicated_with"
        and relationship["target_entity_name"] == "John Doe"
        for relationship in relationship_response.json()
    )


def test_upload_rejects_unknown_matter(client: TestClient) -> None:
    response = client.post(
        "/documents/upload",
        data={"matter_id": "999"},
        files={"file": ("orphan.txt", b"orphan", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "matter_id does not exist"
