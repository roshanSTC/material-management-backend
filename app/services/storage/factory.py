
from functools import lru_cache

from flask import current_app

from app.services.storage.base import StorageError
from app.services.storage.local import LocalStorage


@lru_cache(maxsize=4)
def _create_storage(storage_type: str, storage_path: str):
    """
    Create and cache a storage implementation.

    The cache prevents creating a new storage object for
    every request while still allowing different configured
    storage backends.
    """

    if storage_type == "local":
        return LocalStorage(
            root_path=storage_path,
        )

    raise StorageError(
        f"Unsupported storage backend: {storage_type}"
    )


def get_storage():
    """
    Return the configured storage backend.
    """

    storage_type = (
        current_app.config
        .get("STORAGE_BACKEND", "local")
        .strip()
        .lower()
    )

    storage_path = current_app.config.get(
        "ATTACHMENT_STORAGE_PATH",
        "storage/attachments",
    )

    if not storage_path:
        raise StorageError(
            "ATTACHMENT_STORAGE_PATH is not configured."
        )

    return _create_storage(
        storage_type,
        storage_path,
    )
