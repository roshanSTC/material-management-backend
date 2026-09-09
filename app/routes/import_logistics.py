import json

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.schemas.import_logistics import (
    ImportLogisticsCreateSchema,
    ImportLogisticsQuerySchema,
    ImportLogisticsResponseSchema,
    ImportLogisticsUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    list_attachments,
)
from app.services.import_logistics_service import (
    ImportLogisticsNotFoundError,
    ProjectNotFoundError,
    SupplierNotFoundError,
    create_import_logistics_transaction,
    delete_import_logistics_transaction,
    get_import_logistics_record,
    list_import_logistics_records,
    update_import_logistics_transaction,
)
from app.services.storage.factory import get_storage

import_logistics_bp = Blueprint(
    "import_logistics",
    __name__,
    url_prefix="/api/v1/import-logistics",
    description="Import Logistics APIs",
)


def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _import_logistics_response(logistics):
    attachments = list_attachments(
        entity_type="import_logistics",
        entity_id=logistics.id,
    )

    return {
        "id": logistics.id,
        "project_id": logistics.project_id,
        "supplier_id": logistics.supplier_id,
        "logistic_type": logistics.logistic_type,
        "date": logistics.date,
        "port_of_discharge": logistics.port_of_discharge,
        "remark": logistics.remark,
        # Air fields
        "airway_bill_no": logistics.airway_bill_no,
        "flight_name": logistics.flight_name,
        "flight_no": logistics.flight_no,
        "airport_of_loading": logistics.airport_of_loading,
        # Sea fields
        "bill_of_lading_no": logistics.bill_of_lading_no,
        "vessel_name": logistics.vessel_name,
        "voyage_no": logistics.voyage_no,
        "port_of_loading": logistics.port_of_loading,
        # Timestamps
        "created_at": logistics.created_at,
        "updated_at": logistics.updated_at,
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


def _handle_create_import_logistics():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = ImportLogisticsCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        logistics = create_import_logistics_transaction(data=validated_data)

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="import_logistics",
                entity_id=logistics.id,
                uploaded_by=user_id,
            )
            storage_keys.append(storage_key)

        db.session.commit()
        return _import_logistics_response(logistics), 201

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
        current_app.logger.exception("Failed to create import logistics")
        return _error(
            "IMPORT_LOGISTICS_CREATE_FAILED",
            "Failed to create import logistics.",
            500,
        )


def _handle_list_import_logistics(args=None):
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
        records = list_import_logistics_records(
            project_id=project_id,
        )
        return [_import_logistics_response(rec) for rec in records], 200
    except Exception:
        current_app.logger.exception("Failed to list import logistics")
        return _error(
            "IMPORT_LOGISTICS_LIST_FAILED",
            "Failed to list import logistics.",
            500,
        )


def _handle_get_import_logistics(logistics_id: int):
    try:
        record = get_import_logistics_record(logistics_id)
        return _import_logistics_response(record), 200
    except ImportLogisticsNotFoundError as exc:
        return _error("IMPORT_LOGISTICS_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get import logistics")
        return _error(
            "IMPORT_LOGISTICS_GET_FAILED",
            "Failed to get import logistics.",
            500,
        )


def _handle_update_import_logistics(logistics_id: int):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = ImportLogisticsUpdateSchema()
        validated_data = schema.load(raw_payload) if raw_payload else {}
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        record = update_import_logistics_transaction(
            logistics_id=logistics_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="import_logistics",
                entity_id=record.id,
                uploaded_by=user_id,
            )
            storage_keys.append(storage_key)

        db.session.commit()
        return _import_logistics_response(record), 200

    except ImportLogisticsNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("IMPORT_LOGISTICS_NOT_FOUND", str(exc), 404)
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
        current_app.logger.exception("Failed to update import logistics")
        return _error(
            "IMPORT_LOGISTICS_UPDATE_FAILED",
            "Failed to update import logistics.",
            500,
        )


def _handle_delete_import_logistics(logistics_id: int):
    try:
        storage_keys = delete_import_logistics_transaction(logistics_id)
        db.session.commit()

        storage = get_storage()
        for key in storage_keys:
            try:
                if storage.exists(key):
                    storage.delete(key)
            except Exception:
                current_app.logger.warning(
                    f"Failed to delete attachment storage key {key} during import logistics deletion."
                )

        return {
            "success": True,
            "message": "Import logistics deleted successfully.",
        }, 200

    except ImportLogisticsNotFoundError as exc:
        db.session.rollback()
        return _error("IMPORT_LOGISTICS_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete import logistics")
        return _error(
            "IMPORT_LOGISTICS_DELETE_FAILED",
            "Failed to delete import logistics.",
            500,
        )


