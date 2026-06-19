from collections.abc import Generator
from datetime import UTC
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
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


def test_email_attachment_inventory_and_text_extraction(client: TestClient) -> None:
    email = (
        b"From: Maria Chen <maria@example.com>\r\n"
        b"To: Daniel Ortiz <daniel@example.com>\r\n"
        b"Date: Mon, 14 Apr 2025 09:12:00 -0400\r\n"
        b"Subject: Attachment Test\r\n"
        b"MIME-Version: 1.0\r\n"
        b"Content-Type: multipart/mixed; boundary=BOUNDARY\r\n\r\n"
        b"--BOUNDARY\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n\r\n"
        b"Please review the attached invoice.\r\n"
        b"--BOUNDARY\r\n"
        b"Content-Type: text/plain; name=notes.txt\r\n"
        b"Content-Disposition: attachment; filename=notes.txt\r\n\r\n"
        b"Invoice INV-1042 includes expedited review.\r\n"
        b"--BOUNDARY--\r\n"
    )
    upload = client.post(
        "/documents/upload",
        files={"file": ("attachment-email.eml", email, "message/rfc822")},
    )
    assert upload.status_code == 200

    detail = client.get(f"/documents/{upload.json()['id']}").json()
    assert detail["document_type"] == "email"
    assert detail["attachment_names"] == ["notes.txt"]
    assert "INV-1042" in detail["extracted_text"]
    assert detail["document_date"].startswith("2025-04-14T13:12:00")


def test_richer_classification_and_entity_alias_dedup(client: TestClient) -> None:
    text = (
        "Legal memo dated April 15, 2025. Acme Corporation reviewed the disputed invoice. "
        "Acme Corp requested backup documentation."
    )
    upload = client.post(
        "/documents/upload",
        files={"file": ("risk-memo.txt", text.encode("utf-8"), "text/plain")},
    )
    assert upload.status_code == 200

    detail = client.get(f"/documents/{upload.json()['id']}").json()
    assert detail["document_type"] == "legal_memo"
    assert detail["document_date"].startswith("2025-04-15T00:00:00")

    entities = client.get("/api/entities", params={"q": "acme corp"}).json()
    orgs = [entity for entity in entities if entity["entity_type"] == "ORGANIZATION"]
    assert len(orgs) == 1
    assert orgs[0]["mention_count"] == 2


def test_blank_pdf_is_flagged_for_ocr(client: TestClient, tmp_path: Path) -> None:
    pdf_path = tmp_path / "blank.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with pdf_path.open("wb") as handle:
        writer.write(handle)

    with pdf_path.open("rb") as handle:
        upload = client.post(
            "/documents/upload",
            files={"file": ("blank.pdf", handle.read(), "application/pdf")},
        )
    assert upload.status_code == 200
    assert upload.json()["processing_status"] == "needs_ocr"

    detail = client.get(f"/documents/{upload.json()['id']}").json()
    assert detail["ocr_status"] == "recommended"
    assert any("OCR is recommended" in warning for warning in detail["extraction_warnings"])
