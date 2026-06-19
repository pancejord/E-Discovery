from dataclasses import dataclass

from fastapi import Header, HTTPException

from app.core.config import settings


@dataclass(frozen=True)
class Actor:
    name: str
    authenticated: bool = False


def get_actor(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> Actor:
    if not settings.auth_enabled:
        return Actor(name="local-dev", authenticated=False)

    allowed_keys = {key.strip() for key in (settings.api_keys or "").split(",") if key.strip()}
    if not x_api_key or x_api_key not in allowed_keys:
        raise HTTPException(status_code=401, detail="Valid X-API-Key required")
    return Actor(name=f"api-key:{x_api_key[-6:]}", authenticated=True)


def require_matter_access(actor: Actor, matter_id: int | None) -> None:
    if matter_id is None:
        return
    if settings.auth_enabled and not actor.authenticated:
        raise HTTPException(status_code=403, detail="Matter access denied")
