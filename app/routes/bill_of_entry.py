import json

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.schemas.bill_of_entry import (
    BillOfEntryCreateSchema,
    BillOfEntryQuerySchema,
    BillOfEntryResponseSchema,
    BillOfEntryUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    list_attachments,
)
from app.services.bill_of_entry_service import (
    BillOfEntryNotFoundError,
    ProjectNotFoundError,
    create_bill_of_entry_transaction,
    delete_bill_of_entry_transaction,
    get_bill_of_entry_record,
    list_bills_of_entry_records,
    update_bill_of_entry_transaction,
)
from app.services.storage.factory import get_storage

bill_of_entry_bp = Blueprint(
    "bills_of_entry",
    __name__,
    url_prefix="/api/v1/bills-of-entry",
    description="Bill of Entry APIs",
)


def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _bill_of_entry_response(record):
    attachments = list_attachments(
        entity_type="bill_of_entry",
        entity_id=record.id,
    )

    return {
        "id": record.id,
        "project_id": record.project_id,
        "bill_of_entry_no": record.bill_of_entry_no,
        "bill_of_entry_number": record.bill_of_entry_no,
        "date": record.date,
        "entry_date": record.date,
        "total_assessable_value": record.total_assessable_value,
        "bcd": record.bcd,
        "sws": record.sws,
        "igst": record.igst,
        "total_duty": record.total_duty,
        "remark": record.remark,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
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


def _handle_create_bill_of_entry():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = BillOfEntryCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        record = create_bill_of_entry_transaction(data=validated_data)

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="bill_of_entry",
                entity_id=record.id,
                uploaded_by=user_id,
            )
            storage_keys.append(storage_key)

        db.session.commit()
        return _bill_of_entry_response(record), 201

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
        current_app.logger.exception("Failed to create bill of entry")
        return _error(
            "BILL_OF_ENTRY_CREATE_FAILED",
            "Failed to create bill of entry.",
            500,
        )


def _handle_list_bills_of_entry(args=None):
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

    bill_of_entry_no = (
        args.get("bill_of_entry_no")
        or request.args.get("bill_of_entry_no")
        or request.args.get("billOfEntryNo")
    )

    try:
        records = list_bills_of_entry_records(
            project_id=project_id,
            bill_of_entry_no=bill_of_entry_no,
        )
        return [_bill_of_entry_response(rec) for rec in records], 200
    except Exception:
        current_app.logger.exception("Failed to list bills of entry")
        return _error(
            "BILL_OF_ENTRY_LIST_FAILED",
            "Failed to list bills of entry.",
            500,
        )


def _handle_get_bill_of_entry(bill_of_entry_id: int):
    try:
        record = get_bill_of_entry_record(bill_of_entry_id)
        return _bill_of_entry_response(record), 200
    except BillOfEntryNotFoundError as exc:
        return _error("BILL_OF_ENTRY_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get bill of entry")
        return _error(
            "BILL_OF_ENTRY_GET_FAILED",
            "Failed to get bill of entry.",
            500,
        )


def _handle_update_bill_of_entry(bill_of_entry_id: int):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = BillOfEntryUpdateSchema()
        validated_data = schema.load(raw_payload) if raw_payload else {}
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        record = update_bill_of_entry_transaction(
            bill_of_entry_id=bill_of_entry_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="bill_of_entry",
                entity_id=record.id,
                uploaded_by=user_id,
            )
            storage_keys.append(storage_key)

        db.session.commit()
        return _bill_of_entry_response(record), 200

    except BillOfEntryNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("BILL_OF_ENTRY_NOT_FOUND", str(exc), 404)
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
        current_app.logger.exception("Failed to update bill of entry")
        return _error(
            "BILL_OF_ENTRY_UPDATE_FAILED",
            "Failed to update bill of entry.",
            500,
        )


