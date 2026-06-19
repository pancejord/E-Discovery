from dataclasses import dataclass
from datetime import UTC, datetime
from email import message_from_binary_file
from email.message import Message
from email.utils import parsedate_to_datetime
from pathlib import Path
import re

from docx import Document as DocxDocument
from pypdf import PdfReader
from pypdf.errors import PdfReadError


@dataclass(frozen=True)
class ExtractedDocument:
    text: str
    document_type: str | None = None
    warnings: tuple[str, ...] = ()
    attachment_names: tuple[str, ...] = ()
    ocr_status: str | None = None
    sender: str | None = None
    recipients: str | None = None
    cc: str | None = None
    bcc: str | None = None
    subject: str | None = None
    document_date: datetime | None = None


def extract_document(path: Path, file_type: str) -> ExtractedDocument:
    extension = file_type.lower().lstrip(".")
    if extension == "pdf":
        text, warnings, ocr_status = _extract_pdf(path)
        return ExtractedDocument(
            text=text,
            document_type=_classify_text(path.name, text, fallback="pdf"),
            warnings=tuple(warnings),
            ocr_status=ocr_status,
            document_date=_extract_first_date(text),
        )
    if extension == "docx":
        text, warnings = _extract_docx(path)
        return ExtractedDocument(
            text=text,
            document_type=_classify_text(path.name, text, fallback="document"),
            warnings=tuple(warnings),
            document_date=_extract_first_date(text),
        )
    if extension == "eml":
        return _extract_email(path)
    if extension in {"txt", "md", "csv", "tsv", "log"}:
        text = _read_text(path)
        return ExtractedDocument(
            text=text,
            document_type=_classify_text(path.name, text),
            document_date=_extract_first_date(text),
        )
    return ExtractedDocument(text="", document_type=extension or None)


def _extract_pdf(path: Path) -> tuple[str, list[str], str | None]:
    warnings = []
    try:
        reader = PdfReader(str(path))
    except PdfReadError as error:
        return "", [f"PDF extraction failed: {error}"], "failed"
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            return "", ["PDF is encrypted and could not be decrypted."], "blocked_encrypted"

    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception as error:
            warnings.append(f"Page {page_number} text extraction failed: {error}")
            page_text = ""
        if page_text.strip():
            pages.append(f"[Page {page_number}]\n{page_text.strip()}")
    text = "\n\n".join(pages)
    ocr_status = "recommended" if not text.strip() and len(reader.pages) > 0 else "not_required"
    if ocr_status == "recommended":
        warnings.append("No extractable PDF text found; OCR is recommended.")
    return text, warnings, ocr_status


def _extract_docx(path: Path) -> tuple[str, list[str]]:
    try:
        document = DocxDocument(str(path))
    except Exception as error:
        return "", [f"DOCX extraction failed: {error}"]
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    table_rows = []
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                table_rows.append(" | ".join(cells))
    sections = paragraphs + table_rows
    return "\n\n".join(sections), []


def _extract_email(path: Path) -> ExtractedDocument:
    with path.open("rb") as file:
        message = message_from_binary_file(file)
    body, attachment_names, attachment_texts, warnings = _email_parts(message)
    text_sections = [body, *attachment_texts]
    return ExtractedDocument(
        text="\n\n".join(section.strip() for section in text_sections if section.strip()),
        document_type="email",
        warnings=tuple(warnings),
        attachment_names=tuple(attachment_names),
        sender=message.get("From"),
        recipients=message.get("To"),
        cc=message.get("Cc"),
        bcc=message.get("Bcc"),
        subject=message.get("Subject"),
        document_date=_normalize_datetime(_parse_email_date(message.get("Date"))),
    )


def _email_parts(message: Message) -> tuple[str, list[str], list[str], list[str]]:
    body_parts = []
    attachment_names = []
    attachment_texts = []
    warnings = []
    if message.is_multipart():
        for part in message.walk():
            disposition = str(part.get("Content-Disposition", "")).lower()
            filename = part.get_filename()
            if filename:
                attachment_names.append(filename)
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            content_type = part.get_content_type()
            decoded = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
            if content_type == "text/plain" and "attachment" not in disposition:
                body_parts.append(decoded)
            elif content_type in {"text/plain", "text/csv"} or _is_text_attachment(filename):
                attachment_texts.append(f"[Attachment: {filename or 'unnamed'}]\n{decoded}")
            elif "attachment" in disposition:
                warnings.append(f"Attachment not text-extracted: {filename or content_type}")
        return (
            "\n\n".join(part.strip() for part in body_parts if part.strip()),
            attachment_names,
            attachment_texts,
            warnings,
        )

    payload = message.get_payload(decode=True)
    if payload is None:
        return str(message.get_payload() or ""), attachment_names, attachment_texts, warnings
    return payload.decode(message.get_content_charset() or "utf-8", errors="replace"), attachment_names, attachment_texts, warnings


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


def _classify_text(filename: str, text: str, fallback: str = "text") -> str:
    lowered = f"{filename}\n{text[:1000]}".lower()
    if "response to request for production" in lowered or "request for production no." in lowered:
        return "discovery_response"
    if "legal memo" in lowered or "legal memorandum" in lowered:
        return "legal_memo"
    if "non-disclosure" in lowered or "nda" in lowered:
        return "nda"
    if "invoice" in lowered or "amount due" in lowered or re.search(r"\binv-\d+", lowered):
        return "invoice"
    if "court order" in lowered or lowered.startswith("order "):
        return "court_order"
    if "motion" in lowered or "memorandum of law" in lowered or "complaint" in lowered:
        return "pleading"
    if "slack export" in lowered or "chat export" in lowered:
        return "chat_export"
    if "agreement" in lowered or "contract" in lowered:
        return "contract"
    return fallback


def _extract_first_date(text: str) -> datetime | None:
    match = re.search(
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
        r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2},?\s+\d{4}\b",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y"):
        try:
            return _normalize_datetime(datetime.strptime(match.group(0).replace(".", ""), fmt))
        except ValueError:
            continue
    return None


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _is_text_attachment(filename: str | None) -> bool:
    return bool(filename and Path(filename).suffix.lower() in {".txt", ".csv", ".tsv", ".md", ".log"})
