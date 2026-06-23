from typing import Any

from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.utils.time import utc_now


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
    matter_ids: list[int] | None = None,
    document_id: int | None = None,
    actor: str | None = None,
    action: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    statement = select(AuditLog)
    if matter_id is not None:
        statement = statement.where(AuditLog.matter_id == matter_id)
    elif matter_ids is not None:
        statement = statement.where(AuditLog.matter_id.in_(matter_ids))
    if document_id is not None:
        statement = statement.where(AuditLog.document_id == document_id)
    if actor is not None:
        statement = statement.where(AuditLog.actor == actor)
    if action is not None:
        statement = statement.where(AuditLog.action == action)
    if created_from is not None:
        statement = statement.where(AuditLog.created_at >= created_from)
    if created_to is not None:
        statement = statement.where(AuditLog.created_at <= created_to)
    statement = statement.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(statement))


def purge_expired_audit_events(db: Session) -> int:
    if settings.audit_retention_days <= 0:
        return 0
    cutoff = utc_now() - timedelta(days=settings.audit_retention_days)
    result = db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff))
    db.commit()
    return int(result.rowcount or 0)
