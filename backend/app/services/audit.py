from datetime import datetime, timedelta
from typing import Any
from contextvars import ContextVar

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.role import Role
from app.models.user import User
from app.utils.time import utc_now

_audit_context: ContextVar[dict[str, Any]] = ContextVar("audit_context", default={})


def set_audit_context(**context: Any):
    return _audit_context.set({key: value for key, value in context.items() if value is not None})


def update_audit_context(**context: Any) -> None:
    current = dict(_audit_context.get())
    current.update({key: value for key, value in context.items() if value is not None})
    _audit_context.set(current)


def reset_audit_context(token) -> None:
    _audit_context.reset(token)


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
    context = _audit_context.get()
    enriched_details = dict(details or {})
    actor_context = {
        output_key: context[context_key]
        for context_key, output_key in {
            "actor_user_id": "user_id",
            "actor_role": "role",
            "actor_tenant_id": "tenant_id",
            "actor_organization": "organization",
            "auth_scheme": "auth_scheme",
        }.items()
        if context.get(context_key) is not None
    }
    if actor:
        actor_context = {**_actor_context_from_db(db, actor, context.get("auth_scheme")), **actor_context}
    if actor_context:
        enriched_details.setdefault("actor_context", actor_context)
    event = AuditLog(
        actor=actor,
        action=action,
        matter_id=matter_id,
        document_id=document_id,
        entity_id=entity_id,
        request_id=context.get("request_id"),
        client_ip=context.get("client_ip"),
        user_agent=context.get("user_agent"),
        route=context.get("route"),
        method=context.get("method"),
        response_status=context.get("response_status"),
        summary=summary,
        details=enriched_details or None,
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
    request_id: str | None = None,
    method: str | None = None,
    route: str | None = None,
    response_status: int | None = None,
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
    if request_id is not None:
        statement = statement.where(AuditLog.request_id == request_id)
    if method is not None:
        statement = statement.where(AuditLog.method == method)
    if route is not None:
        statement = statement.where(AuditLog.route == route)
    if response_status is not None:
        statement = statement.where(AuditLog.response_status == response_status)
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


def _actor_context_from_db(db: Session, actor: str, auth_scheme: str | None) -> dict[str, Any]:
    user = db.scalar(select(User).where(User.email == actor))
    if user is None:
        return {"auth_scheme": auth_scheme} if auth_scheme else {}
    role = db.get(Role, user.role_id) if user.role_id else None
    context = {
        "user_id": user.id,
        "role": role.name if role else None,
        "tenant_id": user.tenant_id,
        "organization": user.organization,
        "auth_scheme": auth_scheme,
    }
    return {key: value for key, value in context.items() if value is not None}
