from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    @abstractmethod
    async def put(self, key: str, data: bytes) -> str: ...

    @abstractmethod
    async def get(self, key: str) -> bytes: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def exists(self, key: str) -> bool: ...

    @abstractmethod
    def url(self, key: str) -> str: ...


class LocalFileStorage(StorageBackend):
    def __init__(self, base_path: str) -> None:
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        path = (self.base / key).resolve()
        if not str(path).startswith(str(self.base.resolve())):
            raise ValueError(f"Invalid storage key: {key}")
        return path

    async def put(self, key: str, data: bytes) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return self.url(key)

    async def get(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()

    async def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()

    async def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    def url(self, key: str) -> str:
        return f"local://{key}"
