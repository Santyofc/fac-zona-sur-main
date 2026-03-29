from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = 'CRC'

    def quantized(self) -> 'Money':
        return Money(self.amount.quantize(Decimal('0.00001'), rounding=ROUND_HALF_UP), self.currency)
