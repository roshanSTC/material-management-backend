from flask import request, send_file
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
)
from flask_smorest import Blueprint

from app.schemas.attachment import (
    AttachmentResponseSchema,
)
from app.services.attachment_service import (
    AttachmentNotFoundError,
    AttachmentValidationError,
    create_attachment,
    delete_attachment,
    get_attachment,
    list_attachments,
)
from app.services.storage.factory import get_storage
from app.services.storage.base import StorageError


attachment_bp = Blueprint(
    "attachments",
    __name__,
    url_prefix="/api/v1/attachments",
    description="Attachment APIs",
)


def _attachment_response(attachment):
    return {
        "id": attachment.id,
        "customer_query_id": attachment.customer_query_id,
        "file_name": attachment.file_name,
        "storage_key": attachment.storage_key,
        "content_type": attachment.content_type,
        "file_size": attachment.file_size,
        "uploaded_by": attachment.uploaded_by,
        "created_at": attachment.created_at,
        "updated_at": attachment.updated_at,
    }


# @attachment_bp.post("")
# @attachment_bp.doc(
#     security=[{"BearerAuth": []}],
#     requestBody={
#         "required": True,
#         "content": {
#             "multipart/form-data": {
#                 "schema": {
#                     "type": "object",
#                     "required": [
#                         "customer_query_id",
#                         "file",
#                     ],
#                     "properties": {
#                         "customer_query_id": {
#                             "type": "integer",
#                             "example": 1,
#                         },
#                         "file": {
#                             "type": "string",
#                             "format": "binary",
#                         },
#                     },
#                 },
#             },
#         },
#     },
# )
# @attachment_bp.response(
#     201,
#     AttachmentResponseSchema,
# )
# @jwt_required()
# def upload_attachment():
#     """
#     Upload an attachment for a customer query.
#     """

#     customer_query_id = request.form.get(
#         "customer_query_id"
#     )

#     file = request.files.get("file")

#     if not customer_query_id:
#         return {
#             "success": False,
#             "error": {
#                 "code": "CUSTOMER_QUERY_ID_REQUIRED",
#                 "message": "customer_query_id is required.",
#             },
#         }, 422

#     if file is None:
#         return {
#             "success": False,
#             "error": {
#                 "code": "FILE_REQUIRED",
#                 "message": "File is required.",
#             },
#         }, 422

#     try:
#         customer_query_id = int(customer_query_id)
#     except (TypeError, ValueError):
#         return {
#             "success": False,
#             "error": {
#                 "code": "INVALID_CUSTOMER_QUERY_ID",
#                 "message": (
#                     "customer_query_id must be an integer."
#                 ),
#             },
#         }, 422

#     try:
#         attachment, _storage_key = create_attachment(
#             file=file,
#             customer_query_id=customer_query_id,
#             uploaded_by=int(get_jwt_identity()),
#         )

#         return _attachment_response(
#             attachment
#         ), 201

#     except AttachmentValidationError as exc:
#         return {
#             "success": False,
#             "error": {
#                 "code": "INVALID_ATTACHMENT",
#                 "message": str(exc),
#             },
#         }, 422

#     except StorageError:
#         return {
#             "success": False,
#             "error": {
#                 "code": "STORAGE_ERROR",
#                 "message": "Unable to store attachment.",
#             },
#         }, 500


# @attachment_bp.get(
#     "/customer-query/<int:customer_query_id>"
# )
# @attachment_bp.doc(
#     security=[{"BearerAuth": []}],
# )
# @attachment_bp.response(
#     200,
#     AttachmentResponseSchema(many=True),
# )
# @jwt_required()
# def get_customer_query_attachments(
#     customer_query_id,
# ):
#     """
#     List all attachments belonging to a customer query.
#     """

#     try:
#         attachments = list_attachments(
#             user_id=int(get_jwt_identity()),
#             customer_query_id=customer_query_id,
#         )

#         return [
#             _attachment_response(attachment)
#             for attachment in attachments
#         ], 200

#     except AttachmentValidationError as exc:
#         return {
#             "success": False,
#             "error": {
#                 "code": "INVALID_CUSTOMER_QUERY",
#                 "message": str(exc),
#             },
#         }, 422


@attachment_bp.get(
    "/<int:attachment_id>/download"
)
@attachment_bp.doc(
    security=[{"BearerAuth": []}],
)
@jwt_required()
def download_attachment(attachment_id):
    """
    Download an attachment.
    """

    try:
        attachment = get_attachment(
            attachment_id
        )

    except AttachmentNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "ATTACHMENT_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    storage = get_storage()

    try:
        file_stream = storage.get(
            attachment.storage_key
        )

    except StorageError:
        return {
            "success": False,
            "error": {
                "code": "FILE_NOT_FOUND",
                "message": (
                    "Attachment file is not "
                    "available."
                ),
            },
        }, 404

    return send_file(
        file_stream,
        mimetype=attachment.content_type,
        as_attachment=True,
        download_name=attachment.file_name,
    )


# @attachment_bp.delete(
#     "/<int:attachment_id>"
# )
# @attachment_bp.doc(
#     security=[{"BearerAuth": []}],
# )
# @jwt_required()
# def remove_attachment(attachment_id):
#     """
#     Delete an attachment.
#     """

#     try:
#         delete_attachment(
#             attachment_id
#         )

#     except AttachmentNotFoundError as exc:
#         return {
#             "success": False,
#             "error": {
#                 "code": "ATTACHMENT_NOT_FOUND",
#                 "message": str(exc),
#             },
#         }, 404

#     except StorageError:
#         return {
#             "success": False,
#             "error": {
#                 "code": "STORAGE_ERROR",
#                 "message": "Unable to delete attachment.",
#             },
#         }, 500

#     return "", 204