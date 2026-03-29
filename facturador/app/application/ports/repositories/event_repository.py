from __future__ import annotations

from typing import Protocol
from uuid import UUID


class EventRepository(Protocol):
    async def append_event(self, tenant_id: UUID, invoice_id: UUID, from_status: str, to_status: str, reason: str | None = None) -> None: ...
