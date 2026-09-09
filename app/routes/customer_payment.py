import json

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.schemas.customer_payment import (
    CustomerPaymentCreateSchema,
    CustomerPaymentQuerySchema,
    CustomerPaymentResponseSchema,
    CustomerPaymentUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    list_attachments,
)
from app.services.customer_payment_service import (
    CustomerPaymentNotFoundError,
    ProjectNotFoundError,
    create_customer_payment_transaction,
    delete_customer_payment_transaction,
    get_customer_payment_record,
    list_customer_payment_records,
    update_customer_payment_transaction,
)
from app.services.storage.factory import get_storage

customer_payment_bp = Blueprint(
    "customer_payments",
    __name__,
    url_prefix="/api/v1/customer-payments",
    description="Customer Payment APIs",
)


def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _customer_payment_response(payment):
    attachments = list_attachments(
        entity_type="customer_payment",
        entity_id=payment.id,
    )
    return {
        "id": payment.id,
        "project_id": payment.project_id,
        "invoice_no": payment.invoice_no,
        "invoice_number": payment.invoice_no,
        "invoice_date": payment.invoice_date,
        "invoice_value": payment.invoice_value,
        "payment_amount": payment.payment_amount,
        "payment_date": payment.payment_date,
        "tds": payment.tds,
        "ld": payment.ld,
        "liquidated_damages": payment.ld,
        "remark": payment.remark,
        "remarks": payment.remark,
        "created_at": payment.created_at,
        "updated_at": payment.updated_at,
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
            }
            for attachment in attachments
        ],
    }


def _extract_payload_and_files():
    content_type = request.content_type or ""
    files = []
    raw_payload = {}

    if "multipart/form-data" in content_type:
        data_raw = request.form.get("data")
        if data_raw:
            try:
                raw_payload = json.loads(data_raw)
            except (json.JSONDecodeError, TypeError) as exc:
                raise ValidationError(f"Invalid JSON in form data: {exc}")
        else:
            raw_payload = request.form.to_dict()

        if "file" in request.files:
            files = request.files.getlist("file")
        elif "files" in request.files:
            files = request.files.getlist("files")
        elif "attachments" in request.files:
            files = request.files.getlist("attachments")
    else:
        data_raw = request.form.get("data")
        if data_raw:
            try:
                raw_payload = json.loads(data_raw)
            except (json.JSONDecodeError, TypeError) as exc:
                raise ValidationError(f"Invalid JSON in form data: {exc}")
        else:
            raw_payload = request.get_json(silent=True) or request.form.to_dict() or {}

        if "file" in request.files:
            files = request.files.getlist("file")
        elif "files" in request.files:
            files = request.files.getlist("files")
        elif "attachments" in request.files:
            files = request.files.getlist("attachments")

    return raw_payload, files


def _cleanup_uploaded_files(storage_keys: list[str]) -> None:
    storage = get_storage()
    for storage_key in storage_keys:
        try:
            if storage.exists(storage_key):
                storage.delete(storage_key)
        except Exception:
            current_app.logger.exception(
                "Failed to cleanup attachment: %s", storage_key
            )


def _handle_create_customer_payment():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = CustomerPaymentCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        payment = create_customer_payment_transaction(data=validated_data)

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="customer_payment",
                entity_id=payment.id,
                uploaded_by=user_id,
            )
            if storage_key:
                storage_keys.append(storage_key)

        db.session.commit()
        return _customer_payment_response(payment), 201
    except ProjectNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except AttachmentValidationError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("ATTACHMENT_VALIDATION_ERROR", str(exc), 400)
    except Exception:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        current_app.logger.exception("Failed to create customer payment")
        return _error(
            "CUSTOMER_PAYMENT_CREATE_FAILED",
            "Failed to create customer payment.",
            500,
        )


def _handle_list_customer_payments(args=None):
    if args is None:
        args = {}

    project_id = (
        args.get("project_id")
        or request.args.get("project_id")
        or request.args.get("projectId")
    )
    if project_id is not None:
        try:
            project_id = int(project_id)
        except (ValueError, TypeError):
            project_id = None

    

    try:
        payments = list_customer_payment_records(
            project_id=project_id,
        )
        return [_customer_payment_response(p) for p in payments], 200
    except Exception:
        current_app.logger.exception("Failed to list customer payments")
        return _error(
            "CUSTOMER_PAYMENT_LIST_FAILED",
            "Failed to list customer payments.",
            500,
        )


