from fastapi import APIRouter, File, UploadFile

from app.models.schemas import DocumentIngestionResult, DocumentSummary
from app.services.ingestion import inspect_upload

router = APIRouter()


@router.get("", response_model=list[DocumentSummary])
def list_documents() -> list[DocumentSummary]:
    return []


@router.post("/upload", response_model=DocumentIngestionResult)
async def upload_document(file: UploadFile = File(...)) -> DocumentIngestionResult:
    return await inspect_upload(file)
