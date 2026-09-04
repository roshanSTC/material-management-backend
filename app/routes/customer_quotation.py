import json

from flask import current_app, jsonify, make_response, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.models import Attachment
from app.schemas.customer_quotation import (
    CustomerQuotationCreateSchema,
    CustomerQuotationQuerySchema,
    CustomerQuotationResponseSchema,
    CustomerQuotationUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    delete_attachment,
    list_attachments,
)
from app.services.customer_quotation_service import (
    CustomerNotFoundError,
    CustomerProjectMismatchError,
    CustomerQuotationNotFoundError,
    ProjectNotFoundError,
    create_customer_quotation_transaction,
    delete_customer_quotation_transaction,
    get_customer_quotation_record,
    list_customer_quotation_records,
    update_customer_quotation_transaction,
)
from app.services.storage.factory import get_storage

customer_quotation_bp = Blueprint(
    "customer_quotations",
    __name__,
    url_prefix="/api/v1/customer-quotations",
    description="Customer Quotation APIs",
)


def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _customer_quotation_response(customer_quotation):
    attachments = list_attachments(
        entity_type="customer_quotation",
        entity_id=customer_quotation.id,
    )
    quotation_number = (
        customer_quotation.quotation_number or customer_quotation.qo_number
    )
    return {
        "id": customer_quotation.id,
        "project_id": customer_quotation.project_id,
        "customer_id": customer_quotation.customer_id,
        "quotation_number": quotation_number,
        "qo_number": quotation_number,
        "quotation_date": customer_quotation.quotation_date,
        "quotation_value": customer_quotation.quotation_value,
        "currency_unit": customer_quotation.currency_unit,
        "currency_symbol": customer_quotation.currency_symbol,
        "total_net_amount": customer_quotation.total_net_amount,
        "validity": customer_quotation.validity,
        "remark": customer_quotation.remark,
        "created_at": customer_quotation.created_at,
        "updated_at": customer_quotation.updated_at,
        "items": [
            {
                "id": item.id,
                "customer_quotation_id": item.customer_quotation_id,
                "cost_sheet_item_id": item.cost_sheet_item_id,
                "quotation_number": item.quotation_number,
                "item_code": item.item_code,
                "material_name": item.material_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "net_amount": item.net_amount,
                "customs_duty_rate": (
                    float(item.customs_duty_rate)
                    if item.customs_duty_rate is not None
                    else None
                ),
                "created_at": item.created_at,
            }
            for item in customer_quotation.items
        ],
        "attachments": [
            {
                "id": attachment.id,
                "entity_type": attachment.entity_type,
                "entity_id": attachment.entity_id,
                "file_name": attachment.file_name,
                "storage_key": attachment.storage_key,
                "content_type": attachment.content_type,
                "file_size": attachment.file_size,
                "uploaded_by": attachment.uploaded_by,
                "created_at": attachment.created_at,
                "updated_at": attachment.updated_at,
            }
            for attachment in attachments
        ],
    }


def _extract_payload_and_files():
    if request.content_type and "multipart/form-data" in request.content_type:
        raw_data = request.form.get("data")
        if not raw_data:
            raise ValidationError({"data": ["data field is required in form-data."]})
        try:
            payload = json.loads(raw_data)
        except Exception as exc:
            raise ValidationError({"data": [f"Invalid JSON in data: {exc}"]})
        files = request.files.getlist("file")
        return payload, files
    elif request.is_json:
        return request.get_json() or {}, []
    return {}, []


@customer_quotation_bp.post("")
@customer_quotation_bp.doc(
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
                            "description": "Serialized JSON string matching CustomerQuotationCreateSchema",
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
            "application/json": {
                "schema": CustomerQuotationCreateSchema,
            },
        },
    },
)
@customer_quotation_bp.response(201, CustomerQuotationResponseSchema)
@jwt_required()
def create_customer_quotation():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = CustomerQuotationCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    try:
        customer_quotation = create_customer_quotation_transaction(data=validated_data)

        # Handle file attachments safely
        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            create_attachment(
                file=file,
                entity_type="customer_quotation",
                entity_id=customer_quotation.id,
                uploaded_by=user_id,
            )

        db.session.commit()
        return _customer_quotation_response(customer_quotation), 201

    except ProjectNotFoundError as exc:
        db.session.rollback()
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except CustomerNotFoundError as exc:
        db.session.rollback()
        return _error("CUSTOMER_NOT_FOUND", str(exc), 404)
    except CustomerProjectMismatchError as exc:
        db.session.rollback()
        return _error("CUSTOMER_PROJECT_MISMATCH", str(exc), 400)
    except AttachmentValidationError as exc:
        db.session.rollback()
        return _error("ATTACHMENT_VALIDATION_ERROR", str(exc), 400)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to create customer quotation")
        return _error("CUSTOMER_QUOTATION_CREATE_FAILED", "Failed to create customer quotation.", 500)


