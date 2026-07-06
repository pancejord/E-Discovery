from collections.abc import Generator
from datetime import UTC
from pathlib import Path
import base64
import subprocess
import zipfile

import pytest
from fastapi.testclient import TestClient
from docx import Document as DocxDocument
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
    assert len(detail["child_documents"]) == 1
    assert detail["child_documents"][0]["attachment_filename"] == "notes.txt"
    assert "INV-1042" in detail["extracted_text"]
    assert detail["document_date"].startswith("2025-04-14T13:12:00")
    assert detail["processing_stages"]["extracted"] == "completed"

    child_detail = client.get(f"/documents/{detail['child_documents'][0]['id']}").json()
    assert child_detail["parent_document_id"] == upload.json()["id"]
    assert "INV-1042" in child_detail["extracted_text"]


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


def test_blank_pdf_runs_configured_ocr(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = tmp_path / "blank-ocr.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with pdf_path.open("wb") as handle:
        writer.write(handle)

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="OCR text for scanned invoice INV-2048", stderr="")

    monkeypatch.setattr(settings, "ocr_enabled", True)
    monkeypatch.setattr(settings, "ocr_pdf_to_text_command", "fake-ocr {input}")
    monkeypatch.setattr("app.services.text_extraction.subprocess.run", fake_run)

    with pdf_path.open("rb") as handle:
        upload = client.post(
            "/documents/upload",
            files={"file": ("blank-ocr.pdf", handle.read(), "application/pdf")},
        )
    assert upload.status_code == 200
    assert upload.json()["processing_status"] == "parsed"

    detail = client.get(f"/documents/{upload.json()['id']}").json()
    assert detail["ocr_status"] == "completed"
    assert "INV-2048" in detail["extracted_text"]


def test_email_binary_docx_attachment_is_text_extracted(client: TestClient, tmp_path: Path) -> None:
    docx_path = tmp_path / "attachment.docx"
    document = DocxDocument()
    document.add_paragraph("Binary attachment memorandum mentions Northwind delay fees.")
    document.save(docx_path)
    encoded = base64.b64encode(docx_path.read_bytes())

    email = (
        b"From: Maria Chen <maria@example.com>\r\n"
        b"To: Daniel Ortiz <daniel@example.com>\r\n"
        b"Subject: Binary Attachment\r\n"
        b"MIME-Version: 1.0\r\n"
        b"Content-Type: multipart/mixed; boundary=BOUNDARY\r\n\r\n"
        b"--BOUNDARY\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n\r\n"
        b"Please review the attached memo.\r\n"
        b"--BOUNDARY\r\n"
        b"Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document; name=attachment.docx\r\n"
        b"Content-Disposition: attachment; filename=attachment.docx\r\n"
        b"Content-Transfer-Encoding: base64\r\n\r\n"
        + encoded
        + b"\r\n--BOUNDARY--\r\n"
    )

    upload = client.post(
        "/documents/upload",
        files={"file": ("binary-attachment.eml", email, "message/rfc822")},
    )
    assert upload.status_code == 200

    detail = client.get(f"/documents/{upload.json()['id']}").json()
    assert detail["attachment_names"] == ["attachment.docx"]
    assert detail["child_documents"][0]["attachment_filename"] == "attachment.docx"
    assert "Northwind delay fees" in detail["extracted_text"]
    assert detail["extraction_warnings"] == []


def test_reprocess_rebuilds_document_text_and_stages(client: TestClient) -> None:
    upload = client.post(
        "/documents/upload",
        files={"file": ("reprocess.txt", b"Initial text for indexing.", "text/plain")},
    )
    assert upload.status_code == 200
    detail = client.get(f"/documents/{upload.json()['id']}").json()
    Path(detail["stored_file_path"]).write_text("Updated text after retry with Falcon issue.", encoding="utf-8")

    response = client.post(f"/documents/{upload.json()['id']}/reprocess")

    assert response.status_code == 200
    updated = response.json()
    assert "Falcon issue" in updated["extracted_text"]
    assert updated["processing_stages"]["chunked"] == "completed"
    assert updated["processing_stages"]["entity_extraction"] == "completed"


def test_html_rtf_xlsx_and_zip_extraction(client: TestClient, tmp_path: Path) -> None:
    html = client.post(
        "/documents/upload",
        files={"file": ("page.html", b"<html><body><h1>Falcon HTML issue</h1></body></html>", "text/html")},
    )
    assert html.status_code == 200
    assert "Falcon HTML issue" in client.get(f"/documents/{html.json()['id']}").json()["extracted_text"]

    rtf = client.post(
        "/documents/upload",
        files={"file": ("note.rtf", b"{\\rtf1\\ansi Falcon RTF issue}", "application/rtf")},
    )
    assert rtf.status_code == 200
    assert "Falcon RTF issue" in client.get(f"/documents/{rtf.json()['id']}").json()["extracted_text"]

    xlsx_path = tmp_path / "sheet.xlsx"
    with zipfile.ZipFile(xlsx_path, "w") as workbook:
        workbook.writestr(
            "xl/sharedStrings.xml",
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>Falcon XLSX issue</t></si></sst>',
        )
        workbook.writestr(
            "xl/worksheets/sheet1.xml",
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row><c t="s"><v>0</v></c></row></sheetData></worksheet>',
        )
    xlsx = client.post(
        "/documents/upload",
        files={"file": ("sheet.xlsx", xlsx_path.read_bytes(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert xlsx.status_code == 200
    assert "Falcon XLSX issue" in client.get(f"/documents/{xlsx.json()['id']}").json()["extracted_text"]

    zip_path = tmp_path / "archive.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("inside.txt", "Falcon ZIP issue")
    archive_response = client.post(
        "/documents/upload",
        files={"file": ("archive.zip", zip_path.read_bytes(), "application/zip")},
    )
    assert archive_response.status_code == 200
    archive_detail = client.get(f"/documents/{archive_response.json()['id']}").json()
    assert "Falcon ZIP issue" in archive_detail["extracted_text"]
    assert archive_detail["attachment_names"] == ["inside.txt"]
