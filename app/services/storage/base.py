from abc import ABC, abstractmethod
from typing import BinaryIO

from werkzeug.datastructures import FileStorage


class StorageError(Exception):
    """Base exception for storage errors."""


class StorageNotFoundError(StorageError):
    """Raised when a storage object does not exist."""


class StorageExistsError(StorageError):
    """Raised when a storage object already exists."""


class StorageDeleteError(StorageError):
    """Raised when a storage object cannot be deleted."""


class StorageSaveError(StorageError):
    """Raised when a storage object cannot be saved."""


class Storage(ABC):

    @abstractmethod
    def save(
        self,
        *,
        file: FileStorage,
        storage_key: str,
    ) -> int:
        """Save a file and return its size in bytes."""
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        storage_key: str,
    ) -> BinaryIO:
        """Open a stored file for reading."""
        raise NotImplementedError

    @abstractmethod
    def exists(
        self,
        storage_key: str,
    ) -> bool:
        """Check whether a storage object exists."""
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        storage_key: str,
    ) -> None:
        """Delete a storage object."""
        raise NotImplementedError