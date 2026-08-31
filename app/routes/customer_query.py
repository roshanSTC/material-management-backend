import json

from flask import current_app, request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
)
from flask_smorest import Blueprint
from app.extensions.database import db
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
)

from app.services.storage.factory import get_storage

from app.schemas.customer_query import (
    CustomerQueryCreateSchema,
    CustomerQueryResponseSchema,
)
from app.services.customer_query_service import (
    CustomerNotFoundError,
    CustomerProjectMismatchError,
    ProjectNotFoundError,
    CustomerQueryNotFoundError,
    create_customer_query_transaction,
    get_customer_query_record,
    list_customer_query_records,
)


customer_query_bp = Blueprint(
    "customer_queries",
    __name__,
    url_prefix="/api/v1/customer-queries",
    description="Customer Query / Requirement APIs",
)


def _customer_query_response(customer_query):
    return {
        "id": customer_query.id,
        "project_id": customer_query.project_id,
        "customer_id": customer_query.customer_id,
        "qo_date": customer_query.qo_date,
        "remark": customer_query.remark,
        "created_at": customer_query.created_at,
        "updated_at": customer_query.updated_at,

        "items": [
            {
                "id": item.id,
                "material_name": item.material_name,
                "quantity": item.quantity,
            }
            for item in customer_query.items
        ],

        "attachments": [
            {
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
            for attachment in customer_query.attachments
        ],
    }


@customer_query_bp.post("")
@customer_query_bp.doc(
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
                                '"customer_id":1,'
                                '"qo_date":"2026-08-31",'
                                '"remark":"Urgent requirement",'
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
@customer_query_bp.response(
    201,
    CustomerQueryResponseSchema,
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
        validated_data = CustomerQueryCreateSchema().load(data)

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

        customer_query = create_customer_query_transaction(
            project_id=validated_data["project_id"],
            customer_id=validated_data["customer_id"],
            qo_date=validated_data["qo_date"],
            remark=validated_data.get("remark"),
            items=validated_data["items"],
        )

        for file in files:

            attachment, storage_key = create_attachment(
                file=file,
                customer_query_id=customer_query.id,
                uploaded_by=user_id,
            )

            uploaded_storage_keys.append(storage_key)

        db.session.commit()

        return (
            _customer_query_response(customer_query),
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

    except CustomerNotFoundError as exc:
        db.session.rollback()

        return {
            "success": False,
            "error": {
                "code": "CUSTOMER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except CustomerProjectMismatchError as exc:
        db.session.rollback()

        return {
            "success": False,
            "error": {
                "code": "CUSTOMER_PROJECT_MISMATCH",
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

    except Exception:
        db.session.rollback()

        # Cleanup files already written to storage
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
                "code": "CUSTOMER_QUERY_CREATE_FAILED",
                "message": "Unable to create customer query.",
            },
        }, 500
        
        

@customer_query_bp.get("")
@customer_query_bp.doc(security=[{"BearerAuth": []}])
@customer_query_bp.response(200, CustomerQueryResponseSchema(many=True))
@jwt_required()
def list_all():
    customer_queries = list_customer_query_records()

    return [
        _customer_query_response(customer_query)
        for customer_query in customer_queries
    ], 200
    
    
    
@customer_query_bp.get("/<int:customer_query_id>")
@customer_query_bp.doc(security=[{"BearerAuth": []}])
@customer_query_bp.response(200, CustomerQueryResponseSchema)
@jwt_required()
def get(customer_query_id):
    try:
        customer_query = get_customer_query_record(
            customer_query_id
        )
    except CustomerQueryNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "CUSTOMER_QUERY_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    return _customer_query_response(customer_query), 200