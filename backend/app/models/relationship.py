from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now


class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    matter_id: Mapped[int | None] = mapped_column(ForeignKey("matters.id"), index=True)
    source_entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False, index=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    evidence: Mapped[str | None] = mapped_column(String(1200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    source_entity = relationship("Entity", back_populates="source_relationships", foreign_keys=[source_entity_id])
    target_entity = relationship("Entity", back_populates="target_relationships", foreign_keys=[target_entity_id])
    document = relationship("Document", back_populates="relationships")
