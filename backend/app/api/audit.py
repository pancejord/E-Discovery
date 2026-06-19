from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import Actor, get_actor, require_matter_access
from app.database import get_db
from app.models.schemas import AuditLogRead
from app.services.audit import list_audit_events

router = APIRouter()


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
    matter_id: int | None = None,
    document_id: int | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLogRead]:
    require_matter_access(actor, matter_id)
    return list_audit_events(
        db,
        matter_id=matter_id,
        document_id=document_id,
        action=action,
        limit=limit,
        offset=offset,
    )
