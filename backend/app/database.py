from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def _connect_args(database_url: str) -> dict[str, bool]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    connect_args=_connect_args(settings.database_url),
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    from app.models import (  # noqa: F401
        audit_log,
        chunk,
        custodian,
        document,
        entity,
        entity_mention,
        evaluation,
        matter,
        matter_membership,
        relationship,
        role,
        saved_search,
        user,
    )

    if not settings.database_auto_create_tables or settings.app_environment.lower() in {"production", "prod"}:
        return
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
