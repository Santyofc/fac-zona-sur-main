from decimal import Decimal

from pydantic import BaseModel


class ProductIn(BaseModel):
    code: str
    name: str
    cabys_code: str
    unit_price: Decimal
    tax_rate: Decimal = Decimal('13')
