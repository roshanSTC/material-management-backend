import json

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.schemas.supplier_payment import (
    SupplierPaymentCreateSchema,
    SupplierPaymentQuerySchema,
    SupplierPaymentResponseSchema,
    SupplierPaymentUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    list_attachments,
)
from app.services.supplier_payment_service import (
    PaymentExceedsBalanceError,
    ProjectNotFoundError,
    SupplierNotFoundError,
    SupplierPaymentNotFoundError,
    TotalSupplierValueRequiredError,
    create_supplier_payment_transaction,
    delete_supplier_payment_transaction,
    get_supplier_payment_record,
    list_supplier_payment_records,
    update_supplier_payment_transaction,
)
from app.services.storage.factory import get_storage

supplier_payment_bp = Blueprint(
    "supplier_payments",
    __name__,
    url_prefix="/api/v1/supplier-payments",
    description="Supplier Payment APIs",
)


def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _format_decimal(val):
    if val is None:
        return None
    try:
        from decimal import Decimal
        return f"{Decimal(str(val)):.2f}"
    except Exception:
        return str(val)


def _supplier_payment_response(payment):
    attachments = list_attachments(
        entity_type="supplier_payment",
        entity_id=payment.id,
    )
    return {
        "id": payment.id,
        "project_id": payment.project_id,
        "supplier_id": payment.supplier_id,
        "currency": payment.currency,
        "payment_percentage": _format_decimal(payment.payment_percentage),
        "total_supplier_value": _format_decimal(payment.total_supplier_value),
        "amount_paid": _format_decimal(payment.amount_paid),
        "amount_paid_inr": _format_decimal(payment.amount_paid),
        "amount_paid_currency": _format_decimal(payment.amount_paid),
        "payment_date": payment.payment_date,
        "transaction_details": payment.transaction_details,
        "pending_amount": _format_decimal(payment.pending_amount),
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


def _handle_create_supplier_payment():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = SupplierPaymentCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        payment = create_supplier_payment_transaction(data=validated_data)

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="supplier_payment",
                entity_id=payment.id,
                uploaded_by=user_id,
            )
            if storage_key:
                storage_keys.append(storage_key)

        db.session.commit()
        return _supplier_payment_response(payment), 201
    except PaymentExceedsBalanceError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("PAYMENT_EXCEEDS_OUTSTANDING_BALANCE", str(exc), 400)
    except TotalSupplierValueRequiredError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("TOTAL_SUPPLIER_VALUE_REQUIRED", str(exc), 400)
    except ProjectNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except SupplierNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("SUPPLIER_NOT_FOUND", str(exc), 404)
    except AttachmentValidationError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("ATTACHMENT_VALIDATION_ERROR", str(exc), 400)
    except Exception:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        current_app.logger.exception("Failed to create supplier payment")
        return _error(
            "SUPPLIER_PAYMENT_CREATE_FAILED",
            "Failed to create supplier payment.",
            500,
        )


def _handle_list_supplier_payments(args=None):
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

    supplier_id = (
        args.get("supplier_id")
        or request.args.get("supplier_id")
        or request.args.get("supplierId")
    )
    if supplier_id is not None:
        try:
            supplier_id = int(supplier_id)
        except (ValueError, TypeError):
            supplier_id = None

    currency = (
        args.get("currency")
        or request.args.get("currency")
    )

    try:
        payments = list_supplier_payment_records(
            project_id=project_id,
            supplier_id=supplier_id,
            currency=currency,
        )
        return [_supplier_payment_response(p) for p in payments], 200
    except Exception:
        current_app.logger.exception("Failed to list supplier payments")
        return _error(
            "SUPPLIER_PAYMENT_LIST_FAILED",
            "Failed to list supplier payments.",
            500,
        )


def _handle_get_supplier_payment(payment_id: int):
    try:
        payment = get_supplier_payment_record(payment_id)
        return _supplier_payment_response(payment), 200
    except SupplierPaymentNotFoundError as exc:
        return _error("SUPPLIER_PAYMENT_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get supplier payment")
        return _error(
            "SUPPLIER_PAYMENT_GET_FAILED",
            "Failed to get supplier payment.",
            500,
        )


