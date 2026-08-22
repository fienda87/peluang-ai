from functools import lru_cache

from app.infrastructure.storage import LocalFileStorage, StorageBackend
from app.shared.config import get_settings


@lru_cache
def get_storage() -> StorageBackend:
    settings = get_settings()
    if settings.storage_backend == "local":
        return LocalFileStorage(settings.storage_local_path)
    raise ValueError(f"Unknown storage backend: {settings.storage_backend}")
