from pathlib import Path
from hashlib import sha256
import json
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.entity_mention import EntityMention
from app.models.relationship import Relationship
from app.models.schemas import DocumentIngestionResult
from app.services.chunking import chunk_text
from app.services.embeddings import EMBEDDING_MODEL, embed_text
from app.services.entity_extraction import process_document_entities
from app.services.audit import record_audit_event
from app.services.text_extraction import ExtractedAttachment, ExtractedDocument, extract_document
from app.services.vector_store import index_chunk
from app.utils.file_utils import file_extension, save_upload_file


async def ingest_upload(
    db: Session,
    file: UploadFile,
    matter_id: int | None = None,
    custodian_id: int | None = None,
) -> DocumentIngestionResult:
    stored_path, size_bytes = await save_upload_file(file, Path(settings.upload_dir))
    extension = file_extension(file.filename)
    extracted = extract_document(stored_path, extension)

    document = Document(
        matter_id=matter_id,
        custodian_id=custodian_id,
        original_filename=file.filename or "untitled",
        stored_file_path=str(stored_path),
        file_type=extension,
        processing_status="uploaded",
        processing_stages=json.dumps({"uploaded": "completed"}),
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    process_extracted_document(db, document, extracted)
    _persist_child_attachments(db, document, extracted.attachments)

    return DocumentIngestionResult(
        id=document.id,
        original_filename=document.original_filename,
        stored_file_path=document.stored_file_path,
        file_type=document.file_type,
        content_type=file.content_type,
        size_bytes=size_bytes,
        processing_status=document.processing_status,
    )


def reprocess_document(db: Session, document: Document) -> Document:
    extracted = extract_document(Path(document.stored_file_path), document.file_type)
    process_extracted_document(db, document, extracted, clear_existing=True)
    return document


def process_extracted_document(
    db: Session,
    document: Document,
    extracted: ExtractedDocument,
    *,
    clear_existing: bool = False,
) -> None:
    stages = _stages(document)
    try:
        if clear_existing:
            _clear_derived_data(db, document)
        stages["extracted"] = "completed" if extracted.text else "empty"
        if extracted.ocr_status == "completed":
            stages["ocr"] = "completed"
        elif extracted.ocr_status == "recommended":
            stages["ocr"] = "recommended"
        elif extracted.ocr_status:
            stages["ocr"] = extracted.ocr_status
        _apply_extraction(document, extracted, stages)
        db.commit()
        db.refresh(document)
        _audit_ocr_warnings(db, document, extracted)

        chunks = _replace_chunks(db, document, extracted.text)
        stages["chunked"] = "completed" if chunks else "empty"
        stages["indexed"] = "skipped"
        if chunks:
            stages["indexed"] = _index_chunks(db, document, chunks)
            process_document_entities(db, document, chunks)
            stages["entity_extraction"] = "completed"
        else:
            stages["entity_extraction"] = "skipped"
        document.processing_stages = json.dumps(stages)
        document.processing_error = None
        db.commit()
    except Exception as error:
        stages["failed"] = "true"
        document.processing_status = "failed"
        document.processing_error = str(error)
        document.processing_stages = json.dumps(stages)
        db.commit()
        raise


def get_document_or_404(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


def _apply_extraction(document: Document, extracted: ExtractedDocument, stages: dict[str, str]) -> None:
    document.document_type = extracted.document_type
    document.extracted_text = extracted.text
    document.text_hash = sha256(extracted.text.encode("utf-8")).hexdigest() if extracted.text else None
    document.extraction_warnings = json.dumps(list(extracted.warnings)) if extracted.warnings else None
    document.attachment_names = json.dumps(list(extracted.attachment_names)) if extracted.attachment_names else None
    document.ocr_status = extracted.ocr_status
    document.sender = extracted.sender
    document.recipients = extracted.recipients
    document.cc = extracted.cc
    document.bcc = extracted.bcc
    document.subject = extracted.subject
    document.document_date = extracted.document_date
    document.processing_status = "parsed" if extracted.text else "needs_ocr" if extracted.ocr_status == "recommended" else "uploaded"
    document.processing_stages = json.dumps(stages)


def _replace_chunks(db: Session, document: Document, text: str) -> list[DocumentChunk]:
    chunks = []
    for text_chunk in chunk_text(text):
        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=text_chunk.chunk_index,
            text=text_chunk.text,
            text_hash=text_chunk.text_hash,
            char_start=text_chunk.char_start,
            char_end=text_chunk.char_end,
            token_count=text_chunk.token_count,
            vector_id=str(uuid4()),
            embedding=embed_text(text_chunk.text),
            embedding_model=EMBEDDING_MODEL,
        )
        chunks.append(chunk)
        db.add(chunk)
    if chunks:
        db.commit()
        for chunk in chunks:
            db.refresh(chunk)
    return chunks


def _index_chunks(db: Session, document: Document, chunks: list[DocumentChunk]) -> str:
    status = "completed"
    for chunk in chunks:
        try:
            index_chunk(document, chunk)
        except Exception as error:
            status = "failed"
            record_audit_event(
                db,
                action="vector.index_failure",
                actor=None,
                matter_id=document.matter_id,
                document_id=document.id,
                summary="Vector indexing failed for document chunk",
                details={
                    "filename": document.original_filename,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "error": str(error),
                },
            )
    return status


def _persist_child_attachments(db: Session, parent: Document, attachments: tuple[ExtractedAttachment, ...]) -> None:
    for attachment in attachments:
        child_path = _store_attachment_payload(parent, attachment)
        child = Document(
            parent_document_id=parent.id,
            matter_id=parent.matter_id,
            custodian_id=parent.custodian_id,
            original_filename=attachment.filename,
            attachment_filename=attachment.filename,
            stored_file_path=str(child_path),
            file_type=attachment.file_type,
            processing_status="uploaded",
            processing_stages=json.dumps({"uploaded": "completed", "family_attachment": "completed"}),
        )
        db.add(child)
        db.commit()
        db.refresh(child)
        extracted = ExtractedDocument(
            text=attachment.text,
            document_type=attachment.document_type,
            warnings=attachment.warnings,
            ocr_status=attachment.ocr_status,
            document_date=attachment.document_date,
        )
        process_extracted_document(db, child, extracted)
        record_audit_event(
            db,
            action="document.child_created",
            actor=None,
            matter_id=child.matter_id,
            document_id=child.id,
            summary=f"Created child document for attachment {attachment.filename}",
            details={"parent_document_id": parent.id, "attachment_filename": attachment.filename},
        )


def _store_attachment_payload(parent: Document, attachment: ExtractedAttachment) -> Path:
    attachment_dir = Path(settings.upload_dir) / "attachments" / str(parent.id)
    attachment_dir.mkdir(parents=True, exist_ok=True)
    target = attachment_dir / Path(attachment.filename).name
    target.write_bytes(attachment.payload)
    return target


def _clear_derived_data(db: Session, document: Document) -> None:
    db.execute(delete(EntityMention).where(EntityMention.document_id == document.id))
    db.execute(delete(Relationship).where(Relationship.document_id == document.id))
    db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
    db.commit()


def _audit_ocr_warnings(db: Session, document: Document, extracted: ExtractedDocument) -> None:
    for warning in extracted.warnings:
        if warning.startswith("OCR ") or "OCR" in warning:
            record_audit_event(
                db,
                action="ocr.failure",
                actor=None,
                matter_id=document.matter_id,
                document_id=document.id,
                summary="OCR command did not produce searchable text",
                details={"filename": document.original_filename, "warning": warning},
            )


def _stages(document: Document) -> dict[str, str]:
    if not document.processing_stages:
        return {}
    try:
        parsed = json.loads(document.processing_stages)
    except json.JSONDecodeError:
        return {}
    return {str(key): str(value) for key, value in parsed.items()} if isinstance(parsed, dict) else {}