def _handle_get_customer_payment(payment_id: int):
    try:
        payment = get_customer_payment_record(payment_id)
        return _customer_payment_response(payment), 200
    except CustomerPaymentNotFoundError as exc:
        return _error("CUSTOMER_PAYMENT_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get customer payment")
        return _error(
            "CUSTOMER_PAYMENT_GET_FAILED",
            "Failed to get customer payment.",
            500,
        )


def _handle_update_customer_payment(payment_id: int):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = CustomerPaymentUpdateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        payment = update_customer_payment_transaction(
            payment_id=payment_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="customer_payment",
                entity_id=payment.id,
                uploaded_by=user_id,
            )
            if storage_key:
                storage_keys.append(storage_key)

        db.session.commit()
        return _customer_payment_response(payment), 200
    except CustomerPaymentNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("CUSTOMER_PAYMENT_NOT_FOUND", str(exc), 404)
    except ProjectNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except AttachmentValidationError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("ATTACHMENT_VALIDATION_ERROR", str(exc), 400)
    except Exception:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        current_app.logger.exception("Failed to update customer payment")
        return _error(
            "CUSTOMER_PAYMENT_UPDATE_FAILED",
            "Failed to update customer payment.",
            500,
        )


def _handle_delete_customer_payment(payment_id: int):
    try:
        storage_keys = delete_customer_payment_transaction(payment_id)
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

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Customer payment deleted successfully.",
                }
            ),
            200,
        )
    except CustomerPaymentNotFoundError as exc:
        db.session.rollback()
        return _error("CUSTOMER_PAYMENT_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete customer payment")
        return _error(
            "CUSTOMER_PAYMENT_DELETE_FAILED",
            "Failed to delete customer payment.",
            500,
        )


_REQUEST_BODY_CREATE_DOC = {
    "required": True,
    "content": {
        "multipart/form-data": {
            "schema": {
                "type": "object",
                "required": ["data"],
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Serialized JSON string matching CustomerPaymentCreateSchema",
                        "example": (
                            '{"project_id":2,"invoice_no":"INV-EWU5G-54TRE","invoice_date":"2026-09-10","invoice_value":5149,"payment_amount":234.35,"payment_date":"2026-09-22","tds":34,"ld":34,"remark":"Bank UTR & Settlement Remarks"}'
                        ),
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                },
            },
        },
        "application/json": {
            "schema": CustomerPaymentCreateSchema,
        },
    },
}

_REQUEST_BODY_UPDATE_DOC = {
    "required": False,
    "content": {
        "multipart/form-data": {
            "schema": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Serialized JSON string matching CustomerPaymentUpdateSchema",
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                },
            },
        },
        "application/json": {
            "schema": CustomerPaymentUpdateSchema,
        },
    },
}


@customer_payment_bp.post("")
@customer_payment_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_CREATE_DOC,
)
@customer_payment_bp.response(201, CustomerPaymentResponseSchema)
@jwt_required()
def create_customer_payment():
    return _handle_create_customer_payment()


@customer_payment_bp.get("")
@customer_payment_bp.doc(security=[{"BearerAuth": []}])
@customer_payment_bp.arguments(CustomerPaymentQuerySchema, location="query")
@customer_payment_bp.response(200, CustomerPaymentResponseSchema(many=True))
@jwt_required()
def list_customer_payments(args=None):
    return _handle_list_customer_payments(args)



@customer_payment_bp.patch("/<int:customer_payment_id>")
@customer_payment_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_UPDATE_DOC,
)
@customer_payment_bp.response(200, CustomerPaymentResponseSchema)
@jwt_required()
def update_customer_payment(customer_payment_id):
    return _handle_update_customer_payment(customer_payment_id)


@customer_payment_bp.delete("/<int:customer_payment_id>")
@customer_payment_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_customer_payment(customer_payment_id):
    return _handle_delete_customer_payment(customer_payment_id)