@customer_quotation_bp.get("")
@customer_quotation_bp.doc(security=[{"BearerAuth": []}])
@customer_quotation_bp.arguments(CustomerQuotationQuerySchema, location="query")
@customer_quotation_bp.response(200, CustomerQuotationResponseSchema(many=True))
@jwt_required()
def list_customer_quotations(args=None):
    if args is None:
        args = {}

    project_id = (
        args.get("project_id")
        or request.args.get("project_id")
        or request.args.get("projectId")
        or request.args.get("product_id")
    )
    if project_id is not None:
        try:
            project_id = int(project_id)
        except (ValueError, TypeError):
            project_id = None

    customer_id = (
        args.get("customer_id")
        or request.args.get("customer_id")
        or request.args.get("customerId")
    )
    if customer_id is not None:
        try:
            customer_id = int(customer_id)
        except (ValueError, TypeError):
            customer_id = None

    quotation_number = (
        args.get("quotation_number")
        or request.args.get("quotation_number")
        or request.args.get("quotationNumber")
        or request.args.get("qo_number")
    )

    try:
        quotations = list_customer_quotation_records(
            project_id=project_id,
            customer_id=customer_id,
            quotation_number=quotation_number,
        )
        return [_customer_quotation_response(cq) for cq in quotations], 200
    except Exception:
        current_app.logger.exception("Failed to list customer quotations")
        return _error("CUSTOMER_QUOTATION_LIST_FAILED", "Failed to list customer quotations.", 500)


@customer_quotation_bp.get("/<int:customer_quotation_id>")
@customer_quotation_bp.doc(security=[{"BearerAuth": []}])
@customer_quotation_bp.response(200, CustomerQuotationResponseSchema)
@jwt_required()
def get_customer_quotation(customer_quotation_id):
    try:
        quotation = get_customer_quotation_record(customer_quotation_id)
        return _customer_quotation_response(quotation), 200
    except CustomerQuotationNotFoundError as exc:
        return _error("CUSTOMER_QUOTATION_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get customer quotation")
        return _error("CUSTOMER_QUOTATION_GET_FAILED", "Failed to retrieve customer quotation.", 500)


@customer_quotation_bp.patch("/<int:customer_quotation_id>")
@customer_quotation_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody={
        "required": False,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": "Serialized JSON string matching CustomerQuotationUpdateSchema",
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
            "application/json": {
                "schema": CustomerQuotationUpdateSchema,
            },
        },
    },
)
@customer_quotation_bp.response(200, CustomerQuotationResponseSchema)
@jwt_required()
def update_customer_quotation(customer_quotation_id):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = CustomerQuotationUpdateSchema()
        validated_data = schema.load(raw_payload) if raw_payload else {}
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    try:
        customer_quotation = update_customer_quotation_transaction(
            customer_quotation_id=customer_quotation_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            create_attachment(
                file=file,
                entity_type="customer_quotation",
                entity_id=customer_quotation.id,
                uploaded_by=user_id,
            )

        db.session.commit()
        return _customer_quotation_response(customer_quotation), 200

    except CustomerQuotationNotFoundError as exc:
        db.session.rollback()
        return _error("CUSTOMER_QUOTATION_NOT_FOUND", str(exc), 404)
    except ProjectNotFoundError as exc:
        db.session.rollback()
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except CustomerNotFoundError as exc:
        db.session.rollback()
        return _error("CUSTOMER_NOT_FOUND", str(exc), 404)
    except CustomerProjectMismatchError as exc:
        db.session.rollback()
        return _error("CUSTOMER_PROJECT_MISMATCH", str(exc), 400)
    except AttachmentValidationError as exc:
        db.session.rollback()
        return _error("ATTACHMENT_VALIDATION_ERROR", str(exc), 400)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to update customer quotation")
        return _error("CUSTOMER_QUOTATION_UPDATE_FAILED", "Failed to update customer quotation.", 500)


@customer_quotation_bp.delete("/<int:customer_quotation_id>")
@customer_quotation_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_customer_quotation(customer_quotation_id):
    try:
        storage_keys = delete_customer_quotation_transaction(customer_quotation_id)
        db.session.commit()

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

        return jsonify({"success": True, "message": "Customer quotation deleted successfully."}), 200
    except CustomerQuotationNotFoundError as exc:
        db.session.rollback()
        return _error("CUSTOMER_QUOTATION_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete customer quotation")
        return _error("CUSTOMER_QUOTATION_DELETE_FAILED", "Failed to delete customer quotation.", 500)


