from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Certificate:
    id: UUID
    tenant_id: UUID
    alias: str
    p12_path: str
    is_active: bool
