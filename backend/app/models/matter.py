from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now


class Matter(Base):
    __tablename__ = "matters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    client_name: Mapped[str | None] = mapped_column(String(255), index=True)
    matter_number: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    documents = relationship("Document", back_populates="matter")
    memberships = relationship("MatterMembership", back_populates="matter", cascade="all, delete-orphan")
