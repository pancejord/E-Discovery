from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    matter_id: Mapped[int | None] = mapped_column(ForeignKey("matters.id"), index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    alias_of_entity_id: Mapped[int | None] = mapped_column(ForeignKey("entities.id"), index=True)
    review_status: Mapped[str] = mapped_column(String(50), default="unreviewed", nullable=False, index=True)
    extraction_provider: Mapped[str | None] = mapped_column(String(100), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    alias_of = relationship("Entity", remote_side=[id], back_populates="aliases")
    aliases = relationship("Entity", back_populates="alias_of")
    mentions = relationship("EntityMention", back_populates="entity", cascade="all, delete-orphan")
    source_relationships = relationship(
        "Relationship",
        back_populates="source_entity",
        cascade="all, delete-orphan",
        foreign_keys="Relationship.source_entity_id",
    )
    target_relationships = relationship(
        "Relationship",
        back_populates="target_entity",
        cascade="all, delete-orphan",
        foreign_keys="Relationship.target_entity_id",
    )
