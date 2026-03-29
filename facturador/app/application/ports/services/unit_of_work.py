from __future__ import annotations

from typing import Protocol


class UnitOfWork(Protocol):
    invoice_repository: object
    customer_repository: object
    product_repository: object
    certificate_repository: object
    sequence_repository: object
    event_repository: object
    submission_repository: object

    async def __aenter__(self): ...
    async def __aexit__(self, exc_type, exc, tb): ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
