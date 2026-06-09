from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    matter_id: Mapped[int | None] = mapped_column(ForeignKey("matters.id"), index=True)
    custodian_id: Mapped[int | None] = mapped_column(ForeignKey("custodians.id"), index=True)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    document_type: Mapped[str | None] = mapped_column(String(100), index=True)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    text_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    sender: Mapped[str | None] = mapped_column(String(500), index=True)
    recipients: Mapped[str | None] = mapped_column(Text)
    cc: Mapped[str | None] = mapped_column(Text)
    bcc: Mapped[str | None] = mapped_column(Text)
    subject: Mapped[str | None] = mapped_column(String(1000), index=True)
    document_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    processing_status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False, index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    matter = relationship("Matter", back_populates="documents")
    custodian = relationship("Custodian", back_populates="documents")
