from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class DocumentStateChanged:
    tenant_id: UUID
    invoice_id: UUID
    from_status: str
    to_status: str
    happened_at: datetime
    reason: str | None = None
