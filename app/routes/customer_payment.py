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
from app.repositories.customer_payment_repository import list_customer_payments as repo_list_customer_payments
from app.services.customer_payment_service import (
    CustomerPaymentNotFoundError,
    InvoiceValueRequiredError,
    PaymentExceedsBalanceError,
    ProjectNotFoundError,
    create_customer_payment_transaction,
    delete_customer_payment_transaction,
    get_customer_payment_record,
    get_customer_payment_summary,
    list_customer_payment_records,
    update_customer_payment_transaction,
)
from app.services.storage.factory import get_storage
from app.utils.remark_utils import get_step_remarks_for_response

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


def _format_decimal(val):
    if val is None:
        return None
    try:
        from decimal import Decimal
        return f"{Decimal(str(val)):.2f}"
    except Exception:
        return str(val)


def _customer_payment_response(payment):
    from decimal import Decimal

    attachments = list_attachments(
        entity_type="customer_payment",
        entity_id=payment.id,
    )
    iv = Decimal(str(payment.invoice_value or 0)).quantize(Decimal("0.01"))
    amt = Decimal(str(payment.payment_amount or 0)).quantize(Decimal("0.01"))

    if hasattr(payment, "_cumulative_paid") and hasattr(payment, "_pending_amount"):
        cum_paid = Decimal(str(payment._cumulative_paid)).quantize(Decimal("0.01"))
        pend = Decimal(str(payment._pending_amount)).quantize(Decimal("0.01"))
    else:
        project_payments = repo_list_customer_payments(
            project_id=payment.project_id,
            latest_first=False,
        )
        running_paid = Decimal("0.00")
        for p in project_payments:
            p_amt = Decimal(str(p.payment_amount or 0)).quantize(Decimal("0.01"))
            running_paid += p_amt
            if p.id == payment.id:
                break
        cum_paid = running_paid if running_paid > Decimal("0.00") else amt
        if iv > Decimal("0.00"):
            pend = max((iv - cum_paid).quantize(Decimal("0.01")), Decimal("0.00"))
        else:
            pend = Decimal("0.00")

    if iv > Decimal("0.00"):
        pay_pct = ((amt / iv) * Decimal("100")).quantize(Decimal("0.01"))
        cum_pct = min(
            ((cum_paid / iv) * Decimal("100")).quantize(Decimal("0.01")),
            Decimal("100.00"),
        )
        pend_pct = max((Decimal("100.00") - cum_pct).quantize(Decimal("0.01")), Decimal("0.00"))
        is_completed = (pend <= Decimal("0.00")) or (cum_pct >= Decimal("100.00"))
    else:
        pay_pct = Decimal("100.00") if amt > Decimal("0.00") else Decimal("0.00")
        cum_pct = Decimal("100.00") if cum_paid > Decimal("0.00") else Decimal("0.00")
        pend_pct = Decimal("0.00") if cum_paid > Decimal("0.00") else Decimal("100.00")
        is_completed = cum_paid > Decimal("0.00")

    if is_completed:
        payment_status = "completed"
        status_message = "Payment completed"
    elif cum_paid > Decimal("0.00"):
        payment_status = "partial"
        status_message = f"{cum_pct:.2f}% paid, {pend_pct:.2f}% pending"
    else:
        payment_status = "pending"
        status_message = "0.00% paid, 100.00% pending"

    customer_id = payment.project.customer_id if getattr(payment, "project", None) else None

    return {
        "id": payment.id,
        "project_id": payment.project_id,
        "customer_id": customer_id,
        "invoice_no": payment.invoice_no,
        "invoice_number": payment.invoice_no,
        "invoice_date": payment.invoice_date,
        "payment_percentage": _format_decimal(pay_pct),
        "cumulative_payment_percentage": _format_decimal(cum_pct),
        "pending_percentage": _format_decimal(pend_pct),
        "invoice_value": _format_decimal(payment.invoice_value),
        "payment_amount": _format_decimal(payment.payment_amount),
        "amount_paid": _format_decimal(payment.payment_amount),
        "total_paid_amount": _format_decimal(cum_paid),
        "payment_date": payment.payment_date,
        "pending_amount": _format_decimal(pend),
        "tds": _format_decimal(payment.tds),
        "ld": _format_decimal(payment.ld),
        "liquidated_damages": _format_decimal(payment.ld),
        "is_payment_completed": is_completed,
        "payment_status": payment_status,
        "payment_status_message": status_message,
        "remark": payment.remark,
        "remarks": get_step_remarks_for_response(
            project_id=payment.project_id,
            step_number=14,
            fallback_raw=payment.remark,
            entity_id=payment.id,
        ),
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
        payment = create_customer_payment_transaction(
            data=validated_data,
            user_id=user_id,
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
        return _customer_payment_response(payment), 201
    except PaymentExceedsBalanceError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("PAYMENT_EXCEEDS_OUTSTANDING_BALANCE", str(exc), 400)
    except InvoiceValueRequiredError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("INVOICE_VALUE_REQUIRED", str(exc), 400)
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

    invoice_no = (
        args.get("invoice_no")
        or request.args.get("invoice_no")
        or request.args.get("invoiceNo")
    )
    if invoice_no:
        invoice_no = str(invoice_no).strip()

    try:
        payments = list_customer_payment_records(
            project_id=project_id,
            invoice_no=invoice_no,
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
            user_id=user_id,
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
    except PaymentExceedsBalanceError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("PAYMENT_EXCEEDS_OUTSTANDING_BALANCE", str(exc), 400)
    except InvoiceValueRequiredError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("INVOICE_VALUE_REQUIRED", str(exc), 400)
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
                            '{"project_id":2,"invoice_no":"INV-EWU5G-54TRE","invoice_date":"2026-09-10","payment_percentage":50,"invoice_value":5149,"payment_amount":2574.50,"payment_date":"2026-09-22","tds":34,"ld":34,"remark":"Bank UTR & Settlement Remarks"}'
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


@customer_payment_bp.get("/summary")
@customer_payment_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def get_customer_payment_summary_route():
    project_id = request.args.get("project_id") or request.args.get("projectId")
    if not project_id:
        return _error("PROJECT_ID_REQUIRED", "project_id query parameter is required.", 400)
    try:
        project_id = int(project_id)
        if project_id <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return _error("INVALID_PROJECT_ID", "project_id must be a positive integer.", 400)

    try:
        summary = get_customer_payment_summary(project_id)
        return jsonify(summary), 200
    except ProjectNotFoundError as exc:
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get customer payment summary")
        return _error(
            "CUSTOMER_PAYMENT_SUMMARY_FAILED",
            "Failed to get customer payment summary.",
            500,
        )


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

