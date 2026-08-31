import io

import pytest
from werkzeug.datastructures import FileStorage

from app.services.attachment_service import (
    AttachmentValidationError,
    _validate_file,
)


def make_file(
    content=b"test content",
    filename="test.txt",
    content_type="text/plain",
):
    return FileStorage(
        stream=io.BytesIO(content),
        filename=filename,
        content_type=content_type,
    )


def test_validate_valid_file():
    file = make_file()

    filename, file_size = _validate_file(file)

    assert filename == "test.txt"
    assert file_size == len(b"test content")


def test_validate_missing_file():
    with pytest.raises(AttachmentValidationError):
        _validate_file(None)


def test_validate_missing_filename():
    file = make_file(filename="")

    with pytest.raises(AttachmentValidationError):
        _validate_file(file)


def test_validate_invalid_extension():
    file = make_file(
        filename="malware.exe",
        content_type="application/octet-stream",
    )

    with pytest.raises(AttachmentValidationError):
        _validate_file(file)


def test_validate_invalid_content_type():
    file = make_file(
        filename="test.txt",
        content_type="application/pdf",
    )

    with pytest.raises(AttachmentValidationError):
        _validate_file(file)


def test_validate_empty_file():
    file = make_file(content=b"")

    with pytest.raises(AttachmentValidationError):
        _validate_file(file)
        
        
def test_validate_matching_content_type():
    file = make_file(
        filename="document.pdf",
        content_type="application/pdf",
    )

    filename, file_size = _validate_file(file)

    assert filename == "document.pdf"
    assert file_size == len(b"test content")
    

def test_validate_jpeg_content_type():
    file = make_file(
        filename="photo.jpg",
        content_type="image/jpeg",
    )

    filename, file_size = _validate_file(file)

    assert filename == "photo.jpg"
    assert file_size == len(b"test content")


def test_validate_file_over_10mb():
    file = make_file(
        content=b"x" * (10 * 1024 * 1024 + 1)
    )

    with pytest.raises(AttachmentValidationError):
        _validate_file(file)