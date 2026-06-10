from dataclasses import dataclass
from datetime import datetime
from email import message_from_binary_file
from email.message import Message
from email.utils import parsedate_to_datetime
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


@dataclass(frozen=True)
class ExtractedDocument:
    text: str
    document_type: str | None = None
    sender: str | None = None
    recipients: str | None = None
    cc: str | None = None
    bcc: str | None = None
    subject: str | None = None
    document_date: datetime | None = None


def extract_document(path: Path, file_type: str) -> ExtractedDocument:
    extension = file_type.lower().lstrip(".")
    if extension == "pdf":
        return ExtractedDocument(text=_extract_pdf(path), document_type="pdf")
    if extension == "docx":
        return ExtractedDocument(text=_extract_docx(path), document_type="document")
    if extension == "eml":
        return _extract_email(path)
    if extension in {"txt", "md", "csv", "tsv", "log"}:
        text = _read_text(path)
        return ExtractedDocument(text=text, document_type=_classify_text(path.name, text))
    return ExtractedDocument(text="", document_type=extension or None)


def _extract_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append(f"[Page {page_number}]\n{page_text.strip()}")
    return "\n\n".join(pages)


def _extract_docx(path: Path) -> str:
    document = DocxDocument(str(path))
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n\n".join(paragraphs)


def _extract_email(path: Path) -> ExtractedDocument:
    with path.open("rb") as file:
        message = message_from_binary_file(file)
    return ExtractedDocument(
        text=_email_body(message),
        document_type="email",
        sender=message.get("From"),
        recipients=message.get("To"),
        cc=message.get("Cc"),
        bcc=message.get("Bcc"),
        subject=message.get("Subject"),
        document_date=_parse_email_date(message.get("Date")),
    )


def _email_body(message: Message) -> str:
    if message.is_multipart():
        parts = []
        for part in message.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition", "")):
                payload = part.get_payload(decode=True)
                if payload:
                    parts.append(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
        return "\n\n".join(part.strip() for part in parts if part.strip())

    payload = message.get_payload(decode=True)
    if payload is None:
        return str(message.get_payload() or "")
    return payload.decode(message.get_content_charset() or "utf-8", errors="replace")


def _read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-16", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_email_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None


def _classify_text(filename: str, text: str) -> str:
    lowered = f"{filename}\n{text[:1000]}".lower()
    if "non-disclosure" in lowered or "nda" in lowered:
        return "nda"
    if "invoice" in lowered or "amount due" in lowered:
        return "invoice"
    if "motion" in lowered or "memorandum of law" in lowered:
        return "pleading"
    if "agreement" in lowered or "contract" in lowered:
        return "contract"
    return "text"
