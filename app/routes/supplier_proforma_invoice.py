import json

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.schemas.supplier_proforma_invoice import (
    SupplierProformaInvoiceCreateSchema,
    SupplierProformaInvoiceQuerySchema,
    SupplierProformaInvoiceResponseSchema,
    SupplierProformaInvoiceUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    list_attachments,
)
from app.services.storage.factory import get_storage
from app.services.supplier_proforma_invoice_service import (
    ProjectNotFoundError,
    ProformaInvoiceAlreadyExistsError,
    ProformaInvoiceNotFoundError,
    SupplierNotFoundError,
    create_supplier_proforma_invoice_transaction,
    delete_supplier_proforma_invoice_transaction,
    get_supplier_proforma_invoice_record,
    list_supplier_proforma_invoice_records,
    update_supplier_proforma_invoice_transaction,
)

supplier_proforma_invoice_bp = Blueprint(
    "supplier_proforma_invoices",
    __name__,
    url_prefix="/api/v1/proforma-invoices",
    description="Supplier Proforma Invoice APIs",
)


def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _proforma_invoice_response(invoice):
    attachments = list_attachments(
        entity_type="supplier_proforma_invoice",
        entity_id=invoice.id,
    )
    if not attachments:
        attachments = list_attachments(
            entity_type="proforma_invoice",
            entity_id=invoice.id,
        )

    return {
        "id": invoice.id,
        "project_id": invoice.project_id,
        "supplier_id": invoice.supplier_id,
        "order_confirmation_id": invoice.order_confirmation_id,
        "proforma_invoice_no": invoice.proforma_invoice_no,
        "proforma_invoice_number": invoice.proforma_invoice_no,
        "proforma_invoice_date": invoice.proforma_invoice_date,
        "invoice_date": invoice.proforma_invoice_date,
        "delivery_terms": invoice.delivery_terms,
        "delivery_term": invoice.delivery_terms,
        "delivery_period": invoice.delivery_period,
        "delivery_date": invoice.delivery_date,
        "payment_terms": invoice.payment_terms,
        "payment_term": invoice.payment_terms,
        "warranty_period": invoice.warranty_period,
        "total_amount": invoice.total_amount,
        "total_net_amount": invoice.total_net_amount,
        "remark": invoice.remark,
        "remarks": invoice.remark,
        "created_at": invoice.created_at,
        "updated_at": invoice.updated_at,
        "items": [
            {
                "id": item.id,
                "proforma_invoice_id": item.proforma_invoice_id,
                "material_name": item.material_name or item.description,
                "description": item.description,
                "item_description": item.description,
                "hsn_code": item.hsn_code,
                "hsn": item.hsn_code,
                "hsn_sac": item.hsn_code,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "net_amount": item.net_amount,
                "created_at": item.created_at,
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
    else:
        raw_payload = request.get_json(silent=True) or {}

    return raw_payload, files


def _handle_create_supplier_proforma_invoice():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = SupplierProformaInvoiceCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    try:
        invoice = create_supplier_proforma_invoice_transaction(data=validated_data)

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            create_attachment(
                file=file,
                entity_type="supplier_proforma_invoice",
                entity_id=invoice.id,
                uploaded_by=user_id,
            )

        db.session.commit()
        return _proforma_invoice_response(invoice), 201

    except ProformaInvoiceAlreadyExistsError as exc:
        db.session.rollback()
        return _error("PROFORMA_INVOICE_ALREADY_EXISTS", str(exc), 409)
    except ProjectNotFoundError as exc:
        db.session.rollback()
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except SupplierNotFoundError as exc:
        db.session.rollback()
        return _error("SUPPLIER_NOT_FOUND", str(exc), 404)
    except AttachmentValidationError as exc:
        db.session.rollback()
        return _error("ATTACHMENT_VALIDATION_ERROR", str(exc), 400)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to create supplier proforma invoice")
        return _error(
            "PROFORMA_INVOICE_CREATE_FAILED",
            "Failed to create supplier proforma invoice.",
            500,
        )


def _handle_list_supplier_proforma_invoices(args=None):
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

    proforma_invoice_no = (
        args.get("proforma_invoice_no")
        or args.get("proforma_invoice_number")
        or request.args.get("proforma_invoice_no")
        or request.args.get("proforma_invoice_number")
    )

    try:
        invoices = list_supplier_proforma_invoice_records(
            project_id=project_id,
            supplier_id=supplier_id,
            proforma_invoice_no=proforma_invoice_no,
        )
        return [_proforma_invoice_response(inv) for inv in invoices], 200
    except Exception:
        current_app.logger.exception("Failed to list supplier proforma invoices")
        return _error(
            "PROFORMA_INVOICE_LIST_FAILED",
            "Failed to list supplier proforma invoices.",
            500,
        )


def _handle_update_supplier_proforma_invoice(proforma_invoice_id: int):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = SupplierProformaInvoiceUpdateSchema()
        validated_data = schema.load(raw_payload) if raw_payload else {}
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    try:
        invoice = update_supplier_proforma_invoice_transaction(
            invoice_id=proforma_invoice_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            create_attachment(
                file=file,
                entity_type="supplier_proforma_invoice",
                entity_id=invoice.id,
                uploaded_by=user_id,
            )

        db.session.commit()
        return _proforma_invoice_response(invoice), 200

    except ProformaInvoiceNotFoundError as exc:
        db.session.rollback()
        return _error("PROFORMA_INVOICE_NOT_FOUND", str(exc), 404)
    except ProformaInvoiceAlreadyExistsError as exc:
        db.session.rollback()
        return _error("PROFORMA_INVOICE_ALREADY_EXISTS", str(exc), 409)
    except ProjectNotFoundError as exc:
        db.session.rollback()
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except SupplierNotFoundError as exc:
        db.session.rollback()
        return _error("SUPPLIER_NOT_FOUND", str(exc), 404)
    except AttachmentValidationError as exc:
        db.session.rollback()
        return _error("ATTACHMENT_VALIDATION_ERROR", str(exc), 400)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to update supplier proforma invoice")
        return _error(
            "PROFORMA_INVOICE_UPDATE_FAILED",
            "Failed to update supplier proforma invoice.",
            500,
        )


def _handle_delete_supplier_proforma_invoice(proforma_invoice_id: int):
    try:
        storage_keys = delete_supplier_proforma_invoice_transaction(proforma_invoice_id)
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

        return jsonify({"success": True, "message": "Supplier proforma invoice deleted successfully."}), 200
    except ProformaInvoiceNotFoundError as exc:
        db.session.rollback()
        return _error("PROFORMA_INVOICE_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete supplier proforma invoice")
        return _error(
            "PROFORMA_INVOICE_DELETE_FAILED",
            "Failed to delete supplier proforma invoice.",
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
                        "description": "Serialized JSON string matching SupplierProformaInvoiceCreateSchema",
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                },
            },
        },
        "application/json": {
            "schema": SupplierProformaInvoiceCreateSchema,
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
                        "description": "Serialized JSON string matching SupplierProformaInvoiceUpdateSchema",
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                },
            },
        },
        "application/json": {
            "schema": SupplierProformaInvoiceUpdateSchema,
        },
    },
}


