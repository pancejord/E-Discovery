from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now


class MatterMembership(Base):
    __tablename__ = "matter_memberships"
    __table_args__ = (UniqueConstraint("user_id", "matter_id", name="uq_matter_memberships_user_matter"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    matter_id: Mapped[int] = mapped_column(ForeignKey("matters.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(100), default="reviewer", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="memberships")
    matter = relationship("Matter", back_populates="memberships")
