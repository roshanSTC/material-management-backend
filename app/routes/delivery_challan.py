import json

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.schemas.delivery_challan import (
    DeliveryChallanCreateSchema,
    DeliveryChallanQuerySchema,
    DeliveryChallanResponseSchema,
    DeliveryChallanUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    list_attachments,
)
from app.services.delivery_challan_service import (
    DeliveryChallanNotFoundError,
    ProjectNotFoundError,
    create_delivery_challan_transaction,
    delete_delivery_challan_transaction,
    get_delivery_challan_record,
    list_delivery_challan_records,
    update_delivery_challan_transaction,
)
from app.services.storage.factory import get_storage

delivery_challan_bp = Blueprint(
    "delivery_challans",
    __name__,
    url_prefix="/api/v1/delivery-challans",
    description="Delivery Challan APIs",
)


def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _delivery_challan_response(delivery_challan):
    attachments = list_attachments(
        entity_type="delivery_challan",
        entity_id=delivery_challan.id,
    )
    return {
        "id": delivery_challan.id,
        "project_id": delivery_challan.project_id,
        "delivery_challan_no": delivery_challan.delivery_challan_no,
        "delivery_challan_number": delivery_challan.delivery_challan_no,
        "delivery_challan_date": delivery_challan.delivery_challan_date,
        "remark": delivery_challan.remark,
        "remarks": delivery_challan.remark,
        "created_at": delivery_challan.created_at,
        "updated_at": delivery_challan.updated_at,
        "items": [
            {
                "id": item.id,
                "delivery_challan_id": item.delivery_challan_id,
                "material_name": item.material_name,
                "material_description": item.material_name,
                "hsn_code": item.hsn_code,
                "hsn_sac": item.hsn_code,
                "quantity": str(item.quantity) if item.quantity is not None else None,
                "unit_price": str(item.unit_price) if item.unit_price is not None else None,
                "rate_per_unit": str(item.unit_price) if item.unit_price is not None else None,
                "net_amount": str(item.net_amount) if item.net_amount is not None else None,
                "amount": str(item.net_amount) if item.net_amount is not None else None,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            for item in delivery_challan.items
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


def _handle_create_delivery_challan():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = DeliveryChallanCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        delivery_challan = create_delivery_challan_transaction(
            data=validated_data
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="delivery_challan",
                entity_id=delivery_challan.id,
                uploaded_by=user_id,
            )
            if storage_key:
                storage_keys.append(storage_key)

        db.session.commit()
        return _delivery_challan_response(delivery_challan), 201
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
        current_app.logger.exception("Failed to create delivery challan")
        return _error(
            "DELIVERY_CHALLAN_CREATE_FAILED",
            "Failed to create delivery challan.",
            500,
        )


def _handle_list_delivery_challans(args=None):
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
        delivery_challans = list_delivery_challan_records(
            project_id=project_id,
        )
        return (
            [
                _delivery_challan_response(dc)
                for dc in delivery_challans
            ],
            200,
        )
    except Exception:
        current_app.logger.exception("Failed to list delivery challans")
        return _error(
            "DELIVERY_CHALLAN_LIST_FAILED",
            "Failed to list delivery challans.",
            500,
        )


def _handle_get_delivery_challan(delivery_challan_id: int):
    try:
        delivery_challan = get_delivery_challan_record(delivery_challan_id)
        return _delivery_challan_response(delivery_challan), 200
    except DeliveryChallanNotFoundError as exc:
        return _error("DELIVERY_CHALLAN_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get delivery challan")
        return _error(
            "DELIVERY_CHALLAN_GET_FAILED",
            "Failed to get delivery challan.",
            500,
        )


def _handle_update_delivery_challan(delivery_challan_id: int):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = DeliveryChallanUpdateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        delivery_challan = update_delivery_challan_transaction(
            delivery_challan_id=delivery_challan_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="delivery_challan",
                entity_id=delivery_challan.id,
                uploaded_by=user_id,
            )
            if storage_key:
                storage_keys.append(storage_key)

        db.session.commit()
        return _delivery_challan_response(delivery_challan), 200
    except DeliveryChallanNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("DELIVERY_CHALLAN_NOT_FOUND", str(exc), 404)
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
        current_app.logger.exception("Failed to update delivery challan")
        return _error(
            "DELIVERY_CHALLAN_UPDATE_FAILED",
            "Failed to update delivery challan.",
            500,
        )


def _handle_delete_delivery_challan(delivery_challan_id: int):
    try:
        storage_keys = delete_delivery_challan_transaction(
            delivery_challan_id
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
                    "message": "Delivery challan deleted successfully.",
                }
            ),
            200,
        )
    except DeliveryChallanNotFoundError as exc:
        db.session.rollback()
        return _error("DELIVERY_CHALLAN_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete delivery challan")
        return _error(
            "DELIVERY_CHALLAN_DELETE_FAILED",
            "Failed to delete delivery challan.",
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
                        "description": "Serialized JSON string matching DeliveryChallanCreateSchema",
                        "example": (
                            '{"project_id":2,"delivery_challan_no":"DC-965TFC-T7G","delivery_challan_date":"2026-09-15","remark":"packingConditionOptions","items":[{"material_name":"steel cold","hsn_code":"65465","quantity":55,"unit_price":34,"net_amount":1870},{"material_name":"gdfhbvf","hsn_code":"5464","quantity":55,"unit_price":45,"net_amount":2475}]}'
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
            "schema": DeliveryChallanCreateSchema,
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
                        "description": "Serialized JSON string matching DeliveryChallanUpdateSchema",
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                },
            },
        },
        "application/json": {
            "schema": DeliveryChallanUpdateSchema,
        },
    },
}


@delivery_challan_bp.post("")
@delivery_challan_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_CREATE_DOC,
)
@delivery_challan_bp.response(
    201, DeliveryChallanResponseSchema
)
@jwt_required()
def create_delivery_challan():
    return _handle_create_delivery_challan()


@delivery_challan_bp.get("")
@delivery_challan_bp.doc(security=[{"BearerAuth": []}])
@delivery_challan_bp.arguments(
    DeliveryChallanQuerySchema, location="query"
)
@delivery_challan_bp.response(
    200, DeliveryChallanResponseSchema(many=True)
)
@jwt_required()
def list_delivery_challans(args=None):
    return _handle_list_delivery_challans(args)



@delivery_challan_bp.patch("/<int:delivery_challan_id>")
@delivery_challan_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_UPDATE_DOC,
)
@delivery_challan_bp.response(
    200, DeliveryChallanResponseSchema
)
@jwt_required()
def update_delivery_challan(delivery_challan_id):
    return _handle_update_delivery_challan(delivery_challan_id)


@delivery_challan_bp.delete("/<int:delivery_challan_id>")
@delivery_challan_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_delivery_challan(delivery_challan_id):
    return _handle_delete_delivery_challan(delivery_challan_id)

