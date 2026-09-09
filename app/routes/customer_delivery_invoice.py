import json

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.schemas.customer_delivery_invoice import (
    CustomerDeliveryInvoiceCreateSchema,
    CustomerDeliveryInvoiceQuerySchema,
    CustomerDeliveryInvoiceResponseSchema,
    CustomerDeliveryInvoiceUpdateSchema,
    LatestCustomerDeliveryInvoiceQuerySchema,
    LatestCustomerDeliveryInvoiceResponseSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    list_attachments,
)
from app.services.customer_delivery_invoice_service import (
    CustomerDeliveryInvoiceNotFoundError,
    ProjectNotFoundError,
    create_customer_delivery_invoice_transaction,
    delete_customer_delivery_invoice_transaction,
    get_customer_delivery_invoice_record,
    get_latest_customer_delivery_invoice_record,
    list_customer_delivery_invoice_records,
    update_customer_delivery_invoice_transaction,
)
from app.services.storage.factory import get_storage

customer_delivery_invoice_bp = Blueprint(
    "customer_delivery_invoices",
    __name__,
    url_prefix="/api/v1/customer-tax-invoices",
    description="Customer Tax / Delivery Invoice APIs",
)


def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _customer_delivery_invoice_response(invoice):
    attachments = list_attachments(
        entity_type="customer_delivery_invoice",
        entity_id=invoice.id,
    )
    return {
        "id": invoice.id,
        "project_id": invoice.project_id,
        "invoice_no": invoice.invoice_no,
        "invoice_number": invoice.invoice_no,
        "invoice_date": invoice.invoice_date,
        "gst_rate": invoice.gst_rate,
        "gst_amount": invoice.gst_amount,
        "round_off": invoice.round_off,
        "net_total": invoice.net_total,
        "remark": invoice.remark,
        "remarks": invoice.remark,
        "created_at": invoice.created_at,
        "updated_at": invoice.updated_at,
        "items": [
            {
                "id": item.id,
                "invoice_id": item.invoice_id,
                "material_name": item.material_name,
                "material_description": item.material_name,
                "hsn_code": item.hsn_code,
                "hsn_sac": item.hsn_code,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "rate_per_unit": item.unit_price,
                "net_amount": item.net_amount,
                "amount": item.net_amount,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            for item in invoice.items
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
            }
            for attachment in attachments
        ],
    }


def _format_decimal_str(val, places=2):
    if val is None:
        return None
    try:
        from decimal import Decimal

        d = Decimal(str(val).strip())
        return f"{d:.{places}f}"
    except Exception:
        return str(val)


def _latest_customer_delivery_invoice_response(invoice):
    tot = invoice.net_total
    if tot is None and invoice.items:
        try:
            from decimal import Decimal

            item_sum = sum(
                Decimal(str(item.net_amount or 0)) for item in invoice.items
            )
            gst = Decimal(str(invoice.gst_amount or 0))
            ro = Decimal(str(invoice.round_off or 0))
            tot = item_sum + gst + ro
        except Exception:
            pass

    return {
        "invoice_no": invoice.invoice_no,
        "invoice_date": invoice.invoice_date,
        "net_total": _format_decimal_str(tot, places=2),
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


def _handle_create_customer_delivery_invoice():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = CustomerDeliveryInvoiceCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        invoice = create_customer_delivery_invoice_transaction(data=validated_data)

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="customer_delivery_invoice",
                entity_id=invoice.id,
                uploaded_by=user_id,
            )
            if storage_key:
                storage_keys.append(storage_key)

        db.session.commit()
        return _customer_delivery_invoice_response(invoice), 201
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
        current_app.logger.exception("Failed to create customer delivery invoice")
        return _error(
            "CUSTOMER_DELIVERY_INVOICE_CREATE_FAILED",
            "Failed to create customer delivery invoice.",
            500,
        )


def _handle_list_customer_delivery_invoices(args=None):
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
        or request.args.get("invoice_number")
    )

    try:
        invoices = list_customer_delivery_invoice_records(
            project_id=project_id,
            invoice_no=invoice_no,
        )
        return [_customer_delivery_invoice_response(inv) for inv in invoices], 200
    except Exception:
        current_app.logger.exception("Failed to list customer delivery invoices")
        return _error(
            "CUSTOMER_DELIVERY_INVOICE_LIST_FAILED",
            "Failed to list customer delivery invoices.",
            500,
        )


def _handle_get_customer_delivery_invoice(invoice_id: int):
    try:
        invoice = get_customer_delivery_invoice_record(invoice_id)
        return _customer_delivery_invoice_response(invoice), 200
    except CustomerDeliveryInvoiceNotFoundError as exc:
        return _error("CUSTOMER_DELIVERY_INVOICE_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get customer delivery invoice")
        return _error(
            "CUSTOMER_DELIVERY_INVOICE_GET_FAILED",
            "Failed to get customer delivery invoice.",
            500,
        )


