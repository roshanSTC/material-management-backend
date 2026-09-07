import json

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.schemas.purchase_order import (
    PurchaseOrderCreateSchema,
    PurchaseOrderQuerySchema,
    PurchaseOrderResponseSchema,
    PurchaseOrderUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    list_attachments,
)
from app.services.purchase_order_service import (
    CustomerNotFoundError,
    CustomerProjectMismatchError,
    ProjectNotFoundError,
    PurchaseOrderNotFoundError,
    TenderNotFoundError,
    create_purchase_order_transaction,
    delete_purchase_order_transaction,
    get_latest_purchase_order_record,
    get_purchase_order_record,
    list_purchase_order_records,
    update_purchase_order_transaction,
)
from app.services.storage.factory import get_storage

purchase_order_bp = Blueprint(
    "purchase_orders",
    __name__,
    url_prefix="/api/v1/purchase-orders",
    description="Purchase Order APIs",
)



def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _purchase_order_response(purchase_order):
    attachments = list_attachments(
        entity_type="purchase_order",
        entity_id=purchase_order.id,
    )
    return {
        "id": purchase_order.id,
        "project_id": purchase_order.project_id,
        "customer_id": purchase_order.customer_id,
        "tender_id": purchase_order.tender_id,
        "poc_name": purchase_order.poc_name,
        "email": purchase_order.email,
        "contact": purchase_order.contact,
        "po_no": purchase_order.po_number,
        "po_number": purchase_order.po_number,
        "po_title": purchase_order.po_title,
        "po_date": purchase_order.po_date,
        "delivery_date": purchase_order.delivery_date,
        "delivery_term": purchase_order.delivery_term,
        "delivery_terms": purchase_order.delivery_term,
        "payment_terms": purchase_order.payment_terms,
        "payment_term": purchase_order.payment_terms,
        "warranty_period": purchase_order.warranty_period,
        "gst_rate": purchase_order.gst_rate,
        "gst": purchase_order.gst_rate,
        "gst_amount": purchase_order.gst_amount,
        "total_net_amount": purchase_order.total_net_amount,
        "total_gross_amount": purchase_order.total_gross_amount,
        "remark": purchase_order.remark,
        "remarks": purchase_order.remark,
        "created_at": purchase_order.created_at,
        "updated_at": purchase_order.updated_at,
        "items": [
            {
                "id": item.id,
                "purchase_order_id": item.purchase_order_id,
                "material_name": item.material_name or item.description,
                "description": item.description,
                "hsn_code": item.hsn_code,
                "hsn_sac": item.hsn_code,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "net_amount": item.net_amount,
                "created_at": item.created_at,
            }
            for item in purchase_order.items
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


@purchase_order_bp.post("")
@purchase_order_bp.doc(
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
                            "description": "Serialized JSON string matching PurchaseOrderCreateSchema",
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
                "schema": PurchaseOrderCreateSchema,
            },
        },
    },
)
@purchase_order_bp.response(201, PurchaseOrderResponseSchema)
@jwt_required()
def create_purchase_order():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = PurchaseOrderCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    try:
        purchase_order = create_purchase_order_transaction(data=validated_data)

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            create_attachment(
                file=file,
                entity_type="purchase_order",
                entity_id=purchase_order.id,
                uploaded_by=user_id,
            )

        db.session.commit()
        return _purchase_order_response(purchase_order), 201

    except ProjectNotFoundError as exc:
        db.session.rollback()
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except CustomerNotFoundError as exc:
        db.session.rollback()
        return _error("CUSTOMER_NOT_FOUND", str(exc), 404)
    except CustomerProjectMismatchError as exc:
        db.session.rollback()
        return _error("CUSTOMER_PROJECT_MISMATCH", str(exc), 400)
    except TenderNotFoundError as exc:
        db.session.rollback()
        return _error("TENDER_NOT_FOUND", str(exc), 404)
    except AttachmentValidationError as exc:
        db.session.rollback()
        return _error("ATTACHMENT_VALIDATION_ERROR", str(exc), 400)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to create purchase order")
        return _error("PURCHASE_ORDER_CREATE_FAILED", "Failed to create purchase order.", 500)


