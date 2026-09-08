import json

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.schemas.supplier_packing_list import (
    SupplierPackingListCreateSchema,
    SupplierPackingListQuerySchema,
    SupplierPackingListResponseSchema,
    SupplierPackingListUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    list_attachments,
)
from app.services.storage.factory import get_storage
from app.services.supplier_packing_list_service import (
    ProjectNotFoundError,
    SupplierNotFoundError,
    SupplierPackingListAlreadyExistsError,
    SupplierPackingListNotFoundError,
    create_supplier_packing_list_transaction,
    delete_supplier_packing_list_transaction,
    get_supplier_packing_list_record,
    list_supplier_packing_list_records,
    update_supplier_packing_list_transaction,
)

supplier_packing_list_bp = Blueprint(
    "supplier_packing_lists",
    __name__,
    url_prefix="/api/v1/supplier-packing-lists",
    description="Supplier Packing List APIs",
)


def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _supplier_packing_list_response(packing_list):
    attachments = list_attachments(
        entity_type="supplier_packing_list",
        entity_id=packing_list.id,
    )

    return {
        "id": packing_list.id,
        "project_id": packing_list.project_id,
        "supplier_id": packing_list.supplier_id,
        "packing_list_no": packing_list.packing_list_no,
        "packing_list_number": packing_list.packing_list_no,
        "packing_list_date": packing_list.packing_list_date,
        "packing_condition": packing_list.packing_condition,
        "weight": packing_list.weight,
        "total_weight": packing_list.total_weight,
        "total_gross_weight_kg": packing_list.total_weight,
        "remark": packing_list.remark,
        "remarks": packing_list.remark,
        "created_at": packing_list.created_at,
        "updated_at": packing_list.updated_at,
        "items": [
            {
                "id": item.id,
                "packing_list_id": item.packing_list_id,
                "supplier_packing_list_id": item.packing_list_id,
                "material_name": item.material_name or item.description,
                "description": item.description,
                "material_description": item.description,
                "hsn_code": item.hsn_code,
                "hsn": item.hsn_code,
                "hsn_sac": item.hsn_code,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "net_amount": item.net_amount,
                "weight": item.weight,
                "unit_weight": item.unit_weight,
                "unit_weight_kg": item.unit_weight,
                "total_weight": item.total_weight,
                "created_at": item.created_at,
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
    else:
        raw_payload = request.get_json(silent=True) or {}

    return raw_payload, files


def _handle_create_supplier_packing_list():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = SupplierPackingListCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    try:
        packing_list = create_supplier_packing_list_transaction(data=validated_data)

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            create_attachment(
                file=file,
                entity_type="supplier_packing_list",
                entity_id=packing_list.id,
                uploaded_by=user_id,
            )

        db.session.commit()
        return _supplier_packing_list_response(packing_list), 201

    except SupplierPackingListAlreadyExistsError as exc:
        db.session.rollback()
        return _error("SUPPLIER_PACKING_LIST_ALREADY_EXISTS", str(exc), 409)
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
        current_app.logger.exception("Failed to create supplier packing list")
        return _error(
            "SUPPLIER_PACKING_LIST_CREATE_FAILED",
            "Failed to create supplier packing list.",
            500,
        )


def _handle_list_supplier_packing_lists(args=None):
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
        packing_lists = list_supplier_packing_list_records(
            project_id=project_id,
        )
        return [_supplier_packing_list_response(pl) for pl in packing_lists], 200
    except Exception:
        current_app.logger.exception("Failed to list supplier packing lists")
        return _error(
            "SUPPLIER_PACKING_LIST_LIST_FAILED",
            "Failed to list supplier packing lists.",
            500,
        )


def _handle_get_supplier_packing_list(supplier_packing_list_id: int):
    try:
        packing_list = get_supplier_packing_list_record(supplier_packing_list_id)
        return _supplier_packing_list_response(packing_list), 200
    except SupplierPackingListNotFoundError as exc:
        return _error("SUPPLIER_PACKING_LIST_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get supplier packing list")
        return _error(
            "SUPPLIER_PACKING_LIST_GET_FAILED",
            "Failed to get supplier packing list.",
            500,
        )


def _handle_update_supplier_packing_list(supplier_packing_list_id: int):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = SupplierPackingListUpdateSchema()
        validated_data = schema.load(raw_payload) if raw_payload else {}
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    try:
        packing_list = update_supplier_packing_list_transaction(
            packing_list_id=supplier_packing_list_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            create_attachment(
                file=file,
                entity_type="supplier_packing_list",
                entity_id=packing_list.id,
                uploaded_by=user_id,
            )

        db.session.commit()
        return _supplier_packing_list_response(packing_list), 200

    except SupplierPackingListNotFoundError as exc:
        db.session.rollback()
        return _error("SUPPLIER_PACKING_LIST_NOT_FOUND", str(exc), 404)
    except SupplierPackingListAlreadyExistsError as exc:
        db.session.rollback()
        return _error("SUPPLIER_PACKING_LIST_ALREADY_EXISTS", str(exc), 409)
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
        current_app.logger.exception("Failed to update supplier packing list")
        return _error(
            "SUPPLIER_PACKING_LIST_UPDATE_FAILED",
            "Failed to update supplier packing list.",
            500,
        )


def _handle_delete_supplier_packing_list(supplier_packing_list_id: int):
    try:
        storage_keys = delete_supplier_packing_list_transaction(supplier_packing_list_id)
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

        return jsonify({"success": True, "message": "Supplier packing list deleted successfully."}), 200
    except SupplierPackingListNotFoundError as exc:
        db.session.rollback()
        return _error("SUPPLIER_PACKING_LIST_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete supplier packing list")
        return _error(
            "SUPPLIER_PACKING_LIST_DELETE_FAILED",
            "Failed to delete supplier packing list.",
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
                        "description": "Serialized JSON string matching SupplierPackingListCreateSchema",
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                },
            },
        },
        "application/json": {
            "schema": SupplierPackingListCreateSchema,
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
                        "description": "Serialized JSON string matching SupplierPackingListUpdateSchema",
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                },
            },
        },
        "application/json": {
            "schema": SupplierPackingListUpdateSchema,
        },
    },
}


@supplier_packing_list_bp.post("")
@supplier_packing_list_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_CREATE_DOC,
)
@supplier_packing_list_bp.response(201, SupplierPackingListResponseSchema)
@jwt_required()
def create_supplier_packing_list():
    return _handle_create_supplier_packing_list()


@supplier_packing_list_bp.get("")
@supplier_packing_list_bp.doc(security=[{"BearerAuth": []}])
@supplier_packing_list_bp.arguments(SupplierPackingListQuerySchema, location="query")
@supplier_packing_list_bp.response(200, SupplierPackingListResponseSchema(many=True))
@jwt_required()
def list_supplier_packing_lists(args=None):
    return _handle_list_supplier_packing_lists(args)



@supplier_packing_list_bp.patch("/<int:supplier_packing_list_id>")
@supplier_packing_list_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_UPDATE_DOC,
)
@supplier_packing_list_bp.response(200, SupplierPackingListResponseSchema)
@jwt_required()
def update_supplier_packing_list(supplier_packing_list_id):
    return _handle_update_supplier_packing_list(supplier_packing_list_id)


@supplier_packing_list_bp.delete("/<int:supplier_packing_list_id>")
@supplier_packing_list_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_supplier_packing_list(supplier_packing_list_id):
    return _handle_delete_supplier_packing_list(supplier_packing_list_id)