def _handle_update_customer_delivery_invoice(invoice_id: int):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = CustomerDeliveryInvoiceUpdateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        invoice = update_customer_delivery_invoice_transaction(
            invoice_id=invoice_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="customer_delivery_invoice",
                entity_id=invoice.id,
                uploaded_by=user_id,
            )
            if storage_key:
                storage_keys.append(storage_key)

        db.session.commit()
        return _customer_delivery_invoice_response(invoice), 200
    except CustomerDeliveryInvoiceNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("CUSTOMER_DELIVERY_INVOICE_NOT_FOUND", str(exc), 404)
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
        current_app.logger.exception("Failed to update customer delivery invoice")
        return _error(
            "CUSTOMER_DELIVERY_INVOICE_UPDATE_FAILED",
            "Failed to update customer delivery invoice.",
            500,
        )


def _handle_delete_customer_delivery_invoice(invoice_id: int):
    try:
        storage_keys = delete_customer_delivery_invoice_transaction(invoice_id)
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
                    "message": "Customer delivery invoice deleted successfully.",
                }
            ),
            200,
        )
    except CustomerDeliveryInvoiceNotFoundError as exc:
        db.session.rollback()
        return _error("CUSTOMER_DELIVERY_INVOICE_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete customer delivery invoice")
        return _error(
            "CUSTOMER_DELIVERY_INVOICE_DELETE_FAILED",
            "Failed to delete customer delivery invoice.",
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
                        "description": "Serialized JSON string matching CustomerDeliveryInvoiceCreateSchema",
                        "example": (
                            '{"project_id":2,"invoice_no":"NBHUD-32REF8RYU","invoice_date":"2026-09-15","gst_rate":18,"gst_amount":782.1,"round_off":-0.1,"net_total":5127,"remark":"Customer Tax Invoice","items":[{"material_name":"steel cold","hsn_code":"65465","quantity":55,"unit_price":34,"net_amount":1870},{"material_name":"gdfhbvf","hsn_code":"5464","quantity":55,"unit_price":45,"net_amount":2475}]}'
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
            "schema": CustomerDeliveryInvoiceCreateSchema,
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
                        "description": "Serialized JSON string matching CustomerDeliveryInvoiceUpdateSchema",
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                },
            },
        },
        "application/json": {
            "schema": CustomerDeliveryInvoiceUpdateSchema,
        },
    },
}


@customer_delivery_invoice_bp.post("")
@customer_delivery_invoice_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_CREATE_DOC,
)
@customer_delivery_invoice_bp.response(201, CustomerDeliveryInvoiceResponseSchema)
@jwt_required()
def create_customer_delivery_invoice():
    return _handle_create_customer_delivery_invoice()


@customer_delivery_invoice_bp.get("")
@customer_delivery_invoice_bp.doc(security=[{"BearerAuth": []}])
@customer_delivery_invoice_bp.arguments(
    CustomerDeliveryInvoiceQuerySchema, location="query"
)
@customer_delivery_invoice_bp.response(
    200, CustomerDeliveryInvoiceResponseSchema(many=True)
)
@jwt_required()
def list_customer_delivery_invoices(args=None):
    return _handle_list_customer_delivery_invoices(args)


@customer_delivery_invoice_bp.get("/latest")
@customer_delivery_invoice_bp.doc(
    security=[{"BearerAuth": []}],
    summary="Get Latest Customer Tax Invoice for Project",
    description="Retrieve the latest customer tax invoice for a project containing invoice_no, invoice_date, and net_total.",
)
@customer_delivery_invoice_bp.arguments(
    LatestCustomerDeliveryInvoiceQuerySchema, location="query"
)
@customer_delivery_invoice_bp.response(
    200, LatestCustomerDeliveryInvoiceResponseSchema
)
@jwt_required()
def get_latest_customer_delivery_invoice(args=None):
    if args is None:
        args = {}

    project_id = (
        args.get("project_id")
        or request.args.get("project_id")
        or request.args.get("projectId")
    )
    if not project_id:
        return _error("PROJECT_ID_REQUIRED", "project_id query parameter is required.", 400)

    try:
        project_id = int(project_id)
        if project_id <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return _error("INVALID_PROJECT_ID", "project_id must be a positive integer.", 400)

    try:
        invoice = get_latest_customer_delivery_invoice_record(project_id)
        return _latest_customer_delivery_invoice_response(invoice), 200
    except ProjectNotFoundError as exc:
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except CustomerDeliveryInvoiceNotFoundError as exc:
        return _error("CUSTOMER_DELIVERY_INVOICE_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get latest customer delivery invoice")
        return _error(
            "CUSTOMER_DELIVERY_INVOICE_GET_FAILED",
            "Failed to get latest customer delivery invoice.",
            500,
        )



@customer_delivery_invoice_bp.patch("/<int:customer_delivery_invoice_id>")
@customer_delivery_invoice_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_UPDATE_DOC,
)
@customer_delivery_invoice_bp.response(200, CustomerDeliveryInvoiceResponseSchema)
@jwt_required()
def update_customer_delivery_invoice(customer_delivery_invoice_id):
    return _handle_update_customer_delivery_invoice(customer_delivery_invoice_id)


@customer_delivery_invoice_bp.delete("/<int:customer_delivery_invoice_id>")
@customer_delivery_invoice_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_customer_delivery_invoice(customer_delivery_invoice_id):
    return _handle_delete_customer_delivery_invoice(customer_delivery_invoice_id)

