from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), index=True)
    organization: Mapped[str | None] = mapped_column(String(255), index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(100), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    role = relationship("Role", back_populates="users")
    memberships = relationship("MatterMembership", back_populates="user", cascade="all, delete-orphan")
