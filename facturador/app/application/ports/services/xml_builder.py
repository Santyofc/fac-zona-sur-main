from __future__ import annotations

from typing import Protocol


class XMLBuilder(Protocol):
    async def build(self, payload: dict) -> str: ...
