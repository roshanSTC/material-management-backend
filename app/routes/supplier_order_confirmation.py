import json

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.schemas.supplier_order_confirmation import (
    LatestSupplierOrderConfirmationResponseSchema,
    SupplierOrderConfirmationCreateSchema,
    SupplierOrderConfirmationQuerySchema,
    SupplierOrderConfirmationResponseSchema,
    SupplierOrderConfirmationUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    list_attachments,
)
from app.services.storage.factory import get_storage
from app.services.supplier_order_confirmation_service import (
    OrderConfirmationAlreadyExistsError,
    OrderConfirmationNotFoundError,
    ProjectNotFoundError,
    SupplierNotFoundError,
    create_supplier_order_confirmation_transaction,
    delete_supplier_order_confirmation_transaction,
    get_latest_supplier_order_confirmation_record,
    get_supplier_order_confirmation_record,
    list_supplier_order_confirmation_records,
    update_supplier_order_confirmation_transaction,
)

order_confirmation_bp = Blueprint(
    "order_confirmations",
    __name__,
    url_prefix="/api/v1/order-confirmations",
    description="Supplier Order Confirmation APIs",
)



def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _order_confirmation_response(confirmation):
    attachments = list_attachments(
        entity_type="order_confirmation",
        entity_id=confirmation.id,
    )
    if not attachments:
        attachments = list_attachments(
            entity_type="supplier_order_confirmation",
            entity_id=confirmation.id,
        )

    return {
        "id": confirmation.id,
        "project_id": confirmation.project_id,
        "supplier_id": confirmation.supplier_id,
        "purchase_order_id": confirmation.purchase_order_id,
        "order_confirmation_date": confirmation.order_confirmation_date,
        "confirmation_date": confirmation.order_confirmation_date,
        "email": confirmation.email,
        "ref_no": confirmation.ref_no,
        "reference_number": confirmation.ref_no,
        "shipping_terms": confirmation.shipping_terms,
        "shipping_term": confirmation.shipping_terms,
        "warranty_period": confirmation.warranty_period,
        "delivery_period": confirmation.delivery_period,
        "delivery_term": confirmation.delivery_period,
        "payment_terms": confirmation.payment_terms,
        "payment_term": confirmation.payment_terms,
        "total_amount": confirmation.total_amount,
        "total_net_amount": confirmation.total_net_amount,
        "remark": confirmation.remark,
        "remarks": confirmation.remark,
        "created_at": confirmation.created_at,
        "updated_at": confirmation.updated_at,
        "items": [
            {
                "id": item.id,
                "order_confirmation_id": item.supplier_order_confirmation_id,
                "supplier_order_confirmation_id": item.supplier_order_confirmation_id,
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
            for item in confirmation.items
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


def _latest_order_confirmation_response(confirmation):
    items_list = []
    for item in confirmation.items:
        qty = item.quantity
        price = item.unit_price
        net_amt = item.net_amount
        if net_amt is None and qty is not None and price is not None:
            try:
                from decimal import Decimal
                net_amt = (Decimal(str(qty)) * Decimal(str(price))).quantize(Decimal("0.01"))
            except Exception:
                pass

        items_list.append({
            "unit_price": _format_decimal_str(price, places=2),
            "quantity": _format_decimal_str(qty, places=3) or "0.000",
            "material_name": item.material_name or item.description,
            "hsn_code": item.hsn_code,
            "net_amount": _format_decimal_str(net_amt, places=2),
        })

    return {
        "payment_terms": confirmation.payment_terms,
        "warranty_period": confirmation.warranty_period,
        "shipping_terms": confirmation.shipping_terms,
        "delivery_period": confirmation.delivery_period,
        "items": items_list,
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


def _handle_create_order_confirmation():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = SupplierOrderConfirmationCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    try:
        confirmation = create_supplier_order_confirmation_transaction(data=validated_data)

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            create_attachment(
                file=file,
                entity_type="order_confirmation",
                entity_id=confirmation.id,
                uploaded_by=user_id,
            )

        db.session.commit()
        return _order_confirmation_response(confirmation), 201

    except OrderConfirmationAlreadyExistsError as exc:
        db.session.rollback()
        return _error("ORDER_CONFIRMATION_ALREADY_EXISTS", str(exc), 409)
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
        current_app.logger.exception("Failed to create supplier order confirmation")
        return _error(
            "ORDER_CONFIRMATION_CREATE_FAILED",
            "Failed to create order confirmation.",
            500,
        )


def _handle_list_order_confirmations(args=None):
    if args is None:
        args = {}

    project_id = args.get("project_id") or request.args.get("project_id") or request.args.get("projectId")
    if project_id is not None:
        try:
            project_id = int(project_id)
        except (ValueError, TypeError):
            project_id = None

    supplier_id = args.get("supplier_id") or request.args.get("supplier_id") or request.args.get("supplierId")
    if supplier_id is not None:
        try:
            supplier_id = int(supplier_id)
        except (ValueError, TypeError):
            supplier_id = None

    ref_no = args.get("ref_no") or args.get("reference_number") or request.args.get("ref_no") or request.args.get("refNo")

    try:
        confirmations = list_supplier_order_confirmation_records(
            project_id=project_id,
        )
        return [_order_confirmation_response(c) for c in confirmations], 200
    except Exception:
        current_app.logger.exception("Failed to list supplier order confirmations")
        return _error(
            "ORDER_CONFIRMATION_LIST_FAILED",
            "Failed to list order confirmations.",
            500,
        )


def _handle_get_latest_order_confirmation(args=None):
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
        confirmation = get_latest_supplier_order_confirmation_record(project_id)
        return _latest_order_confirmation_response(confirmation), 200
    except ProjectNotFoundError as exc:
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except OrderConfirmationNotFoundError as exc:
        return _error("ORDER_CONFIRMATION_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get latest order confirmation")
        return _error(
            "ORDER_CONFIRMATION_GET_FAILED",
            "Failed to get latest order confirmation.",
            500,
        )





def _handle_update_order_confirmation(order_confirmation_id: int):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = SupplierOrderConfirmationUpdateSchema()
        validated_data = schema.load(raw_payload) if raw_payload else {}
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    try:
        confirmation = update_supplier_order_confirmation_transaction(
            confirmation_id=order_confirmation_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            create_attachment(
                file=file,
                entity_type="order_confirmation",
                entity_id=confirmation.id,
                uploaded_by=user_id,
            )

        db.session.commit()
        return _order_confirmation_response(confirmation), 200

    except OrderConfirmationNotFoundError as exc:
        db.session.rollback()
        return _error("ORDER_CONFIRMATION_NOT_FOUND", str(exc), 404)
    except OrderConfirmationAlreadyExistsError as exc:
        db.session.rollback()
        return _error("ORDER_CONFIRMATION_ALREADY_EXISTS", str(exc), 409)
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
        current_app.logger.exception("Failed to update order confirmation")
        return _error(
            "ORDER_CONFIRMATION_UPDATE_FAILED",
            "Failed to update order confirmation.",
            500,
        )


def _handle_delete_order_confirmation(order_confirmation_id: int):
    try:
        storage_keys = delete_supplier_order_confirmation_transaction(order_confirmation_id)
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

        return jsonify({"success": True, "message": "Order confirmation deleted successfully."}), 200
    except OrderConfirmationNotFoundError as exc:
        db.session.rollback()
        return _error("ORDER_CONFIRMATION_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete order confirmation")
        return _error(
            "ORDER_CONFIRMATION_DELETE_FAILED",
            "Failed to delete order confirmation.",
            500,
        )


# ==========================================
# /api/v1/order-confirmations endpoints
# ==========================================

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
                        "description": "Serialized JSON string matching SupplierOrderConfirmationCreateSchema",
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                },
            },
        },
        "application/json": {
            "schema": SupplierOrderConfirmationCreateSchema,
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
                        "description": "Serialized JSON string matching SupplierOrderConfirmationUpdateSchema",
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                },
            },
        },
        "application/json": {
            "schema": SupplierOrderConfirmationUpdateSchema,
        },
    },
}


