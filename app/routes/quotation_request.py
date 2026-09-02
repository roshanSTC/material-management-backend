import json

from flask import current_app, request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
)
from app.extensions.database import db
from flask_smorest import Blueprint

from app.schemas.quotation_request import (
    QuotationRequestCreateSchema,
    QuotationRequestResponseSchema,
)

from app.services.attachment_service import AttachmentValidationError, create_attachment, delete_attachment, list_attachments
from app.services.quotation_request_service import (
    ProjectNotFoundError,
    SupplierNotFoundError,
    SupplierProjectMismatchError,
    QuotationRequestNotFoundError,
    create_quotation_request_transaction,
    delete_quotation_request_transaction,
    get_quotation_request_record,
    list_quotation_request_records,
    update_quotation_request_transaction,
)
from app.services.storage.factory import get_storage


quotation_request_bp = Blueprint(
    "quotation_requests",
    __name__,
    url_prefix="/api/v1/quotation-requests",
    description="Quotation Request APIs",
)


def _quotation_request_response(
    quotation_request,
):

    attachments = list_attachments(
        entity_type="quotation_request",
        entity_id=quotation_request.id,
    )

    return {
        "id": quotation_request.id,
        "project_id": quotation_request.project_id,
        "supplier_id": quotation_request.supplier_id,

        "quotation_requested_date": (
            quotation_request.quotation_requested_date
        ),

        "supplier_contacted": (
            quotation_request.supplier_contacted
        ),

        "remarks": quotation_request.remarks,

        "created_at": quotation_request.created_at,
        "updated_at": quotation_request.updated_at,

        "items": [
            {
                "id": item.id,
                "material_name": item.material_name,
                "quantity": item.quantity,
            }
            for item in quotation_request.items
        ],

        "attachments": [
            {
                "id": attachment.id,
                "file_name": attachment.file_name,
                "storage_key": attachment.storage_key,
                "content_type": attachment.content_type,
                "file_size": attachment.file_size,
                "uploaded_by": attachment.uploaded_by,
                "created_at": attachment.created_at,
            }
            for attachment in attachments
        ],
    }


