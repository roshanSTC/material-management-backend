import io

import pytest

from app.services.storage import (
    LocalStorage,
    StorageDeleteError,
    StorageNotFoundError,
    StorageSaveError,
)


@pytest.fixture
def storage(tmp_path):
    return LocalStorage(tmp_path)


def test_save_file(storage):
    file = io.BytesIO(b"hello material management")

    size = storage.save(
        file=file,
        storage_key="test.txt",
    )

    assert size == len(b"hello material management")
    assert storage.exists("test.txt")

    path = storage.get_path("test.txt")

    assert path.read_bytes() == b"hello material management"


def test_save_nested_file(storage):
    file = io.BytesIO(b"nested file")

    storage.save(
        file=file,
        storage_key="documents/2026/test.txt",
    )

    assert storage.exists(
        "documents/2026/test.txt"
    )

    path = storage.get_path(
        "documents/2026/test.txt"
    )

    assert path.read_bytes() == b"nested file"


def test_delete_file(storage):
    file = io.BytesIO(b"delete me")

    storage.save(
        file=file,
        storage_key="delete.txt",
    )

    assert storage.exists("delete.txt")

    storage.delete("delete.txt")

    assert not storage.exists("delete.txt")


def test_delete_nonexistent_file_is_safe(storage):
    storage.delete("does-not-exist.txt")

    assert not storage.exists(
        "does-not-exist.txt"
    )


def test_get_nonexistent_file_raises(storage):
    with pytest.raises(StorageNotFoundError):
        storage.get_path("missing.txt")


def test_path_traversal_is_rejected(storage):
    file = io.BytesIO(b"malicious")

    with pytest.raises(ValueError):
        storage.save(
            file=file,
            storage_key="../../malicious.txt",
        )


def test_absolute_path_is_rejected(storage):
    file = io.BytesIO(b"malicious")

    with pytest.raises(ValueError):
        storage.save(
            file=file,
            storage_key="/tmp/malicious.txt",
        )


def test_empty_storage_key_is_rejected(storage):
    file = io.BytesIO(b"test")

    with pytest.raises(ValueError):
        storage.save(
            file=file,
            storage_key="",
        )


def test_save_rejects_existing_file(storage):
    storage.save(
        file=io.BytesIO(b"first"),
        storage_key="same.txt",
    )

    with pytest.raises(StorageSaveError):
        storage.save(
            file=io.BytesIO(b"second"),
            storage_key="same.txt",
        )

    path = storage.get_path("same.txt")

    assert path.read_bytes() == b"first"


def test_file_cleanup_after_failed_write(storage, monkeypatch):
    file = io.BytesIO(b"test data")

    original_replace = storage.root_path.__class__.replace

    def failing_replace(self, target):
        raise OSError("simulated failure")

    monkeypatch.setattr(
        type(storage.root_path / "dummy"),
        "replace",
        failing_replace,
    )

    with pytest.raises(StorageSaveError):
        storage.save(
            file=file,
            storage_key="failed.txt",
        )

    assert not storage.exists("failed.txt")

    temporary_files = list(
        storage.root_path.glob(".*.tmp")
    )

    assert temporary_files == []