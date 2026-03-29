from pathlib import Path

from app.core.config import settings


class LocalStorageService:
    def __init__(self):
        self.root = Path(settings.STORAGE_ROOT)
        self.root.mkdir(parents=True, exist_ok=True)

    async def put_text(self, key: str, content: str) -> str:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return str(path)

    async def put_bytes(self, key: str, content: bytes) -> str:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)

    async def get_text(self, key: str) -> str:
        return (self.root / key).read_text(encoding='utf-8')

    async def get_bytes(self, key: str) -> bytes:
        return (self.root / key).read_bytes()