def _handle_update_supplier_payment(payment_id: int):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = SupplierPaymentUpdateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        payment = update_supplier_payment_transaction(
            payment_id=payment_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="supplier_payment",
                entity_id=payment.id,
                uploaded_by=user_id,
            )
            if storage_key:
                storage_keys.append(storage_key)

        db.session.commit()
        return _supplier_payment_response(payment), 200
    except PaymentExceedsBalanceError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("PAYMENT_EXCEEDS_OUTSTANDING_BALANCE", str(exc), 400)
    except TotalSupplierValueRequiredError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("TOTAL_SUPPLIER_VALUE_REQUIRED", str(exc), 400)
    except SupplierPaymentNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("SUPPLIER_PAYMENT_NOT_FOUND", str(exc), 404)
    except ProjectNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except SupplierNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("SUPPLIER_NOT_FOUND", str(exc), 404)
    except AttachmentValidationError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("ATTACHMENT_VALIDATION_ERROR", str(exc), 400)
    except Exception:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        current_app.logger.exception("Failed to update supplier payment")
        return _error(
            "SUPPLIER_PAYMENT_UPDATE_FAILED",
            "Failed to update supplier payment.",
            500,
        )


def _handle_delete_supplier_payment(payment_id: int):
    try:
        storage_keys = delete_supplier_payment_transaction(payment_id)
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
                    "message": "Supplier payment deleted successfully.",
                }
            ),
            200,
        )
    except SupplierPaymentNotFoundError as exc:
        db.session.rollback()
        return _error("SUPPLIER_PAYMENT_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete supplier payment")
        return _error(
            "SUPPLIER_PAYMENT_DELETE_FAILED",
            "Failed to delete supplier payment.",
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
                        "description": "Serialized JSON string matching SupplierPaymentCreateSchema",
                        "example": (
                            '{"project_id":2,"currency":"INR","payment_percentage":100,"total_supplier_value":3000,"amount_paid":3000,"payment_date":"2026-09-08","transaction_details":"sdggsggffdg","pending_amount":44,"remark":"Bank UTR & Settlement Remarks"}'
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
            "schema": SupplierPaymentCreateSchema,
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
                        "description": "Serialized JSON string matching SupplierPaymentUpdateSchema",
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                },
            },
        },
        "application/json": {
            "schema": SupplierPaymentUpdateSchema,
        },
    },
}


@supplier_payment_bp.post("")
@supplier_payment_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_CREATE_DOC,
)
@supplier_payment_bp.response(201, SupplierPaymentResponseSchema)
@jwt_required()
def create_supplier_payment():
    return _handle_create_supplier_payment()


@supplier_payment_bp.get("")
@supplier_payment_bp.doc(security=[{"BearerAuth": []}])
@supplier_payment_bp.arguments(SupplierPaymentQuerySchema, location="query")
@supplier_payment_bp.response(200, SupplierPaymentResponseSchema(many=True))
@jwt_required()
def list_supplier_payments(args=None):
    return _handle_list_supplier_payments(args)


@supplier_payment_bp.get("/<int:supplier_payment_id>")
@supplier_payment_bp.doc(security=[{"BearerAuth": []}])
@supplier_payment_bp.response(200, SupplierPaymentResponseSchema)
@jwt_required()
def get_supplier_payment(supplier_payment_id):
    return _handle_get_supplier_payment(supplier_payment_id)


@supplier_payment_bp.patch("/<int:supplier_payment_id>")
@supplier_payment_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_UPDATE_DOC,
)
@supplier_payment_bp.response(200, SupplierPaymentResponseSchema)
@jwt_required()
def update_supplier_payment(supplier_payment_id):
    return _handle_update_supplier_payment(supplier_payment_id)


@supplier_payment_bp.delete("/<int:supplier_payment_id>")
@supplier_payment_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_supplier_payment(supplier_payment_id):
    return _handle_delete_supplier_payment(supplier_payment_id)
