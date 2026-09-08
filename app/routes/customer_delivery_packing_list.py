import json

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.schemas.customer_delivery_packing_list import (
    CustomerDeliveryPackingListCreateSchema,
    CustomerDeliveryPackingListQuerySchema,
    CustomerDeliveryPackingListResponseSchema,
    CustomerDeliveryPackingListUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    list_attachments,
)
from app.services.customer_delivery_packing_list_service import (
    CustomerDeliveryPackingListNotFoundError,
    ProjectNotFoundError,
    create_customer_delivery_packing_list_transaction,
    delete_customer_delivery_packing_list_transaction,
    get_customer_delivery_packing_list_record,
    list_customer_delivery_packing_list_records,
    update_customer_delivery_packing_list_transaction,
)
from app.services.storage.factory import get_storage

customer_delivery_packing_list_bp = Blueprint(
    "customer_delivery_packing_lists",
    __name__,
    url_prefix="/api/v1/customer-packing-lists",
    description="Customer Delivery Packing List APIs",
)


def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _customer_delivery_packing_list_response(packing_list):
    attachments = list_attachments(
        entity_type="customer_delivery_packing_list",
        entity_id=packing_list.id,
    )
    return {
        "id": packing_list.id,
        "project_id": packing_list.project_id,
        "packing_list_no": packing_list.packing_list_no,
        "packing_list_number": packing_list.packing_list_no,
        "packing_list_date": packing_list.packing_list_date,
        "total_no_of_packs": packing_list.total_no_of_packs,
        "packing_condition": packing_list.packing_condition,
        "net_weight": packing_list.net_weight,
        "net_weight_kg": packing_list.net_weight,
        "gross_weight": packing_list.gross_weight,
        "gross_weight_kg": packing_list.gross_weight,
        "remark": packing_list.remark,
        "remarks": packing_list.remark,
        "created_at": packing_list.created_at,
        "updated_at": packing_list.updated_at,
        "items": [
            {
                "id": item.id,
                "packing_list_id": item.packing_list_id,
                "package_no": item.package_no,
                "material_name": item.material_name,
                "material_description": item.material_name,
                "hsn_code": item.hsn_code,
                "hsn_sac": item.hsn_code,
                "quantity": str(item.quantity) if item.quantity is not None else None,
                "weight": str(item.weight) if item.weight is not None else None,
                "total_weight_kg": str(item.weight) if item.weight is not None else None,
                "weight_per_unit_kg": str(item.weight) if item.weight is not None else None,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            for item in packing_list.items
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


def _handle_create_customer_delivery_packing_list():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = CustomerDeliveryPackingListCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        packing_list = create_customer_delivery_packing_list_transaction(
            data=validated_data
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="customer_delivery_packing_list",
                entity_id=packing_list.id,
                uploaded_by=user_id,
            )
            if storage_key:
                storage_keys.append(storage_key)

        db.session.commit()
        return _customer_delivery_packing_list_response(packing_list), 201
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
        current_app.logger.exception("Failed to create customer delivery packing list")
        return _error(
            "CUSTOMER_DELIVERY_PACKING_LIST_CREATE_FAILED",
            "Failed to create customer delivery packing list.",
            500,
        )


def _handle_list_customer_delivery_packing_lists(args=None):
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

    packing_list_no = (
        args.get("packing_list_no")
        or request.args.get("packing_list_no")
        or request.args.get("packingListNo")
        or request.args.get("packing_list_number")
    )

    try:
        packing_lists = list_customer_delivery_packing_list_records(
            project_id=project_id,
            packing_list_no=packing_list_no,
        )
        return (
            [
                _customer_delivery_packing_list_response(pl)
                for pl in packing_lists
            ],
            200,
        )
    except Exception:
        current_app.logger.exception("Failed to list customer delivery packing lists")
        return _error(
            "CUSTOMER_DELIVERY_PACKING_LIST_LIST_FAILED",
            "Failed to list customer delivery packing lists.",
            500,
        )


def _handle_get_customer_delivery_packing_list(packing_list_id: int):
    try:
        packing_list = get_customer_delivery_packing_list_record(packing_list_id)
        return _customer_delivery_packing_list_response(packing_list), 200
    except CustomerDeliveryPackingListNotFoundError as exc:
        return _error("CUSTOMER_DELIVERY_PACKING_LIST_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get customer delivery packing list")
        return _error(
            "CUSTOMER_DELIVERY_PACKING_LIST_GET_FAILED",
            "Failed to get customer delivery packing list.",
            500,
        )


def _handle_update_customer_delivery_packing_list(packing_list_id: int):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = CustomerDeliveryPackingListUpdateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        packing_list = update_customer_delivery_packing_list_transaction(
            packing_list_id=packing_list_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="customer_delivery_packing_list",
                entity_id=packing_list.id,
                uploaded_by=user_id,
            )
            if storage_key:
                storage_keys.append(storage_key)

        db.session.commit()
        return _customer_delivery_packing_list_response(packing_list), 200
    except CustomerDeliveryPackingListNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("CUSTOMER_DELIVERY_PACKING_LIST_NOT_FOUND", str(exc), 404)
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
        current_app.logger.exception("Failed to update customer delivery packing list")
        return _error(
            "CUSTOMER_DELIVERY_PACKING_LIST_UPDATE_FAILED",
            "Failed to update customer delivery packing list.",
            500,
        )


def _handle_delete_customer_delivery_packing_list(packing_list_id: int):
    try:
        storage_keys = delete_customer_delivery_packing_list_transaction(
            packing_list_id
        )
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
                    "message": "Customer delivery packing list deleted successfully.",
                }
            ),
            200,
        )
    except CustomerDeliveryPackingListNotFoundError as exc:
        db.session.rollback()
        return _error("CUSTOMER_DELIVERY_PACKING_LIST_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete customer delivery packing list")
        return _error(
            "CUSTOMER_DELIVERY_PACKING_LIST_DELETE_FAILED",
            "Failed to delete customer delivery packing list.",
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
                        "description": "Serialized JSON string matching CustomerDeliveryPackingListCreateSchema",
                        "example": (
                            '{"project_id":2,"packing_list_no":"vgfrde467","packing_list_date":"2026-09-07","total_no_of_packs":7,"packing_condition":"bvcfgdesr5gyuj","net_weight":"465tyghvb","gross_weight":"v cfdrytugyh","items":[{"package_no":"Box #1","material_name":"steel cold","hsn_code":"65465","quantity":55,"weight":8},{"package_no":"Box #2","material_name":"gdfhbvf","hsn_code":"5464","quantity":55,"weight":855}]}'
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
            "schema": CustomerDeliveryPackingListCreateSchema,
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
                        "description": "Serialized JSON string matching CustomerDeliveryPackingListUpdateSchema",
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                },
            },
        },
        "application/json": {
            "schema": CustomerDeliveryPackingListUpdateSchema,
        },
    },
}


