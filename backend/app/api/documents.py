from pathlib import Path
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import Actor, accessible_matter_ids, get_actor, require_matter_access, require_scoped_write_matter
from app.database import get_db
from app.models.chunk import DocumentChunk
from app.models.custodian import Custodian
from app.models.document import Document
from app.models.entity import Entity
from app.models.entity_mention import EntityMention
from app.models.matter import Matter
from app.models.relationship import Relationship
from app.models.schemas import (
    ChunkRead,
    DocumentDetail,
    DocumentEntityMention,
    DocumentIngestionResult,
    DocumentSummary,
    RelationshipSummary,
)
from app.services.ingestion import get_document_or_404, ingest_upload
from app.services.audit import record_audit_event

router = APIRouter()


@router.get("", response_model=list[DocumentSummary])
def list_documents(
    db: Session = Depends(get_db),
    matter_id: int | None = None,
    custodian_id: int | None = None,
    processing_status: str | None = None,
    limit: int = 100,
    offset: int = 0,
    actor: Actor = Depends(get_actor),
) -> list[Document]:
    require_matter_access(db, actor, matter_id)
    matter_ids = accessible_matter_ids(db, actor)
    statement = select(Document)
    if matter_id is not None:
        statement = statement.where(Document.matter_id == matter_id)
    elif matter_ids is not None:
        statement = statement.where(Document.matter_id.in_(matter_ids))
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
    actor: Actor = Depends(get_actor),
) -> DocumentIngestionResult:
    require_scoped_write_matter(db, actor, matter_id)
    if matter_id is not None and db.get(Matter, matter_id) is None:
        raise HTTPException(status_code=400, detail="matter_id does not exist")
    if custodian_id is not None and db.get(Custodian, custodian_id) is None:
        raise HTTPException(status_code=400, detail="custodian_id does not exist")
    try:
        result = await ingest_upload(db, file, matter_id=matter_id, custodian_id=custodian_id)
    except Exception as error:
        record_audit_event(
            db,
            action="document.ingestion_failed",
            actor=actor.name,
            matter_id=matter_id,
            summary=f"Failed to ingest {file.filename or 'upload'}",
            details={"error": str(error)},
        )
        raise
    record_audit_event(
        db,
        action="document.upload",
        actor=actor.name,
        matter_id=matter_id,
        document_id=result.id,
        summary=f"Uploaded {result.original_filename}",
        details={"file_type": result.file_type, "processing_status": result.processing_status},
    )
    return result


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> DocumentDetail:
    document = get_document_or_404(db, document_id)
    require_matter_access(db, actor, document.matter_id)
    chunks = list(
        db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.chunk_index)
        )
    )
    mentions = []
    mention_rows = db.execute(
        select(EntityMention, Entity)
        .join(Entity, EntityMention.entity_id == Entity.id)
        .where(EntityMention.document_id == document.id)
        .order_by(EntityMention.char_start, EntityMention.id)
    ).all()
    for mention, entity in mention_rows:
        mentions.append(
            DocumentEntityMention(
                id=mention.id,
                entity_id=entity.id,
                entity_name=entity.name,
                entity_type=entity.entity_type,
                chunk_id=mention.chunk_id,
                mention_text=mention.mention_text,
                char_start=mention.char_start,
                char_end=mention.char_end,
                citation=mention.citation,
            )
        )

    relationship_rows = list(
        db.scalars(
            select(Relationship)
            .where(Relationship.document_id == document.id)
            .order_by(Relationship.relationship_type, Relationship.id)
        )
    )
    relationships = []
    for relationship in relationship_rows:
        source = db.get(Entity, relationship.source_entity_id)
        target = db.get(Entity, relationship.target_entity_id)
        relationships.append(
            RelationshipSummary(
                id=relationship.id,
                matter_id=relationship.matter_id,
                source_entity_id=relationship.source_entity_id,
                source_entity_name=source.name if source else "",
                relationship_type=relationship.relationship_type,
                target_entity_id=relationship.target_entity_id,
                target_entity_name=target.name if target else "",
                document_id=relationship.document_id,
                confidence=relationship.confidence,
                evidence=relationship.evidence,
            )
        )

    record_audit_event(
        db,
        action="document.view",
        actor=actor.name,
        matter_id=document.matter_id,
        document_id=document.id,
        summary=f"Viewed {document.original_filename}",
    )
    return DocumentDetail(
        **DocumentSummary.model_validate(document).model_dump(),
        stored_file_path=document.stored_file_path,
        extracted_text=document.extracted_text,
        text_hash=document.text_hash,
        extraction_warnings=_json_list(document.extraction_warnings),
        attachment_names=_json_list(document.attachment_names),
        ocr_status=document.ocr_status,
        sender=document.sender,
        recipients=document.recipients,
        cc=document.cc,
        bcc=document.bcc,
        chunks=[ChunkRead.model_validate(chunk) for chunk in chunks],
        entity_mentions=mentions,
        relationships=relationships,
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> Response:
    document = get_document_or_404(db, document_id)
    require_matter_access(db, actor, document.matter_id)
    stored_path = Path(document.stored_file_path)
    matter_id = document.matter_id
    filename = document.original_filename

    db.delete(document)
    db.commit()

    if stored_path.exists():
        stored_path.unlink()

    record_audit_event(
        db,
        action="document.delete",
        actor=actor.name,
        matter_id=matter_id,
        document_id=document_id,
        summary=f"Deleted {filename}",
    )
    return Response(status_code=204)


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]
