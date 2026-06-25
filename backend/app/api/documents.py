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
    DocumentCodingUpdate,
    DocumentDetail,
    DocumentEntityMention,
    DocumentIngestionResult,
    DocumentSummary,
    RelationshipSummary,
)
from app.services.ingestion import get_document_or_404, ingest_upload, reprocess_document
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
) -> list[DocumentSummary]:
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
    return [_document_summary(document) for document in db.scalars(statement)]


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
    child_documents = list(
        db.scalars(
            select(Document)
            .where(Document.parent_document_id == document.id)
            .order_by(Document.created_at, Document.id)
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
                confidence_explanation=relationship.confidence_explanation,
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
        **_document_summary(document).model_dump(),
        stored_file_path=document.stored_file_path,
        extracted_text=document.extracted_text,
        text_hash=document.text_hash,
        extraction_warnings=_json_list(document.extraction_warnings),
        attachment_names=_json_list(document.attachment_names),
        ocr_status=document.ocr_status,
        notes=document.notes,
        sender=document.sender,
        recipients=document.recipients,
        cc=document.cc,
        bcc=document.bcc,
        child_documents=[_document_summary(child) for child in child_documents],
        chunks=[ChunkRead.model_validate(chunk) for chunk in chunks],
        entity_mentions=mentions,
        relationships=relationships,
    )


@router.patch("/{document_id}/coding", response_model=DocumentDetail)
def update_document_coding(
    document_id: int,
    request: DocumentCodingUpdate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> DocumentDetail:
    document = get_document_or_404(db, document_id)
    require_matter_access(db, actor, document.matter_id)
    updates = request.model_dump(exclude_unset=True)
    if "tags" in updates:
        document.tags = json.dumps(_clean_list(updates["tags"]))
    if "issue_codes" in updates:
        document.issue_codes = json.dumps(_clean_list(updates["issue_codes"]))
    if "notes" in updates:
        document.notes = updates["notes"]
    if "privilege_flag" in updates:
        document.privilege_flag = bool(updates["privilege_flag"])
    if "review_status" in updates and updates["review_status"]:
        document.review_status = updates["review_status"]
    db.commit()
    db.refresh(document)
    record_audit_event(
        db,
        action="document.coding_update",
        actor=actor.name,
        matter_id=document.matter_id,
        document_id=document.id,
        summary=f"Updated review coding for {document.original_filename}",
        details={"updated_fields": sorted(updates)},
    )
    return get_document(document_id=document_id, db=db, actor=actor)


@router.post("/{document_id}/reprocess", response_model=DocumentDetail)
def reprocess_document_endpoint(
    document_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> DocumentDetail:
    document = get_document_or_404(db, document_id)
    require_matter_access(db, actor, document.matter_id)
    try:
        reprocess_document(db, document)
    except Exception as error:
        record_audit_event(
            db,
            action="document.reprocess_failed",
            actor=actor.name,
            matter_id=document.matter_id,
            document_id=document.id,
            summary=f"Failed to reprocess {document.original_filename}",
            details={"error": str(error)},
        )
        raise
    record_audit_event(
        db,
        action="document.reprocess",
        actor=actor.name,
        matter_id=document.matter_id,
        document_id=document.id,
        summary=f"Reprocessed {document.original_filename}",
    )
    return get_document(document_id=document_id, db=db, actor=actor)


@router.post("/{document_id}/retry/{stage}", response_model=DocumentDetail)
def retry_document_stage(
    document_id: int,
    stage: str,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> DocumentDetail:
    if stage not in {"extraction", "ocr", "indexing", "entity_extraction", "all"}:
        raise HTTPException(status_code=400, detail="stage must be extraction, ocr, indexing, entity_extraction, or all")
    return reprocess_document_endpoint(document_id=document_id, db=db, actor=actor)


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


def _clean_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return sorted({str(value).strip() for value in values if str(value).strip()})


def _document_summary(document: Document) -> DocumentSummary:
    return DocumentSummary(
        id=document.id,
        matter_id=document.matter_id,
        custodian_id=document.custodian_id,
        parent_document_id=document.parent_document_id,
        attachment_filename=document.attachment_filename,
        original_filename=document.original_filename,
        file_type=document.file_type,
        document_type=document.document_type,
        subject=document.subject,
        document_date=document.document_date,
        processing_status=document.processing_status,
        tags=_json_list(document.tags),
        issue_codes=_json_list(document.issue_codes),
        privilege_flag=document.privilege_flag,
        review_status=document.review_status,
        processing_stages=_json_dict(document.processing_stages),
        processing_error=document.processing_error,
        risk_score=document.risk_score,
        created_at=document.created_at,
    )


def _json_dict(value: str | None) -> dict[str, str]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {str(key): str(item) for key, item in parsed.items()}
