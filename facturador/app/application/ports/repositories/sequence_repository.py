from __future__ import annotations

from typing import Protocol
from uuid import UUID


class SequenceRepository(Protocol):
    async def next_sequence(self, tenant_id: UUID, branch: int, terminal: int, doc_type: str) -> int: ...
