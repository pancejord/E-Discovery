from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.schemas import DocumentIngestionResult
from app.utils.file_utils import file_extension, save_upload_file


async def ingest_upload(
    db: Session,
    file: UploadFile,
    matter_id: int | None = None,
    custodian_id: int | None = None,
) -> DocumentIngestionResult:
    stored_path, size_bytes = await save_upload_file(file, Path(settings.upload_dir))

    document = Document(
        matter_id=matter_id,
        custodian_id=custodian_id,
        original_filename=file.filename or "untitled",
        stored_file_path=str(stored_path),
        file_type=file_extension(file.filename),
        processing_status="uploaded",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

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
