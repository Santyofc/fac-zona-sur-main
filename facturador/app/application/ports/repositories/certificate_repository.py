from __future__ import annotations

from typing import Protocol
from uuid import UUID


class CertificateRepository(Protocol):
    async def create(self, payload: dict) -> dict: ...
    async def get_active(self, tenant_id: UUID) -> dict | None: ...
