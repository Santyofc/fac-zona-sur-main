from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr


class InvoiceItemIn(BaseModel):
    description: str
    cabys_code: str = '0000000000000'
    quantity: Decimal = Field(default=Decimal('1'), gt=0)
    unit_price: Decimal = Field(gt=0)
    discount_pct: Decimal = Field(default=Decimal('0'), ge=0, le=100)
    tax_rate: Decimal = Field(default=Decimal('13'))


class InvoiceCreateIn(BaseModel):
    customer_id: UUID | None = None
    doc_type: str = 'FE'
    currency: str = 'CRC'
    issue_date: datetime = Field(default_factory=datetime.utcnow)
    notes: str | None = None
    idempotency_key: str
    created_by: UUID
    items: list[InvoiceItemIn]


class IssueInvoiceIn(BaseModel):
    requested_by: UUID
    idempotency_key: str


class EmailInvoiceIn(BaseModel):
    recipient_email: EmailStr
    idempotency_key: str


class InvoiceOut(BaseModel):
    id: UUID
    doc_type: str
    status: str
    consecutive: str | None = None
    clave: str | None = None
    total: Decimal
    currency: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data['id'],
            doc_type=data['doc_type'],
            status=data['status'],
            consecutive=data.get('consecutive'),
            clave=data.get('clave'),
            total=data.get('total', 0),
            currency=data.get('currency', 'CRC'),
        )
