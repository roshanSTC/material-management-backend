import io
from unittest.mock import patch
from pathlib import Path

import pytest
from werkzeug.datastructures import FileStorage

from app.extensions.database import db
from app.models.attachment import Attachment
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
)
from app.services.storage.base import StorageSaveError


def make_file(
    content=b"test attachment content",
    filename="document.txt",
    content_type="text/plain",
):
    return FileStorage(
        stream=io.BytesIO(content),
        filename=filename,
        content_type=content_type,
    )


def test_create_attachment_success(app, test_user, project):
    file = make_file()

    attachment = create_attachment(
        file=file,
        entity_type="project",
        entity_id=project.id,
        uploaded_by=test_user.id,
    )

    assert attachment.id is not None
    assert attachment.entity_type == "project"
    assert attachment.entity_id == project.id
    assert attachment.file_name == "document.txt"
    assert attachment.content_type == "text/plain"
    assert attachment.file_size == len(
        b"test attachment content"
    )
    assert attachment.uploaded_by == test_user.id

    stored_path = (
        Path(app.config["ATTACHMENT_STORAGE_PATH"])
        / attachment.storage_key
    )

    assert stored_path.exists()
    assert (
        stored_path.read_bytes()
        == b"test attachment content"
    )


def test_create_attachment_creates_db_record(
    app,
    test_user,
    project,
):
    file = make_file()

    attachment = create_attachment(
        file=file,
        entity_type="project",
        entity_id=project.id,
        uploaded_by=test_user.id,
    )

    saved_attachment = db.session.get(
        Attachment,
        attachment.id,
    )

    assert saved_attachment is not None
    assert saved_attachment.storage_key == (
        attachment.storage_key
    )


@patch(
    "app.services.attachment_service.get_storage"
)
def test_storage_failure_does_not_create_db_record(
    mock_get_storage,
    app,
    test_user,
    project,
):
    mock_storage = mock_get_storage.return_value

    mock_storage.save.side_effect = StorageSaveError(
        "Simulated storage failure"
    )

    file = make_file()

    with pytest.raises(StorageSaveError):
        create_attachment(
            file=file,
            entity_type="project",
            entity_id=project.id,
            uploaded_by=test_user.id,
        )

    attachments = Attachment.query.all()

    assert attachments == []

    mock_storage.save.assert_called_once()


@patch(
    "app.services.attachment_service.get_storage"
)
def test_db_failure_cleans_up_stored_file(
    mock_get_storage,
    app,
    test_user,
    project,
):
    mock_storage = mock_get_storage.return_value

    storage_key = "generated-key.txt"

    mock_storage.save.return_value = len(
        b"test attachment content"
    )

    mock_storage.exists.return_value = True

    file = make_file()

    with patch(
        "app.services.attachment_service.uuid.uuid4"
    ) as mock_uuid:
        mock_uuid.return_value.hex = (
            "generated-key"
        )

        with patch.object(
            db.session,
            "commit",
            side_effect=RuntimeError(
                "Simulated DB failure"
            ),
        ):
            with pytest.raises(RuntimeError):
                create_attachment(
                    file=file,
                    entity_type="project",
                    entity_id=project.id,
                    uploaded_by=test_user.id,
                )

    mock_storage.save.assert_called_once()
    mock_storage.exists.assert_called_once_with(
        storage_key
    )
    mock_storage.delete.assert_called_once_with(
        storage_key
    )

    attachments = Attachment.query.all()

    assert attachments == []


@patch(
    "app.services.attachment_service.get_storage"
)
def test_size_mismatch_cleans_up_file(
    mock_get_storage,
    app,
    test_user,
    project,
):
    mock_storage = mock_get_storage.return_value

    mock_storage.save.return_value = 999
    mock_storage.exists.return_value = True

    file = make_file()

    with pytest.raises(
        AttachmentValidationError,
        match="Uploaded file size changed",
    ):
        create_attachment(
            file=file,
            entity_type="project",
            entity_id=project.id,
            uploaded_by=test_user.id,
        )

    mock_storage.exists.assert_called_once()
    mock_storage.delete.assert_called_once()

    attachments = Attachment.query.all()

    assert attachments == []