import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class HaciendaSubmissionModel(Base):
    __tablename__ = 'hacienda_submissions'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'invoice_id', 'idempotency_key', name='uq_submission_idempotency'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('invoices.id', ondelete='CASCADE'), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(120), index=True)
    xml_unsigned_url: Mapped[str] = mapped_column(String(500))
    xml_signed_url: Mapped[str] = mapped_column(String(500))
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    hacienda_payload: Mapped[dict] = mapped_column(JSON)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
