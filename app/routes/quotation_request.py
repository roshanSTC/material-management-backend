import json

from flask import request
from flask_jwt_extended import (
    jwt_required,
)
from flask_smorest import Blueprint

from app.schemas.quotation_request import (
    QuotationRequestCreateSchema,
    QuotationRequestResponseSchema,
)

from app.services.quotation_request_service import (
    ProjectNotFoundError,
    SupplierNotFoundError,
    SupplierProjectMismatchError,
    QuotationRequestNotFoundError,
    create_quotation_request_transaction,
    get_quotation_request_record,
    list_quotation_request_records,
)


quotation_request_bp = Blueprint(
    "quotation_requests",
    __name__,
    url_prefix="/api/v1/quotation-requests",
    description="Quotation Request APIs",
)


def _quotation_request_response(
    quotation_request,
):
    return {
        "id": quotation_request.id,
        "project_id": quotation_request.project_id,
        "supplier_id": quotation_request.supplier_id,
        "request_date": quotation_request.request_date,
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
                                '"request_date":"2026-09-01",'
                                '"remarks":"Please provide quotation",'
                                '"items":['
                                '{"material_name":"Steel",'
                                '"quantity":"10.000"}'
                                "]}"
                            ),
                        },
                    },
                },
            },
        },
    },
)
@jwt_required()
def create():

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
        data = json.loads(
            data_raw
        )

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
            QuotationRequestCreateSchema().load(
                data
            )
        )

    except Exception as exc:
        return {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(exc),
            },
        }, 422

    try:

        quotation_request = (
            create_quotation_request_transaction(
                project_id=validated_data[
                    "project_id"
                ],
                supplier_id=validated_data[
                    "supplier_id"
                ],
                request_date=validated_data[
                    "request_date"
                ],
                remarks=validated_data.get(
                    "remarks"
                ),
                items=validated_data[
                    "items"
                ],
            )
        )

        return (
            _quotation_request_response(
                quotation_request
            ),
            201,
        )

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

    except Exception:

        from app.extensions.database import db

        db.session.rollback()

        return {
            "success": False,
            "error": {
                "code": "QUOTATION_REQUEST_CREATE_FAILED",
                "message": (
                    "Unable to create quotation request."
                ),
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


@quotation_request_bp.get(
    "/<int:quotation_request_id>"
)
@quotation_request_bp.doc(
    security=[{"BearerAuth": []}]
)
@jwt_required()
def get(
    quotation_request_id,
):

    try:

        quotation_request = (
            get_quotation_request_record(
                quotation_request_id
            )
        )

    except QuotationRequestNotFoundError as exc:

        return {
            "success": False,
            "error": {
                "code": "QUOTATION_REQUEST_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    return (
        _quotation_request_response(
            quotation_request
        ),
        200,
    )