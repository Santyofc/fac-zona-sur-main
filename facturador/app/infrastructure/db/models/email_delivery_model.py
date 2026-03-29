import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class EmailDeliveryModel(Base):
    __tablename__ = 'email_deliveries'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'invoice_id', 'idempotency_key', name='uq_email_delivery_idempotency'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('invoices.id', ondelete='CASCADE'), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(120), index=True)
    recipient_email: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), index=True)
    provider_payload: Mapped[dict] = mapped_column(JSON)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
