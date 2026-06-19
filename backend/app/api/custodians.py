from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import Actor, get_actor
from app.database import get_db
from app.models.custodian import Custodian
from app.models.schemas import CustodianCreate, CustodianRead, CustodianUpdate
from app.services.audit import record_audit_event

router = APIRouter()


@router.get("", response_model=list[CustodianRead])
def list_custodians(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Custodian]:
    statement = select(Custodian)
    if q:
        normalized = f"%{q.lower()}%"
        statement = statement.where(
            or_(
                Custodian.full_name.ilike(normalized),
                Custodian.email.ilike(normalized),
                Custodian.organization.ilike(normalized),
            )
        )
    statement = statement.order_by(Custodian.full_name).limit(limit).offset(offset)
    record_audit_event(db, action="custodian.list", actor=actor.name, summary="Listed custodians")
    return list(db.scalars(statement))


@router.post("", response_model=CustodianRead)
def create_custodian(
    request: CustodianCreate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> Custodian:
    custodian = Custodian(**request.model_dump())
    db.add(custodian)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="email already exists") from error
    db.refresh(custodian)
    record_audit_event(
        db,
        action="custodian.create",
        actor=actor.name,
        summary=f"Created custodian {custodian.full_name}",
    )
    return custodian


@router.get("/{custodian_id}", response_model=CustodianRead)
def get_custodian(custodian_id: int, db: Session = Depends(get_db)) -> Custodian:
    custodian = db.get(Custodian, custodian_id)
    if custodian is None:
        raise HTTPException(status_code=404, detail="Custodian not found")
    return custodian


@router.patch("/{custodian_id}", response_model=CustodianRead)
def update_custodian(
    custodian_id: int,
    request: CustodianUpdate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> Custodian:
    custodian = db.get(Custodian, custodian_id)
    if custodian is None:
        raise HTTPException(status_code=404, detail="Custodian not found")

    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(custodian, key, value)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="email already exists") from error
    db.refresh(custodian)
    record_audit_event(
        db,
        action="custodian.update",
        actor=actor.name,
        summary=f"Updated custodian {custodian.full_name}",
    )
    return custodian
