from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class IssueCommand:
    tenant_id: UUID
    invoice_id: UUID
    requested_by: UUID
    idempotency_key: str


@dataclass(slots=True)
class CreateInvoiceCommand:
    tenant_id: UUID
    created_by: UUID
    doc_type: str
    customer_id: UUID | None
    currency: str
    issue_date: datetime
    items: list[dict]
    idempotency_key: str
