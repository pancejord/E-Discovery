import csv
import hashlib
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.auth import Actor, accessible_matter_ids, get_actor, require_matter_access
from app.core.config import settings
from app.database import get_db
from app.models.schemas import AuditLogRead
from app.services.audit import list_audit_events, purge_expired_audit_events, record_audit_event

router = APIRouter()


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
    matter_id: int | None = None,
    document_id: int | None = None,
    event_actor: str | None = None,
    action: str | None = None,
    request_id: str | None = None,
    method: str | None = None,
    route: str | None = None,
    response_status: int | None = None,
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
        request_id=request_id,
        method=method,
        route=route,
        response_status=response_status,
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
    request_id: str | None = None,
    method: str | None = None,
    route: str | None = None,
    response_status: int | None = None,
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
        request_id=request_id,
        method=method,
        route=route,
        response_status=response_status,
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
                "request_id": event.request_id,
                "client_ip": event.client_ip,
                "user_agent": event.user_agent,
                "route": event.route,
                "method": event.method,
                "response_status": event.response_status,
                "summary": event.summary,
                "details": event.details,
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ]
        content = json.dumps(payload)
        manifest = _audit_export_manifest(content, "json", len(events))
        record_audit_event(
            db,
            action="audit.export",
            actor=actor.name,
            matter_id=matter_id,
            document_id=document_id,
            summary="Exported audit events",
            details={"format": "json", "manifest": manifest},
        )
        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition": "attachment; filename=audit-events.json",
                "X-Audit-Export-Manifest": json.dumps(manifest),
            },
        )
    if format != "csv":
        raise HTTPException(status_code=400, detail="format must be csv or json")

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "created_at",
            "actor",
            "action",
            "request_id",
            "client_ip",
            "user_agent",
            "route",
            "method",
            "response_status",
            "matter_id",
            "document_id",
            "entity_id",
            "summary",
            "details",
        ]
    )
    for event in events:
        writer.writerow(
            [
                event.id,
                event.created_at.isoformat(),
                event.actor or "",
                event.action,
                event.request_id or "",
                event.client_ip or "",
                event.user_agent or "",
                event.route or "",
                event.method or "",
                event.response_status or "",
                event.matter_id or "",
                event.document_id or "",
                event.entity_id or "",
                event.summary or "",
                json.dumps(event.details or {}),
            ]
        )
    content = buffer.getvalue()
    manifest = _audit_export_manifest(content, "csv", len(events))
    record_audit_event(
        db,
        action="audit.export",
        actor=actor.name,
        matter_id=matter_id,
        document_id=document_id,
        summary="Exported audit events",
        details={"format": "csv", "manifest": manifest},
    )
    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=audit-events.csv",
            "X-Audit-Export-Manifest": json.dumps(manifest),
        },
    )


@router.post("/retention/purge")
def purge_audit_retention(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> dict[str, int]:
    if not actor.is_admin:
        raise HTTPException(status_code=403, detail="Admin role required")
    deleted_count = purge_expired_audit_events(db)
    record_audit_event(
        db,
        action="audit.retention.purge_manual",
        actor=actor.name,
        summary="Manually purged expired audit events",
        details={"retention_days": settings.audit_retention_days, "deleted_count": deleted_count},
    )
    return {"retention_days": settings.audit_retention_days, "deleted_count": deleted_count}


def _audit_export_manifest(content: str, export_format: str, event_count: int) -> dict[str, str | int]:
    encoded = content.encode("utf-8")
    return {
        "format": export_format,
        "event_count": event_count,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "byte_count": len(encoded),
    }
