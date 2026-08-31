import os
from pathlib import Path
from typing import BinaryIO

from app.models import attachment
from app.services.storage.base import (
    Storage,
    StorageDeleteError,
    StorageNotFoundError,
    StorageSaveError,
    StorageError,
)



class LocalStorage(Storage):
    """
    Local filesystem implementation of the storage interface.
    """

    def __init__(self, root_path: str | Path):
        self.root_path = Path(root_path).resolve()

        self.root_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _resolve_path(self, storage_key: str) -> Path:
        """
        Resolve a storage key safely inside the storage root.

        Prevents path traversal attacks such as:
            ../../some-secret-file
        """

        if not storage_key:
            raise ValueError("storage_key is required.")

        relative_path = Path(storage_key)

        if relative_path.is_absolute():
            raise ValueError("Absolute storage keys are not allowed.")

        file_path = (self.root_path / relative_path).resolve()

        try:
            file_path.relative_to(self.root_path)
        except ValueError as exc:
            raise ValueError(
                "Invalid storage key."
            ) from exc

        return file_path

    def save(
        self,
        file: BinaryIO,
        storage_key: str,
    ) -> int:
        """
        Save a file atomically.

        Existing storage keys are rejected.

        Returns:
            Number of bytes written.
        """

        destination = self._resolve_path(storage_key)

        if destination.exists():
            raise StorageSaveError(
                f"Storage key already exists: {storage_key}"
            )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = destination.with_name(
            f".{destination.name}.tmp"
        )

        bytes_written = 0

        try:
            file.seek(0)

            with temporary_path.open("xb") as output:
                while True:
                    chunk = file.read(1024 * 1024)

                    if not chunk:
                        break

                    output.write(chunk)
                    bytes_written += len(chunk)

                output.flush()
                os.fsync(output.fileno())

            # Atomic move into the final location.
            #
            # Since we already verified that destination
            # does not exist, this should not overwrite
            # an existing storage object.
            if destination.exists():
                raise StorageSaveError(
                    f"Storage key already exists: {storage_key}"
                )

            temporary_path.replace(destination)

            return bytes_written

        except StorageSaveError:
            if temporary_path.exists():
                try:
                    temporary_path.unlink()
                except OSError:
                    pass

            raise

        except Exception as exc:
            if temporary_path.exists():
                try:
                    temporary_path.unlink()
                except OSError:
                    pass

            raise StorageSaveError(
                f"Failed to save file: {storage_key}"
            ) from exc
            
    def get(self, storage_key: str) -> BinaryIO:
        """Open a stored file for reading."""

        file_path = self._resolve_path(storage_key)

        if not file_path.exists():
            raise StorageNotFoundError(
                f"Storage object not found: {storage_key}"
            )

        if not file_path.is_file():
            raise StorageNotFoundError(
                f"Storage object is not a file: {storage_key}"
            )

        try:
            return file_path.open("rb")
        except OSError as exc:
            raise StorageError(
                f"Failed to read storage object: {storage_key}"
            ) from exc

    def delete(self, storage_key: str) -> None:
        """Delete a file from local storage."""

        file_path = self._resolve_path(storage_key)

        if not file_path.exists():
            return

        if not file_path.is_file():
            raise StorageDeleteError(
                f"Storage object is not a file: {storage_key}"
            )

        try:
            file_path.unlink()

        except OSError as exc:
            raise StorageDeleteError(
                f"Failed to delete file: {storage_key}"
            ) from exc

    def exists(self, storage_key: str) -> bool:
        """Check whether a file exists."""

        file_path = self._resolve_path(storage_key)

        return file_path.is_file()

    def get_path(self, storage_key: str) -> Path:
        """Return the physical path for a storage key."""

        file_path = self._resolve_path(storage_key)

        if not file_path.exists():
            raise StorageNotFoundError(
                f"File not found: {storage_key}"
            )

        if not file_path.is_file():
            raise StorageNotFoundError(
                f"Storage object is not a file: {storage_key}"
            )

        return file_path