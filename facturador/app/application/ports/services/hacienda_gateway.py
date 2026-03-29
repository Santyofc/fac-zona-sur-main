from __future__ import annotations

from typing import Protocol


class HaciendaGateway(Protocol):
    async def submit(self, payload: dict) -> dict: ...
    async def get_status(self, clave: str) -> dict: ...