@supplier_proforma_invoice_bp.post("")
@supplier_proforma_invoice_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_CREATE_DOC,
)
@supplier_proforma_invoice_bp.response(201, SupplierProformaInvoiceResponseSchema)
@jwt_required()
def create_supplier_proforma_invoice():
    return _handle_create_supplier_proforma_invoice()


@supplier_proforma_invoice_bp.get("")
@supplier_proforma_invoice_bp.doc(security=[{"BearerAuth": []}])
@supplier_proforma_invoice_bp.arguments(SupplierProformaInvoiceQuerySchema, location="query")
@supplier_proforma_invoice_bp.response(200, SupplierProformaInvoiceResponseSchema(many=True))
@jwt_required()
def list_supplier_proforma_invoices(args=None):
    return _handle_list_supplier_proforma_invoices(args)


@supplier_proforma_invoice_bp.patch("/<int:proforma_invoice_id>")
@supplier_proforma_invoice_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_UPDATE_DOC,
)
@supplier_proforma_invoice_bp.response(200, SupplierProformaInvoiceResponseSchema)
@jwt_required()
def update_supplier_proforma_invoice(proforma_invoice_id):
    return _handle_update_supplier_proforma_invoice(proforma_invoice_id)


@supplier_proforma_invoice_bp.delete("/<int:proforma_invoice_id>")
@supplier_proforma_invoice_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_supplier_proforma_invoice(proforma_invoice_id):
    return _handle_delete_supplier_proforma_invoice(proforma_invoice_id)