@purchase_order_bp.get("")
@purchase_order_bp.doc(security=[{"BearerAuth": []}])
@purchase_order_bp.arguments(PurchaseOrderQuerySchema, location="query")
@purchase_order_bp.response(200, PurchaseOrderResponseSchema(many=True))
@jwt_required()
def list_purchase_orders(args=None):
    if args is None:
        args = {}

    project_id = (
        args.get("project_id")
    )
    if project_id is not None:
        try:
            project_id = int(project_id)
        except (ValueError, TypeError):
            project_id = None

    

    

    try:
        orders = list_purchase_order_records(
            project_id=project_id,
        )
        return [_purchase_order_response(po) for po in orders], 200
    except Exception:
        current_app.logger.exception("Failed to list purchase orders")
        return _error("PURCHASE_ORDER_LIST_FAILED", "Failed to list purchase orders.", 500)




@purchase_order_bp.get("/latest")
@purchase_order_bp.doc(security=[{"BearerAuth": []}])
@purchase_order_bp.response(200, PurchaseOrderResponseSchema)
@jwt_required()
def get_latest_purchase_order():
    project_id = (
        request.args.get("project_id")
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
        po = get_latest_purchase_order_record(project_id)
        return _purchase_order_response(po), 200
    except ProjectNotFoundError as exc:
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except PurchaseOrderNotFoundError as exc:
        return _error("PURCHASE_ORDER_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get latest purchase order")
        return _error("PURCHASE_ORDER_GET_FAILED", "Failed to get latest purchase order.", 500)


@purchase_order_bp.patch("/<int:purchase_order_id>")
@purchase_order_bp.doc(
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
                            "description": "Serialized JSON string matching PurchaseOrderUpdateSchema",
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
                "schema": PurchaseOrderUpdateSchema,
            },
        },
    },
)
@purchase_order_bp.response(200, PurchaseOrderResponseSchema)
@jwt_required()
def update_purchase_order(purchase_order_id):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = PurchaseOrderUpdateSchema()
        validated_data = schema.load(raw_payload) if raw_payload else {}
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    try:
        purchase_order = update_purchase_order_transaction(
            purchase_order_id=purchase_order_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            create_attachment(
                file=file,
                entity_type="purchase_order",
                entity_id=purchase_order.id,
                uploaded_by=user_id,
            )

        db.session.commit()
        return _purchase_order_response(purchase_order), 200

    except PurchaseOrderNotFoundError as exc:
        db.session.rollback()
        return _error("PURCHASE_ORDER_NOT_FOUND", str(exc), 404)
    except ProjectNotFoundError as exc:
        db.session.rollback()
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except CustomerNotFoundError as exc:
        db.session.rollback()
        return _error("CUSTOMER_NOT_FOUND", str(exc), 404)
    except CustomerProjectMismatchError as exc:
        db.session.rollback()
        return _error("CUSTOMER_PROJECT_MISMATCH", str(exc), 400)
    except TenderNotFoundError as exc:
        db.session.rollback()
        return _error("TENDER_NOT_FOUND", str(exc), 404)
    except AttachmentValidationError as exc:
        db.session.rollback()
        return _error("ATTACHMENT_VALIDATION_ERROR", str(exc), 400)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to update purchase order")
        return _error("PURCHASE_ORDER_UPDATE_FAILED", "Failed to update purchase order.", 500)


@purchase_order_bp.delete("/<int:purchase_order_id>")
@purchase_order_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_purchase_order(purchase_order_id):
    try:
        storage_keys = delete_purchase_order_transaction(purchase_order_id)
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

        return jsonify({"success": True, "message": "Purchase order deleted successfully."}), 200
    except PurchaseOrderNotFoundError as exc:
        db.session.rollback()
        return _error("PURCHASE_ORDER_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete purchase order")
        return _error("PURCHASE_ORDER_DELETE_FAILED", "Failed to delete purchase order.", 500)


