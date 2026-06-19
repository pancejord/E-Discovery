from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now


class EntityMention(Base):
    __tablename__ = "entity_mentions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    chunk_id: Mapped[int | None] = mapped_column(ForeignKey("document_chunks.id"), index=True)
    mention_text: Mapped[str] = mapped_column(String(500), nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    citation: Mapped[str] = mapped_column(String(1200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    entity = relationship("Entity", back_populates="mentions")
    document = relationship("Document", back_populates="entity_mentions")
    chunk = relationship("DocumentChunk")
