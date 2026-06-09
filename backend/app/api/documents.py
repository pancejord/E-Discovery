from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.custodian import Custodian
from app.models.document import Document
from app.models.matter import Matter
from app.models.schemas import DocumentDetail, DocumentIngestionResult, DocumentSummary
from app.services.ingestion import get_document_or_404, ingest_upload

router = APIRouter()


@router.get("", response_model=list[DocumentSummary])
def list_documents(
    db: Session = Depends(get_db),
    matter_id: int | None = None,
    custodian_id: int | None = None,
    processing_status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Document]:
    statement = select(Document)
    if matter_id is not None:
        statement = statement.where(Document.matter_id == matter_id)
    if custodian_id is not None:
        statement = statement.where(Document.custodian_id == custodian_id)
    if processing_status is not None:
        statement = statement.where(Document.processing_status == processing_status)
    statement = statement.order_by(Document.created_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(statement))


@router.post("/upload", response_model=DocumentIngestionResult)
async def upload_document(
    file: UploadFile = File(...),
    matter_id: int | None = Form(None),
    custodian_id: int | None = Form(None),
    db: Session = Depends(get_db),
) -> DocumentIngestionResult:
    if matter_id is not None and db.get(Matter, matter_id) is None:
        raise HTTPException(status_code=400, detail="matter_id does not exist")
    if custodian_id is not None and db.get(Custodian, custodian_id) is None:
        raise HTTPException(status_code=400, detail="custodian_id does not exist")
    return await ingest_upload(db, file, matter_id=matter_id, custodian_id=custodian_id)


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: int, db: Session = Depends(get_db)) -> Document:
    return get_document_or_404(db, document_id)


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)) -> Response:
    document = get_document_or_404(db, document_id)
    stored_path = Path(document.stored_file_path)

    db.delete(document)
    db.commit()

    if stored_path.exists():
        stored_path.unlink()

    return Response(status_code=204)
