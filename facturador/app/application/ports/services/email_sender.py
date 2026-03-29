from __future__ import annotations

from typing import Protocol


class EmailSender(Protocol):
    async def send(self, payload: dict) -> dict: ...