_REQUEST_BODY_CREATE_DOC = {
    "required": True,
    "description": "Form data containing serialized JSON payload in 'data' field and document attachments in 'file' field.",
    "content": {
        "multipart/form-data": {
            "schema": {
                "type": "object",
                "required": ["data"],
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Serialized JSON string matching ImportLogisticsCreateSchema. Payload itself specifies logistic_type ('air' or 'sea').",
                        "example": '{"project_id":1,"logistic_type":"sea","date":"2026-09-16","port_of_discharge":"dadar","remark":"Shipping Documents & Attachments","bill_of_lading_no":"DF4FR-34RG-4FD","vessel_name":"Oscare ","voyage_no":"3REF4R43F","port_of_loading":"KURLA"}',
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                        "description": "Document attachment files (e.g. Bill of Lading, Airway Bill, Shipping documents)",
                    },
                },
            },
        },
        "application/json": {
            "schema": ImportLogisticsCreateSchema,
            "examples": {
                "sea": {
                    "summary": "Sea Logistics Payload",
                    "value": {
                        "project_id": 1,
                        "logistic_type": "sea",
                        "date": "2026-09-16",
                        "port_of_discharge": "dadar",
                        "remark": "Shipping Documents & Attachments",
                        "bill_of_lading_no": "DF4FR-34RG-4FD",
                        "vessel_name": "Oscare ",
                        "voyage_no": "3REF4R43F",
                        "port_of_loading": "KURLA",
                    },
                },
                "air": {
                    "summary": "Air Logistics Payload",
                    "value": {
                        "project_id": 1,
                        "logistic_type": "air",
                        "date": "2026-09-09",
                        "port_of_discharge": "dadar",
                        "remark": "Shipping Documents & Attachments",
                        "airway_bill_no": "E45RE-G54-GF",
                        "flight_name": "Eirates",
                        "flight_no": "234SD4",
                        "airport_of_loading": "nalasupara",
                    },
                },
            },
        },
    },
}

_REQUEST_BODY_UPDATE_DOC = {
    "required": False,
    "description": "Form data containing serialized JSON payload in 'data' field and optional document attachments in 'file' field.",
    "content": {
        "multipart/form-data": {
            "schema": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Serialized JSON string matching ImportLogisticsUpdateSchema",
                        "example": '{"port_of_discharge":"dadar","remark":"Shipping Documents & Attachments","bill_of_lading_no":"DF4FR-34RG-4FD","vessel_name":"Oscare ","voyage_no":"3REF4R43F","port_of_loading":"KURLA"}',
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                        "description": "Document attachment files",
                    },
                },
            },
        },
        "application/json": {
            "schema": ImportLogisticsUpdateSchema,
        },
    },
}


@import_logistics_bp.post("")
@import_logistics_bp.doc(
    security=[{"BearerAuth": []}],
    summary="Create import logistics record",
    description="Supports JSON payload and multipart/form-data with file attachments for air and sea logistics.",
    requestBody=_REQUEST_BODY_CREATE_DOC,
)
@import_logistics_bp.response(201, ImportLogisticsResponseSchema)
@jwt_required()
def create_import_logistics():
    return _handle_create_import_logistics()


@import_logistics_bp.get("")
@import_logistics_bp.doc(
    security=[{"BearerAuth": []}],
    summary="Get all import logistics records",
    description="List all import logistics records with optional filtering by project_id, supplier_id, logistic_type.",
)
@import_logistics_bp.arguments(ImportLogisticsQuerySchema, location="query")
@import_logistics_bp.response(200, ImportLogisticsResponseSchema(many=True))
@jwt_required()
def list_import_logistics(args=None):
    return _handle_list_import_logistics(args)



@import_logistics_bp.patch("/<int:logistics_id>")
@import_logistics_bp.doc(
    security=[{"BearerAuth": []}],
    summary="Update import logistics record",
    requestBody=_REQUEST_BODY_UPDATE_DOC,
)
@import_logistics_bp.response(200, ImportLogisticsResponseSchema)
@jwt_required()
def update_import_logistics(logistics_id: int):
    return _handle_update_import_logistics(logistics_id)


@import_logistics_bp.delete("/<int:logistics_id>")
@import_logistics_bp.doc(
    security=[{"BearerAuth": []}],
    summary="Delete import logistics record",
)
@jwt_required()
def delete_import_logistics(logistics_id: int):
    return _handle_delete_import_logistics(logistics_id)

