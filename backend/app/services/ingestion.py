from fastapi import UploadFile

from app.models.schemas import DocumentIngestionResult


async def inspect_upload(file: UploadFile) -> DocumentIngestionResult:
    contents = await file.read()
    return DocumentIngestionResult(
        filename=file.filename or "untitled",
        content_type=file.content_type,
        size_bytes=len(contents),
    )
