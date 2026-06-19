from pathlib import Path
from hashlib import sha256
import json
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.schemas import DocumentIngestionResult
from app.services.chunking import chunk_text
from app.services.embeddings import EMBEDDING_MODEL, embed_text
from app.services.entity_extraction import process_document_entities
from app.services.text_extraction import extract_document
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
        document_type=extracted.document_type,
        extracted_text=extracted.text,
        text_hash=sha256(extracted.text.encode("utf-8")).hexdigest() if extracted.text else None,
        extraction_warnings=json.dumps(list(extracted.warnings)) if extracted.warnings else None,
        attachment_names=json.dumps(list(extracted.attachment_names)) if extracted.attachment_names else None,
        ocr_status=extracted.ocr_status,
        sender=extracted.sender,
        recipients=extracted.recipients,
        cc=extracted.cc,
        bcc=extracted.bcc,
        subject=extracted.subject,
        document_date=extracted.document_date,
        processing_status="parsed" if extracted.text else "needs_ocr" if extracted.ocr_status == "recommended" else "uploaded",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    chunks = []
    for text_chunk in chunk_text(extracted.text):
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
            try:
                index_chunk(document, chunk)
            except Exception:
                pass
        process_document_entities(db, document, chunks)

    return DocumentIngestionResult(
        id=document.id,
        original_filename=document.original_filename,
        stored_file_path=document.stored_file_path,
        file_type=document.file_type,
        content_type=file.content_type,
        size_bytes=size_bytes,
        processing_status=document.processing_status,
    )


def get_document_or_404(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
