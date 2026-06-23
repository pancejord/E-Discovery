from dataclasses import dataclass
from hashlib import sha256

from fastapi import Depends, Header, HTTPException
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models.matter_membership import MatterMembership
from app.models.role import Role
from app.models.user import User
from app.services.audit import record_audit_event


@dataclass(frozen=True)
class Actor:
    name: str
    authenticated: bool = False
    user_id: int | None = None
    role_name: str | None = None
    is_admin: bool = False


def get_actor(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Actor:
    if not settings.auth_enabled:
        return Actor(name="local-dev", authenticated=False, is_admin=True)

    if not x_api_key:
        raise HTTPException(status_code=401, detail="Valid X-API-Key required")

    user = db.scalar(select(User).where(User.api_key_hash == hash_api_key(x_api_key), User.is_active.is_(True)))
    if user is None:
        record_audit_event(
            db,
            action="auth.denied",
            actor="unknown",
            summary="Rejected API key authentication",
            details={"reason": "invalid_api_key"},
        )
        raise HTTPException(status_code=401, detail="Valid X-API-Key required")

    role = db.get(Role, user.role_id) if user.role_id else None
    return Actor(
        name=user.email,
        authenticated=True,
        user_id=user.id,
        role_name=role.name if role else None,
        is_admin=bool(role and role.is_admin),
    )


def hash_api_key(api_key: str) -> str:
    return sha256(api_key.encode("utf-8")).hexdigest()


def require_matter_access(db: Session, actor: Actor, matter_id: int | None) -> None:
    if matter_id is None:
        return
    if _has_matter_access(db, actor, matter_id):
        return
    _record_permission_denial(db, actor, matter_id, "matter_access_denied")
    raise HTTPException(status_code=403, detail="Matter access denied")


def require_scoped_write_matter(db: Session, actor: Actor, matter_id: int | None) -> None:
    if not settings.auth_enabled:
        return
    if matter_id is None:
        _record_permission_denial(db, actor, None, "matter_id_required")
        raise HTTPException(status_code=400, detail="matter_id required when auth is enabled")
    require_matter_access(db, actor, matter_id)


def accessible_matter_ids(db: Session, actor: Actor) -> list[int] | None:
    if not settings.auth_enabled or actor.is_admin:
        return None
    if not actor.authenticated or actor.user_id is None:
        return []
    return list(
        db.scalars(
            select(MatterMembership.matter_id)
            .where(MatterMembership.user_id == actor.user_id)
            .order_by(MatterMembership.matter_id)
        )
    )


def _has_matter_access(db: Session, actor: Actor, matter_id: int) -> bool:
    if not settings.auth_enabled or actor.is_admin:
        return True
    if not actor.authenticated or actor.user_id is None:
        return False
    return bool(
        db.scalar(
            select(
                exists().where(
                    MatterMembership.user_id == actor.user_id,
                    MatterMembership.matter_id == matter_id,
                )
            )
        )
    )


def _record_permission_denial(db: Session, actor: Actor, matter_id: int | None, reason: str) -> None:
    record_audit_event(
        db,
        action="permission.denied",
        actor=actor.name,
        matter_id=matter_id,
        summary="Denied matter access",
        details={"reason": reason},
    )
