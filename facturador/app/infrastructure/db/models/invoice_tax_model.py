import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class InvoiceTaxModel(Base):
    __tablename__ = 'invoice_taxes'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), index=True)
    invoice_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('invoice_items.id', ondelete='CASCADE'), index=True)
    code: Mapped[str] = mapped_column(String(10))
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal('13.00'))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 5), default=Decimal('0'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
