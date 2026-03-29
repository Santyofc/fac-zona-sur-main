from __future__ import annotations

from typing import Protocol
from uuid import UUID


class CustomerRepository(Protocol):
    async def create(self, payload: dict) -> dict: ...
    async def list_by_tenant(self, tenant_id: UUID) -> list[dict]: ...
