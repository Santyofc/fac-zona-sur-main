from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(slots=True)
class InvoiceTax:
    id: UUID
    invoice_item_id: UUID
    code: str
    rate: Decimal
    amount: Decimal


@dataclass(slots=True)
class InvoiceItem:
    id: UUID
    invoice_id: UUID
    line_number: int
    cabys_code: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_pct: Decimal
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal


@dataclass(slots=True)
class InvoiceAggregate:
    tenant_id: UUID
    invoice_id: UUID
    doc_type: str
    status: str
    consecutive: str | None
    clave: str | None
    currency: str
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