@quotation_request_bp.post("")
@quotation_request_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody={
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "required": ["data"],
                    "properties": {
                        "data": {
                            "type": "string",
                            "example": (
                                '{"project_id":1,'
                                '"supplier_id":1,'
                                '"quotation_requested_date":"2026-09-01",'
                                '"supplier_contacted":true,'
                                '"remarks":"Please provide quotation",'
                                '"items":['
                                '{"material_name":"Steel",'
                                '"quantity":"10.000"}'
                                ']}'
                            ),
                        },
                        "file": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "format": "binary",
                            },
                        },
                    },
                },
            },
        },
    },
)
@jwt_required()
def create():

    files = request.files.getlist("file")

    data_raw = request.form.get("data")

    if not data_raw:
        return {
            "success": False,
            "error": {
                "code": "DATA_REQUIRED",
                "message": "data is required.",
            },
        }, 422

    try:
        data = json.loads(data_raw)

    except json.JSONDecodeError:
        return {
            "success": False,
            "error": {
                "code": "INVALID_DATA",
                "message": "data must contain valid JSON.",
            },
        }, 422

    try:
        validated_data = (
            QuotationRequestCreateSchema().load(data)
        )

    except Exception as exc:
        return {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(exc),
            },
        }, 422

    uploaded_storage_keys = []

    try:

        user_id = int(get_jwt_identity())

        quotation_request = (
            create_quotation_request_transaction(
                project_id=validated_data["project_id"],
                supplier_id=validated_data["supplier_id"],
                quotation_requested_date=validated_data[
                    "quotation_requested_date"
                ],
                supplier_contacted=validated_data[
                    "supplier_contacted"
                ],
                remarks=validated_data.get("remarks"),
                items=validated_data["items"],
            )
        )

        for file in files:

            attachment, storage_key = create_attachment(
                file=file,
                entity_type="quotation_request",
                entity_id=quotation_request.id,
                uploaded_by=user_id,
            )

            uploaded_storage_keys.append(storage_key)

        db.session.commit()

        return (
            _quotation_request_response(
                quotation_request
            ),
            201,
        )

    except ProjectNotFoundError as exc:

        db.session.rollback()

        return {
            "success": False,
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except SupplierNotFoundError as exc:

        db.session.rollback()

        return {
            "success": False,
            "error": {
                "code": "SUPPLIER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except SupplierProjectMismatchError as exc:

        db.session.rollback()

        return {
            "success": False,
            "error": {
                "code": "SUPPLIER_PROJECT_MISMATCH",
                "message": str(exc),
            },
        }, 409

    except AttachmentValidationError as exc:

        db.session.rollback()

        return {
            "success": False,
            "error": {
                "code": "INVALID_ATTACHMENT",
                "message": str(exc),
            },
        }, 422

    except Exception as exc:

        db.session.rollback()

        current_app.logger.exception(
            "Quotation request creation failed"
        )

        storage = get_storage()

        for storage_key in uploaded_storage_keys:

            try:

                if storage.exists(storage_key):
                    storage.delete(storage_key)

            except Exception:

                current_app.logger.exception(
                    "Failed to cleanup attachment: %s",
                    storage_key,
                )

        return {
            "success": False,
            "error": {
                "code": "QUOTATION_REQUEST_CREATE_FAILED",
                "message": str(exc),
            },
        }, 500


@quotation_request_bp.get("")
@quotation_request_bp.doc(
    security=[{"BearerAuth": []}]
)
@jwt_required()
def list_all():

    quotation_requests = (
        list_quotation_request_records()
    )

    return [
        _quotation_request_response(
            quotation_request
        )
        for quotation_request
        in quotation_requests
    ], 200
    
    
@quotation_request_bp.patch(
    "/<int:quotation_request_id>"
)
@quotation_request_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody={
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": (
                                "Partial JSON payload. "
                                "Only supplied fields are updated."
                            ),
                            "example": (
                                '{"remarks":"Updated quotation request",'
                                '"supplier_contacted":true,'
                                '"items":['
                                '{"material_name":"Steel",'
                                '"quantity":"20.000"}'
                                ']}'
                            ),
                        },
                        "file": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "format": "binary",
                            },
                        },
                    },
                },
            },
        },
    },
)
@jwt_required()
def update(quotation_request_id):

    files = request.files.getlist("file")

    data_raw = request.form.get("data")

    if not data_raw:
        return {
            "success": False,
            "error": {
                "code": "DATA_REQUIRED",
                "message": "data is required.",
            },
        }, 422

    try:
        data = json.loads(data_raw)

    except json.JSONDecodeError:

        return {
            "success": False,
            "error": {
                "code": "INVALID_DATA",
                "message": "data must contain valid JSON.",
            },
        }, 422

    if not isinstance(data, dict):

        return {
            "success": False,
            "error": {
                "code": "INVALID_DATA",
                "message": "data must contain a JSON object.",
            },
        }, 422

    try:
        user_id = int(get_jwt_identity())

        # Check that request exists before starting update
        quotation_request = (
            get_quotation_request_record(
                quotation_request_id
            )
        )

        uploaded_storage_keys = []

        try:

            quotation_request = (
                update_quotation_request_transaction(
                    quotation_request_id=quotation_request_id,
                    project_id=data.get("project_id"),
                    supplier_id=data.get("supplier_id"),
                    quotation_requested_date=data.get(
                        "quotation_requested_date"
                    ),
                    supplier_contacted=data.get(
                        "supplier_contacted"
                    ),
                    remarks=data.get("remarks"),
                    items=data.get("items"),
                )
            )

            # Add new attachments
            for file in files:

                attachment, storage_key = create_attachment(
                    file=file,
                    entity_type="quotation_request",
                    entity_id=quotation_request.id,
                    uploaded_by=user_id,
                )

                uploaded_storage_keys.append(storage_key)

            db.session.commit()

            return (
                _quotation_request_response(
                    quotation_request
                ),
                200,
            )

        except Exception:
            db.session.rollback()

            # Cleanup newly uploaded files
            storage = get_storage()

            for storage_key in uploaded_storage_keys:

                try:

                    if storage.exists(storage_key):
                        storage.delete(storage_key)

                except Exception:

                    current_app.logger.exception(
                        "Failed to cleanup attachment: %s",
                        storage_key,
                    )

            raise

    except QuotationRequestNotFoundError as exc:

        return {
            "success": False,
            "error": {
                "code": "QUOTATION_REQUEST_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except ProjectNotFoundError as exc:

        return {
            "success": False,
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except SupplierNotFoundError as exc:

        return {
            "success": False,
            "error": {
                "code": "SUPPLIER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except SupplierProjectMismatchError as exc:

        return {
            "success": False,
            "error": {
                "code": "SUPPLIER_PROJECT_MISMATCH",
                "message": str(exc),
            },
        }, 409

    except AttachmentValidationError as exc:

        return {
            "success": False,
            "error": {
                "code": "INVALID_ATTACHMENT",
                "message": str(exc),
            },
        }, 422

    except Exception as exc:

        current_app.logger.exception(
            "Quotation request update failed"
        )

        return {
            "success": False,
            "error": {
                "code": "QUOTATION_REQUEST_UPDATE_FAILED",
                "message": str(exc),
            },
        }, 500
        
        
@quotation_request_bp.delete("/<int:quotation_request_id>")
@quotation_request_bp.response(200)
@quotation_request_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete(quotation_request_id):
    try:
        quotation_request = get_quotation_request_record(
            quotation_request_id
        )

        if not quotation_request:
            raise QuotationRequestNotFoundError(
                f"Quotation request {quotation_request_id} not found."
            )

        # Get attachments before deleting DB records
        attachments = list_attachments(
            entity_type="quotation_request",
            entity_id=quotation_request_id,
        )

        storage_keys = [
            attachment.storage_key
            for attachment in attachments
        ]

        # Delete attachment DB records
        delete_attachment(
            entity_type="quotation_request",
            entity_id=quotation_request_id,
        )

        # Delete quotation request + child items
        delete_quotation_request_transaction(
            quotation_request_id
        )

        # Commit DB transaction
        db.session.commit()

        # Delete physical files AFTER successful DB commit
        storage = get_storage()

        for storage_key in storage_keys:
            try:
                if storage.exists(storage_key):
                    storage.delete(storage_key)
            except Exception:
                current_app.logger.exception(
                    "Failed to delete storage file: %s",
                    storage_key,
                )

        return {
            "success": True,
            "message": "Quotation request deleted successfully.",
        }, 200

    except QuotationRequestNotFoundError:
        db.session.rollback()

        return {
            "success": False,
            "error": {
                "code": "QUOTATION_REQUEST_NOT_FOUND",
                "message": "Quotation request not found.",
            },
        }, 404

    except Exception as exc:
        db.session.rollback()

        current_app.logger.exception(
            "Quotation request deletion failed: %s",
            exc,
        )

        return {
            "success": False,
            "error": {
                "code": "QUOTATION_REQUEST_DELETE_FAILED",
                "message": str(exc),
            },
        }, 500


# @quotation_request_bp.get(
#     "/<int:quotation_request_id>"
# )
# @quotation_request_bp.doc(
#     security=[{"BearerAuth": []}]
# )
# @jwt_required()
# def get(
#     quotation_request_id,
# ):

#     try:

#         quotation_request = (
#             get_quotation_request_record(
#                 quotation_request_id
#             )
#         )

#     except QuotationRequestNotFoundError as exc:

#         return {
#             "success": False,
#             "error": {
#                 "code": "QUOTATION_REQUEST_NOT_FOUND",
#                 "message": str(exc),
#             },
#         }, 404

#     return (
#         _quotation_request_response(
#             quotation_request
#         ),
#         200,
#     )