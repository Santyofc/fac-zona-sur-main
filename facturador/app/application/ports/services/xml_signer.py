from __future__ import annotations

from typing import Protocol


class XMLSigner(Protocol):
    async def sign(self, xml_content: str, cert_path: str, cert_password: str) -> str: ...
