import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class InvoiceItemModel(Base):
    __tablename__ = 'invoice_items'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('invoices.id', ondelete='CASCADE'), index=True)
    line_number: Mapped[int] = mapped_column(SmallInteger)
    cabys_code: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 5))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 5))
    discount_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal('0'))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 5), default=Decimal('0'))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(12, 5), default=Decimal('0'))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 5), default=Decimal('0'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