@order_confirmation_bp.post("")
@order_confirmation_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_CREATE_DOC,
)
@order_confirmation_bp.response(201, SupplierOrderConfirmationResponseSchema)
@jwt_required()
def create_order_confirmation():
    return _handle_create_order_confirmation()


@order_confirmation_bp.get("")
@order_confirmation_bp.doc(security=[{"BearerAuth": []}])
@order_confirmation_bp.arguments(SupplierOrderConfirmationQuerySchema, location="query")
@order_confirmation_bp.response(200, SupplierOrderConfirmationResponseSchema(many=True))
@jwt_required()
def list_order_confirmations(args=None):
    return _handle_list_order_confirmations(args)


@order_confirmation_bp.get("/latest")
@order_confirmation_bp.doc(security=[{"BearerAuth": []}])
@order_confirmation_bp.arguments(SupplierOrderConfirmationQuerySchema, location="query")
@order_confirmation_bp.response(200, LatestSupplierOrderConfirmationResponseSchema)
@jwt_required()
def get_latest_order_confirmation(args=None):
    return _handle_get_latest_order_confirmation(args)



@order_confirmation_bp.patch("/<int:order_confirmation_id>")
@order_confirmation_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_UPDATE_DOC,
)
@order_confirmation_bp.response(200, SupplierOrderConfirmationResponseSchema)
@jwt_required()
def update_order_confirmation(order_confirmation_id):
    return _handle_update_order_confirmation(order_confirmation_id)


@order_confirmation_bp.delete("/<int:order_confirmation_id>")
@order_confirmation_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_order_confirmation(order_confirmation_id):
    return _handle_delete_order_confirmation(order_confirmation_id)


