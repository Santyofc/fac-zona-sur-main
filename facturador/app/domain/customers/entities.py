from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Customer:
    id: UUID
    tenant_id: UUID
    name: str
    email: str | None
    id_type: str
    id_number: str
