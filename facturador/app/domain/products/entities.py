from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(slots=True)
class Product:
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    cabys_code: str
    unit_price: Decimal
    tax_rate: Decimal