@customer_delivery_packing_list_bp.post("")
@customer_delivery_packing_list_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_CREATE_DOC,
)
@customer_delivery_packing_list_bp.response(
    201, CustomerDeliveryPackingListResponseSchema
)
@jwt_required()
def create_customer_delivery_packing_list():
    return _handle_create_customer_delivery_packing_list()


@customer_delivery_packing_list_bp.get("")
@customer_delivery_packing_list_bp.doc(security=[{"BearerAuth": []}])
@customer_delivery_packing_list_bp.arguments(
    CustomerDeliveryPackingListQuerySchema, location="query"
)
@customer_delivery_packing_list_bp.response(
    200, CustomerDeliveryPackingListResponseSchema(many=True)
)
@jwt_required()
def list_customer_delivery_packing_lists(args=None):
    return _handle_list_customer_delivery_packing_lists(args)



@customer_delivery_packing_list_bp.patch("/<int:packing_list_id>")
@customer_delivery_packing_list_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_UPDATE_DOC,
)
@customer_delivery_packing_list_bp.response(
    200, CustomerDeliveryPackingListResponseSchema
)
@jwt_required()
def update_customer_delivery_packing_list(packing_list_id):
    return _handle_update_customer_delivery_packing_list(packing_list_id)


@customer_delivery_packing_list_bp.delete("/<int:packing_list_id>")
@customer_delivery_packing_list_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_customer_delivery_packing_list(packing_list_id):
    return _handle_delete_customer_delivery_packing_list(packing_list_id)

