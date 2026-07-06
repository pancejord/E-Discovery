from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.time import utc_now


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_matter_created", "matter_id", "created_at"),
        Index("ix_audit_logs_action_created", "action", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    actor: Mapped[str | None] = mapped_column(String(255), index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    matter_id: Mapped[int | None] = mapped_column(index=True)
    document_id: Mapped[int | None] = mapped_column(index=True)
    entity_id: Mapped[int | None] = mapped_column(index=True)
    request_id: Mapped[str | None] = mapped_column(String(100), index=True)
    client_ip: Mapped[str | None] = mapped_column(String(100), index=True)
    user_agent: Mapped[str | None] = mapped_column(String(1000))
    route: Mapped[str | None] = mapped_column(String(500), index=True)
    method: Mapped[str | None] = mapped_column(String(20), index=True)
    response_status: Mapped[int | None] = mapped_column(index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
