from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import Actor, get_actor, hash_api_key, require_admin
from app.database import get_db
from app.models.matter import Matter
from app.models.matter_membership import MatterMembership
from app.models.role import Role
from app.models.schemas import (
    AdminUserCreate,
    AdminUserCreateResponse,
    AdminUserRead,
    AdminUserUpdate,
    ApiKeyRotationRequest,
    ApiKeyRotationResponse,
    MatterMembershipCreate,
    MatterMembershipRead,
    MatterMembershipUpdate,
    RoleCreate,
    RoleRead,
)
from app.models.user import User
from app.services.audit import record_audit_event

router = APIRouter()


@router.get("/roles", response_model=list[RoleRead])
def list_roles(db: Session = Depends(get_db), actor: Actor = Depends(get_actor)) -> list[Role]:
    require_admin(actor)
    return list(db.scalars(select(Role).order_by(Role.name)))


@router.post("/roles", response_model=RoleRead)
def create_role(
    request: RoleCreate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> Role:
    require_admin(actor)
    role = Role(**request.model_dump())
    db.add(role)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="role name already exists") from error
    db.refresh(role)
    record_audit_event(
        db,
        action="role.create",
        actor=actor.name,
        summary=f"Created role {role.name}",
        details={"role_id": role.id, "is_admin": role.is_admin},
    )
    return role


@router.get("/users", response_model=list[AdminUserRead])
def list_users(db: Session = Depends(get_db), actor: Actor = Depends(get_actor)) -> list[AdminUserRead]:
    require_admin(actor)
    users = db.scalars(select(User).order_by(User.email)).all()
    return [_user_read(db, user) for user in users]


@router.post("/users", response_model=AdminUserCreateResponse)
def create_user(
    request: AdminUserCreate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> AdminUserCreateResponse:
    require_admin(actor)
    _ensure_role_exists(db, request.role_id)
    api_key = request.api_key or _new_api_key()
    user = User(
        email=request.email,
        display_name=request.display_name,
        api_key_hash=hash_api_key(api_key),
        role_id=request.role_id,
        organization=request.organization,
        tenant_id=request.tenant_id,
        is_active=request.is_active,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="user email or API key already exists") from error
    db.refresh(user)
    record_audit_event(
        db,
        action="user.create",
        actor=actor.name,
        summary=f"Created user {user.email}",
        details={"user_id": user.id, "role_id": user.role_id, "is_active": user.is_active},
    )
    return AdminUserCreateResponse(user=_user_read(db, user), api_key=api_key)


@router.patch("/users/{user_id}", response_model=AdminUserRead)
def update_user(
    user_id: int,
    request: AdminUserUpdate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> AdminUserRead:
    require_admin(actor)
    user = _get_user(db, user_id)
    updates = request.model_dump(exclude_unset=True)
    _ensure_role_exists(db, updates.get("role_id"))
    for key, value in updates.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    record_audit_event(
        db,
        action="user.update",
        actor=actor.name,
        summary=f"Updated user {user.email}",
        details={"user_id": user.id, "updated_fields": sorted(updates)},
    )
    return _user_read(db, user)


@router.post("/users/{user_id}/rotate-key", response_model=ApiKeyRotationResponse)
def rotate_user_key(
    user_id: int,
    request: ApiKeyRotationRequest,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> ApiKeyRotationResponse:
    require_admin(actor)
    user = _get_user(db, user_id)
    api_key = request.api_key or _new_api_key()
    user.api_key_hash = hash_api_key(api_key)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="API key already exists") from error
    db.refresh(user)
    record_audit_event(
        db,
        action="user.rotate_key",
        actor=actor.name,
        summary=f"Rotated API key for {user.email}",
        details={"user_id": user.id},
    )
    return ApiKeyRotationResponse(user=_user_read(db, user), api_key=api_key)


@router.get("/memberships", response_model=list[MatterMembershipRead])
def list_memberships(
    user_id: int | None = None,
    matter_id: int | None = None,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> list[MatterMembershipRead]:
    require_admin(actor)
    statement = select(MatterMembership).order_by(MatterMembership.created_at.desc())
    if user_id is not None:
        statement = statement.where(MatterMembership.user_id == user_id)
    if matter_id is not None:
        statement = statement.where(MatterMembership.matter_id == matter_id)
    return [_membership_read(db, membership) for membership in db.scalars(statement)]


@router.post("/memberships", response_model=MatterMembershipRead)
def create_membership(
    request: MatterMembershipCreate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> MatterMembershipRead:
    require_admin(actor)
    _get_user(db, request.user_id)
    _get_matter(db, request.matter_id)
    membership = MatterMembership(**request.model_dump())
    db.add(membership)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="membership already exists") from error
    db.refresh(membership)
    record_audit_event(
        db,
        action="membership.create",
        actor=actor.name,
        matter_id=membership.matter_id,
        summary="Created matter membership",
        details={"membership_id": membership.id, "user_id": membership.user_id, "role": membership.role},
    )
    return _membership_read(db, membership)


@router.patch("/memberships/{membership_id}", response_model=MatterMembershipRead)
def update_membership(
    membership_id: int,
    request: MatterMembershipUpdate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> MatterMembershipRead:
    require_admin(actor)
    membership = _get_membership(db, membership_id)
    membership.role = request.role
    db.commit()
    db.refresh(membership)
    record_audit_event(
        db,
        action="membership.update",
        actor=actor.name,
        matter_id=membership.matter_id,
        summary="Updated matter membership",
        details={"membership_id": membership.id, "user_id": membership.user_id, "role": membership.role},
    )
    return _membership_read(db, membership)


@router.delete("/memberships/{membership_id}", status_code=204)
def delete_membership(
    membership_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> Response:
    require_admin(actor)
    membership = _get_membership(db, membership_id)
    details = {"membership_id": membership.id, "user_id": membership.user_id, "role": membership.role}
    matter_id = membership.matter_id
    db.delete(membership)
    db.commit()
    record_audit_event(
        db,
        action="membership.delete",
        actor=actor.name,
        matter_id=matter_id,
        summary="Deleted matter membership",
        details=details,
    )
    return Response(status_code=204)


def _new_api_key() -> str:
    return f"ls_{token_urlsafe(32)}"


def _ensure_role_exists(db: Session, role_id: int | None) -> None:
    if role_id is not None and db.get(Role, role_id) is None:
        raise HTTPException(status_code=404, detail="Role not found")


def _get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _get_matter(db: Session, matter_id: int) -> Matter:
    matter = db.get(Matter, matter_id)
    if matter is None:
        raise HTTPException(status_code=404, detail="Matter not found")
    return matter


def _get_membership(db: Session, membership_id: int) -> MatterMembership:
    membership = db.get(MatterMembership, membership_id)
    if membership is None:
        raise HTTPException(status_code=404, detail="Membership not found")
    return membership


def _user_read(db: Session, user: User) -> AdminUserRead:
    role = db.get(Role, user.role_id) if user.role_id else None
    return AdminUserRead(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role_id=user.role_id,
        role_name=role.name if role else None,
        organization=user.organization,
        tenant_id=user.tenant_id,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _membership_read(db: Session, membership: MatterMembership) -> MatterMembershipRead:
    user = _get_user(db, membership.user_id)
    matter = _get_matter(db, membership.matter_id)
    return MatterMembershipRead(
        id=membership.id,
        user_id=membership.user_id,
        user_email=user.email,
        matter_id=membership.matter_id,
        matter_name=matter.name,
        role=membership.role,
        created_at=membership.created_at,
    )
