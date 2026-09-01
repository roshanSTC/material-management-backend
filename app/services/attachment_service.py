
import os
import uuid

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.extensions.database import db
from app.models.attachment import Attachment
from app.services.storage import StorageError
from app.services.storage.factory import get_storage
from app.services.attachment_authorization_service import (
    authorize_project_access,
)


ALLOWED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "csv",
    "jpg",
    "jpeg",
    "png",
    "txt",
}


ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "image/jpeg",
    "image/png",
    "text/plain",
}


ALLOWED_MIME_TYPES_BY_EXTENSION = {
    "pdf": {
        "application/pdf",
    },
    "doc": {
        "application/msword",
    },
    "docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
    "xls": {
        "application/vnd.ms-excel",
    },
    "xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    },
    "csv": {
        "text/csv",
    },
    "jpg": {
        "image/jpeg",
    },
    "jpeg": {
        "image/jpeg",
    },
    "png": {
        "image/png",
    },
    "txt": {
        "text/plain",
    },
}


MAX_FILE_SIZE = 10 * 1024 * 1024


class AttachmentValidationError(Exception):
    pass


class AttachmentNotFoundError(Exception):
    pass


def _get_extension(filename: str) -> str:
    if "." not in filename:
        return ""

    return filename.rsplit(".", 1)[1].lower()


def _validate_file(file: FileStorage):
    if not file:
        raise AttachmentValidationError(
            "File is required."
        )

    if not file.filename:
        raise AttachmentValidationError(
            "File name is required."
        )

    filename = secure_filename(file.filename)

    if not filename:
        raise AttachmentValidationError(
            "Invalid file name."
        )

    extension = _get_extension(filename)

    if extension not in ALLOWED_EXTENSIONS:
        raise AttachmentValidationError(
            f"File type '.{extension}' is not allowed."
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise AttachmentValidationError(
            "The uploaded file content type is not allowed."
        )

    allowed_content_types = (
        ALLOWED_MIME_TYPES_BY_EXTENSION.get(
            extension,
            set(),
        )
    )

    if file.content_type not in allowed_content_types:
        raise AttachmentValidationError(
            "File extension does not match the content type."
        )

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size <= 0:
        raise AttachmentValidationError(
            "Uploaded file is empty."
        )

    if file_size > MAX_FILE_SIZE:
        raise AttachmentValidationError(
            "File size must not exceed 10 MB."
        )

    return filename, file_size


def create_attachment(
    *,
    file: FileStorage,
    customer_query_id: int,
    uploaded_by: int,
):
    filename, file_size = _validate_file(file)

    storage_key = (
        f"attachments/"
        f"customer-query/{customer_query_id}/"
        f"{uuid.uuid4().hex}_{filename}"
    )

    storage = get_storage()
    file_stored = False

    try:
        actual_size = storage.save(
            file=file,
            storage_key=storage_key,
        )

        file_stored = True

        if actual_size != file_size:
            raise AttachmentValidationError(
                "Uploaded file size changed during storage."
            )

        attachment = Attachment(
            customer_query_id=customer_query_id,
            file_name=filename,
            storage_key=storage_key,
            content_type=file.content_type,
            file_size=actual_size,
            uploaded_by=uploaded_by,
        )

        db.session.add(attachment)
        db.session.flush()

        return attachment, storage_key

    except Exception:
        if file_stored:
            try:
                if storage.exists(storage_key):
                    storage.delete(storage_key)
            except StorageError:
                current_app.logger.exception(
                    "Failed to clean up stored attachment: %s",
                    storage_key,
                )

        raise


def list_attachments(
    *,
    user_id: int,
    customer_query_id: int,
):
    """
    Return attachments belonging to a customer query.
    """

    if customer_query_id <= 0:
        raise AttachmentValidationError(
            "customer_query_id must be a positive integer."
        )

    attachments = (
        Attachment.query
        .filter(
            Attachment.customer_query_id
            == customer_query_id
        )
        .order_by(
            Attachment.created_at.desc()
        )
        .all()
    )

    return attachments


def get_attachment(
    attachment_id: int,
):
    attachment = db.session.get(
        Attachment,
        attachment_id,
    )

    if attachment is None:
        raise AttachmentNotFoundError(
            "Attachment not found."
        )

    return attachment


def delete_attachment(
    attachment_id: int,
):
    attachment = get_attachment(
        attachment_id
    )

    storage = get_storage()

    storage_key = attachment.storage_key

    db.session.delete(attachment)
    db.session.commit()

    try:
        if storage.exists(storage_key):
            storage.delete(storage_key)

    except StorageError:
        current_app.logger.exception(
            "Attachment DB record deleted but physical "
            "file cleanup failed: %s",
            storage_key,
        )

    return attachment
