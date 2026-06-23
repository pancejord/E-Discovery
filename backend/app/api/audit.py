import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.auth import Actor, accessible_matter_ids, get_actor, require_matter_access
from app.core.config import settings
from app.database import get_db
from app.models.schemas import AuditLogRead
from app.services.audit import list_audit_events, purge_expired_audit_events

router = APIRouter()


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
    matter_id: int | None = None,
    document_id: int | None = None,
    event_actor: str | None = None,
    action: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLogRead]:
    require_matter_access(db, actor, matter_id)
    matter_ids = accessible_matter_ids(db, actor) if matter_id is None else None
    return list_audit_events(
        db,
        matter_id=matter_id,
        matter_ids=matter_ids,
        document_id=document_id,
        actor=event_actor,
        action=action,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
        offset=offset,
    )


@router.get("/export")
def export_audit_logs(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
    matter_id: int | None = None,
    document_id: int | None = None,
    event_actor: str | None = None,
    action: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    format: str = "csv",
    limit: int = 1000,
) -> Response:
    require_matter_access(db, actor, matter_id)
    matter_ids = accessible_matter_ids(db, actor) if matter_id is None else None
    events = list_audit_events(
        db,
        matter_id=matter_id,
        matter_ids=matter_ids,
        document_id=document_id,
        actor=event_actor,
        action=action,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
    )
    if format == "json":
        payload = [
            {
                "id": event.id,
                "actor": event.actor,
                "action": event.action,
                "matter_id": event.matter_id,
                "document_id": event.document_id,
                "entity_id": event.entity_id,
                "summary": event.summary,
                "details": event.details,
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ]
        return Response(
            content=json.dumps(payload),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=audit-events.json"},
        )
    if format != "csv":
        raise HTTPException(status_code=400, detail="format must be csv or json")

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "created_at", "actor", "action", "matter_id", "document_id", "entity_id", "summary", "details"])
    for event in events:
        writer.writerow(
            [
                event.id,
                event.created_at.isoformat(),
                event.actor or "",
                event.action,
                event.matter_id or "",
                event.document_id or "",
                event.entity_id or "",
                event.summary or "",
                json.dumps(event.details or {}),
            ]
        )
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit-events.csv"},
    )


@router.post("/retention/purge")
def purge_audit_retention(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> dict[str, int]:
    if not actor.is_admin:
        raise HTTPException(status_code=403, detail="Admin role required")
    deleted_count = purge_expired_audit_events(db)
    return {"retention_days": settings.audit_retention_days, "deleted_count": deleted_count}
