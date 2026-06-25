from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.time import utc_now


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    matter_id: Mapped[int | None] = mapped_column(ForeignKey("matters.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    query: Mapped[str] = mapped_column(String(1000), nullable=False)
    filters: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_by: Mapped[str | None] = mapped_column(String(255), index=True)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
