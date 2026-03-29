import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class InvoiceModel(Base):
    __tablename__ = 'invoices'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'idempotency_key', name='uq_invoice_idempotency'),
        UniqueConstraint('tenant_id', 'consecutive', name='uq_invoice_tenant_consecutive'),
        UniqueConstraint('tenant_id', 'clave', name='uq_invoice_tenant_clave'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), index=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('customers.id', ondelete='SET NULL'), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    doc_type: Mapped[str] = mapped_column(String(5), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(120), index=True)
    consecutive: Mapped[str | None] = mapped_column(String(20), nullable=True)
    clave: Mapped[str | None] = mapped_column(String(50), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default='CRC')
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 5), default=Decimal('0'))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(12, 5), default=Decimal('0'))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 5), default=Decimal('0'))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
