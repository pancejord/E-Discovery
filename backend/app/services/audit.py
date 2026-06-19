from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record_audit_event(
    db: Session,
    *,
    action: str,
    actor: str | None = None,
    matter_id: int | None = None,
    document_id: int | None = None,
    entity_id: int | None = None,
    summary: str | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    event = AuditLog(
        actor=actor,
        action=action,
        matter_id=matter_id,
        document_id=document_id,
        entity_id=entity_id,
        summary=summary,
        details=details,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_audit_events(
    db: Session,
    *,
    matter_id: int | None = None,
    document_id: int | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    statement = select(AuditLog)
    if matter_id is not None:
        statement = statement.where(AuditLog.matter_id == matter_id)
    if document_id is not None:
        statement = statement.where(AuditLog.document_id == document_id)
    if action is not None:
        statement = statement.where(AuditLog.action == action)
    statement = statement.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(statement))
