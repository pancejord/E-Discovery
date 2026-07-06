import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import Actor, accessible_matter_ids, get_actor, require_matter_access
from app.database import get_db
from app.models.matter import Matter
from app.models.schemas import MatterCreate, MatterRead, MatterUpdate
from app.services.audit import record_audit_event

router = APIRouter()


@router.get("", response_model=list[MatterRead])
def list_matters(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Matter]:
    statement = select(Matter)
    matter_ids = accessible_matter_ids(db, actor)
    if matter_ids is not None:
        statement = statement.where(Matter.id.in_(matter_ids))
    if q:
        normalized = f"%{q.lower()}%"
        statement = statement.where(Matter.name.ilike(normalized))
    statement = statement.order_by(Matter.created_at.desc()).limit(limit).offset(offset)
    record_audit_event(db, action="matter.list", actor=actor.name, summary="Listed matters")
    return list(db.scalars(statement))


@router.post("", response_model=MatterRead)
def create_matter(
    request: MatterCreate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> Matter:
    payload = request.model_dump()
    payload["ai_allowed_modes"] = json.dumps(payload.get("ai_allowed_modes") or [])
    matter = Matter(**payload)
    db.add(matter)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="matter_number already exists") from error
    db.refresh(matter)
    record_audit_event(
        db,
        action="matter.create",
        actor=actor.name,
        matter_id=matter.id,
        summary=f"Created matter {matter.name}",
    )
    return matter


@router.get("/{matter_id}", response_model=MatterRead)
def get_matter(
    matter_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> Matter:
    require_matter_access(db, actor, matter_id)
    matter = db.get(Matter, matter_id)
    if matter is None:
        raise HTTPException(status_code=404, detail="Matter not found")
    return matter


@router.patch("/{matter_id}", response_model=MatterRead)
def update_matter(
    matter_id: int,
    request: MatterUpdate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> Matter:
    require_matter_access(db, actor, matter_id)
    matter = db.get(Matter, matter_id)
    if matter is None:
        raise HTTPException(status_code=404, detail="Matter not found")

    payload = request.model_dump(exclude_unset=True)
    if "ai_allowed_modes" in payload:
        payload["ai_allowed_modes"] = json.dumps(payload["ai_allowed_modes"] or [])
    for key, value in payload.items():
        setattr(matter, key, value)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="matter_number already exists") from error
    db.refresh(matter)
    record_audit_event(
        db,
        action="matter.update",
        actor=actor.name,
        matter_id=matter.id,
        summary=f"Updated matter {matter.name}",
    )
    return matter