def _handle_delete_bill_of_entry(bill_of_entry_id: int):
    try:
        storage_keys = delete_bill_of_entry_transaction(bill_of_entry_id)
        db.session.commit()

        storage = get_storage()
        for key in storage_keys:
            try:
                if storage.exists(key):
                    storage.delete(key)
            except Exception:
                current_app.logger.warning(
                    f"Failed to delete attachment storage key {key} during bill of entry deletion."
                )

        return {
            "success": True,
            "message": "Bill of entry deleted successfully.",
        }, 200

    except BillOfEntryNotFoundError as exc:
        db.session.rollback()
        return _error("BILL_OF_ENTRY_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete bill of entry")
        return _error(
            "BILL_OF_ENTRY_DELETE_FAILED",
            "Failed to delete bill of entry.",
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
                        "description": "Serialized JSON string matching BillOfEntryCreateSchema",
                        "example": '{"project_id":1,"bill_of_entry_no":"454UHF-4FRDF","date":"2026-09-15","total_assessable_value":2445,"bcd":34,"sws":245,"igst":222,"total_duty":501,"remark":"Customs Documents & Attachments\\n"}',
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                        "description": "Customs document attachments (e.g. Bill of Entry copy, duty receipts)",
                    },
                },
            },
        },
        "application/json": {
            "schema": BillOfEntryCreateSchema,
            "examples": {
                "default": {
                    "summary": "Bill of Entry Payload",
                    "value": {
                        "project_id": 1,
                        "bill_of_entry_no": "454UHF-4FRDF",
                        "date": "2026-09-15",
                        "total_assessable_value": 2445,
                        "bcd": 34,
                        "sws": 245,
                        "igst": 222,
                        "total_duty": 501,
                        "remark": "Customs Documents & Attachments\n",
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
                        "description": "Serialized JSON string matching BillOfEntryUpdateSchema",
                        "example": '{"bill_of_entry_no":"454UHF-4FRDF","date":"2026-09-15","total_assessable_value":2445,"bcd":34,"sws":245,"igst":222,"total_duty":501,"remark":"Customs Documents & Attachments\\n"}',
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
            "schema": BillOfEntryUpdateSchema,
        },
    },
}


@bill_of_entry_bp.post("")
@bill_of_entry_bp.doc(
    security=[{"BearerAuth": []}],
    summary="Create bill of entry record",
    description="Supports form-data with serialized JSON in 'data' and files in 'file', as well as raw JSON.",
    requestBody=_REQUEST_BODY_CREATE_DOC,
)
@bill_of_entry_bp.response(201, BillOfEntryResponseSchema)
@jwt_required()
def create_bill_of_entry():
    return _handle_create_bill_of_entry()


@bill_of_entry_bp.get("")
@bill_of_entry_bp.doc(
    security=[{"BearerAuth": []}],
    summary="Get all bills of entry",
    description="List all bills of entry with optional filtering by project_id and bill_of_entry_no.",
)
@bill_of_entry_bp.arguments(BillOfEntryQuerySchema, location="query")
@bill_of_entry_bp.response(200, BillOfEntryResponseSchema(many=True))
@jwt_required()
def list_bills_of_entry(args=None):
    return _handle_list_bills_of_entry(args)




@bill_of_entry_bp.patch("/<int:bill_of_entry_id>")
@bill_of_entry_bp.doc(
    security=[{"BearerAuth": []}],
    summary="Update bill of entry record",
    requestBody=_REQUEST_BODY_UPDATE_DOC,
)
@bill_of_entry_bp.response(200, BillOfEntryResponseSchema)
@jwt_required()
def update_bill_of_entry(bill_of_entry_id: int):
    return _handle_update_bill_of_entry(bill_of_entry_id)


@bill_of_entry_bp.delete("/<int:bill_of_entry_id>")
@bill_of_entry_bp.doc(
    security=[{"BearerAuth": []}],
    summary="Delete bill of entry record",
)
@jwt_required()
def delete_bill_of_entry(bill_of_entry_id: int):
    return _handle_delete_bill_of_entry(bill_of_entry_id)

