from __future__ import annotations

from typing import Protocol
from uuid import UUID


class SubmissionRepository(Protocol):
    async def create_submission(self, payload: dict) -> dict: ...
    async def get_latest(self, tenant_id: UUID, invoice_id: UUID) -> dict | None: ...
