from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_matter_date", "matter_id", "document_date"),
        Index("ix_documents_matter_review", "matter_id", "review_status"),
        Index("ix_documents_matter_privilege", "matter_id", "privilege_flag"),
        Index("ix_documents_matter_type", "matter_id", "document_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    matter_id: Mapped[int | None] = mapped_column(ForeignKey("matters.id"), index=True)
    custodian_id: Mapped[int | None] = mapped_column(ForeignKey("custodians.id"), index=True)
    parent_document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), index=True)
    attachment_filename: Mapped[str | None] = mapped_column(String(500), index=True)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    document_type: Mapped[str | None] = mapped_column(String(100), index=True)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    text_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    extraction_warnings: Mapped[str | None] = mapped_column(Text)
    attachment_names: Mapped[str | None] = mapped_column(Text)
    ocr_status: Mapped[str | None] = mapped_column(String(100), index=True)
    sender: Mapped[str | None] = mapped_column(String(500), index=True)
    recipients: Mapped[str | None] = mapped_column(Text)
    cc: Mapped[str | None] = mapped_column(Text)
    bcc: Mapped[str | None] = mapped_column(Text)
    subject: Mapped[str | None] = mapped_column(String(1000), index=True)
    document_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    tags: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    issue_codes: Mapped[str | None] = mapped_column(Text)
    privilege_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    review_status: Mapped[str] = mapped_column(String(100), default="unreviewed", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    processing_status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False, index=True)
    processing_stages: Mapped[str | None] = mapped_column(Text)
    processing_error: Mapped[str | None] = mapped_column(Text)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    matter = relationship("Matter", back_populates="documents")
    custodian = relationship("Custodian", back_populates="documents")
    parent_document = relationship("Document", remote_side=[id], back_populates="child_documents")
    child_documents = relationship("Document", back_populates="parent_document")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    entity_mentions = relationship("EntityMention", back_populates="document", cascade="all, delete-orphan")
    relationships = relationship("Relationship", back_populates="document", cascade="all, delete-orphan")
