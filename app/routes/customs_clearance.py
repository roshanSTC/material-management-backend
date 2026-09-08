import json

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.schemas.customs_clearance import (
    CustomsClearanceCreateSchema,
    CustomsClearanceQuerySchema,
    CustomsClearanceResponseSchema,
    CustomsClearanceUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    list_attachments,
)
from app.services.customs_clearance_service import (
    CustomsClearanceNotFoundError,
    ProjectNotFoundError,
    create_customs_clearance_transaction,
    delete_customs_clearance_transaction,
    get_customs_clearance_record,
    list_customs_clearances_records,
    update_customs_clearance_transaction,
)
from app.services.storage.factory import get_storage

customs_clearance_bp = Blueprint(
    "customs_clearances",
    __name__,
    url_prefix="/api/v1/customs-clearances",
    description="Customs Clearance APIs",
)


def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _customs_clearance_response(record):
    attachments = list_attachments(
        entity_type="customs_clearance",
        entity_id=record.id,
    )

    return {
        "id": record.id,
        "project_id": record.project_id,
        "bill_of_entry_id": record.bill_of_entry_id,
        "cha_name": record.cha_name,
        "bill_of_entry_no": record.bill_of_entry_no,
        "bill_of_entry_number": record.bill_of_entry_no,
        "boe_date": record.boe_date,
        "customs_location": record.customs_location,
        "customs_location_port": record.customs_location,
        "duty_paid_date": record.duty_paid_date,
        "challan_no": record.challan_no,
        "challan_number": record.challan_no,
        "cfs_name": record.cfs_name,
        "transaction_ref_no": record.transaction_ref_no,
        "transaction_payment_reference": record.transaction_ref_no,
        "duty_amount": record.duty_amount,
        "igst_amount": record.igst_amount,
        "other_customs_charges": record.other_customs_charges,
        "total_customs_amount": record.total_customs_amount,
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

    known_file_keys = (
        "duty_challan_file",
        "boe_file",
        "other_docs_file",
    )

    if "multipart/form-data" in content_type:
        data_raw = request.form.get("data")
        if data_raw:
            try:
                raw_payload = json.loads(data_raw)
            except (json.JSONDecodeError, TypeError) as exc:
                raise ValidationError(f"Invalid JSON in form data: {exc}")
        else:
            raw_payload = request.form.to_dict()

        for key in known_file_keys:
            if key in request.files:
                for f in request.files.getlist(key):
                    if f and getattr(f, "filename", None):
                        files.append(f)
    else:
        data_raw = request.form.get("data")
        if data_raw:
            try:
                raw_payload = json.loads(data_raw)
            except (json.JSONDecodeError, TypeError) as exc:
                raise ValidationError(f"Invalid JSON in form data: {exc}")
        else:
            raw_payload = request.get_json(silent=True) or request.form.to_dict() or {}

        for key in known_file_keys:
            if key in request.files:
                for f in request.files.getlist(key):
                    if f and getattr(f, "filename", None):
                        files.append(f)

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


def _handle_create_customs_clearance():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = CustomsClearanceCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        record = create_customs_clearance_transaction(data=validated_data)

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="customs_clearance",
                entity_id=record.id,
                uploaded_by=user_id,
            )
            storage_keys.append(storage_key)

        db.session.commit()
        return _customs_clearance_response(record), 201

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
        current_app.logger.exception("Failed to create customs clearance")
        return _error(
            "CUSTOMS_CLEARANCE_CREATE_FAILED",
            "Failed to create customs clearance.",
            500,
        )


def _handle_list_customs_clearances(args=None):
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

    challan_no = (
        args.get("challan_no")
        or request.args.get("challan_no")
        or request.args.get("challanNo")
    )

    try:
        records = list_customs_clearances_records(
            project_id=project_id,
            bill_of_entry_no=bill_of_entry_no,
            challan_no=challan_no,
        )
        return [_customs_clearance_response(rec) for rec in records], 200
    except Exception:
        current_app.logger.exception("Failed to list customs clearances")
        return _error(
            "CUSTOMS_CLEARANCE_LIST_FAILED",
            "Failed to list customs clearances.",
            500,
        )


def _handle_get_customs_clearance(clearance_id: int):
    try:
        record = get_customs_clearance_record(clearance_id)
        return _customs_clearance_response(record), 200
    except CustomsClearanceNotFoundError as exc:
        return _error("CUSTOMS_CLEARANCE_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get customs clearance")
        return _error(
            "CUSTOMS_CLEARANCE_GET_FAILED",
            "Failed to get customs clearance.",
            500,
        )


def _handle_update_customs_clearance(clearance_id: int):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = CustomsClearanceUpdateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        record = update_customs_clearance_transaction(
            clearance_id=clearance_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="customs_clearance",
                entity_id=record.id,
                uploaded_by=user_id,
            )
            storage_keys.append(storage_key)

        db.session.commit()
        return _customs_clearance_response(record), 200

    except CustomsClearanceNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("CUSTOMS_CLEARANCE_NOT_FOUND", str(exc), 404)
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
        current_app.logger.exception("Failed to update customs clearance")
        return _error(
            "CUSTOMS_CLEARANCE_UPDATE_FAILED",
            "Failed to update customs clearance.",
            500,
        )


def _handle_delete_customs_clearance(clearance_id: int):
    try:
        storage_keys = delete_customs_clearance_transaction(clearance_id)
        db.session.commit()

        storage = get_storage()
        for key in storage_keys:
            try:
                if storage.exists(key):
                    storage.delete(key)
            except Exception:
                current_app.logger.warning(
                    f"Failed to delete attachment storage key {key} during customs clearance deletion."
                )

        return {
            "success": True,
            "message": "Customs clearance deleted successfully.",
        }, 200

    except CustomsClearanceNotFoundError as exc:
        db.session.rollback()
        return _error("CUSTOMS_CLEARANCE_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete customs clearance")
        return _error(
            "CUSTOMS_CLEARANCE_DELETE_FAILED",
            "Failed to delete customs clearance.",
            500,
        )


_REQUEST_BODY_CREATE_DOC = {
    "required": True,
    "description": "Form data containing serialized JSON payload in 'data' field and document attachments.",
    "content": {
        "multipart/form-data": {
            "schema": {
                "type": "object",
                "required": ["data"],
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Serialized JSON string matching CustomsClearanceCreateSchema",
                        "example": '{"project_id":1,"cha_name":"DHL global","bill_of_entry_no":"BOE-34G56-RG","boe_date":"2026-09-09","customs_location":"MUMBAI","duty_paid_date":"2026-09-02","challan_no":"ICDE-CHAKR45-R5","cfs_name":"gateway ","transaction_ref_no":"DHF7456HG56","duty_amount":5445,"igst_amount":8745,"other_customs_charges":546,"total_customs_amount":14736,"remark":"Total Customs Amount (Duty + IGST + Other Charges)"}',
                    },
                    "duty_challan_file": {
                        "type": "string",
                        "format": "binary",
                        "description": "Duty challan document file",
                    },
                    "boe_file": {
                        "type": "string",
                        "format": "binary",
                        "description": "Bill of Entry document file",
                    },
                    "other_docs_file": {
                        "type": "string",
                        "format": "binary",
                        "description": "Other customs clearance document file",
                    },
                },
            },
        },
        "application/json": {
            "schema": CustomsClearanceCreateSchema,
            "examples": {
                "default": {
                    "summary": "Customs Clearance Payload",
                    "value": {
                        "project_id": 1,
                        "cha_name": "DHL global",
                        "bill_of_entry_no": "BOE-34G56-RG",
                        "boe_date": "2026-09-09",
                        "customs_location": "MUMBAI",
                        "duty_paid_date": "2026-09-02",
                        "challan_no": "ICDE-CHAKR45-R5",
                        "cfs_name": "gateway ",
                        "transaction_ref_no": "DHF7456HG56",
                        "duty_amount": 5445,
                        "igst_amount": 8745,
                        "other_customs_charges": 546,
                        "total_customs_amount": 14736,
                        "remark": "Total Customs Amount (Duty + IGST + Other Charges)",
                    },
                },
            },
        },
    },
}

_REQUEST_BODY_UPDATE_DOC = {
    "required": False,
    "description": "Form data or JSON to update customs clearance record.",
    "content": {
        "multipart/form-data": {
            "schema": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Serialized JSON string matching CustomsClearanceUpdateSchema",
                        "example": '{"cha_name":"DHL Global Forwarding","duty_paid_date":"2026-09-03","total_customs_amount":15000}',
                    },
                    "duty_challan_file": {
                        "type": "string",
                        "format": "binary",
                        "description": "New duty challan document file",
                    },
                    "boe_file": {
                        "type": "string",
                        "format": "binary",
                        "description": "New Bill of Entry document file",
                    },
                    "other_docs_file": {
                        "type": "string",
                        "format": "binary",
                        "description": "New other customs clearance document file",
                    },
                },
            },
        },
        "application/json": {
            "schema": CustomsClearanceUpdateSchema,
        },
    },
}


@customs_clearance_bp.route("", methods=["POST"])
@customs_clearance_bp.doc(
    summary="Create Customs Clearance",
    description="Create a new Customs Clearance record with optional attachments.",
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_CREATE_DOC,
)
@customs_clearance_bp.response(201, CustomsClearanceResponseSchema)
@jwt_required()
def create_customs_clearance_route():
    return _handle_create_customs_clearance()


@customs_clearance_bp.route("", methods=["GET"])
@customs_clearance_bp.doc(
    summary="List Customs Clearances",
    description="Retrieve all customs clearance records with optional filters.",
    security=[{"BearerAuth": []}],
)
@customs_clearance_bp.arguments(CustomsClearanceQuerySchema, location="query")
@customs_clearance_bp.response(200, CustomsClearanceResponseSchema(many=True))
@jwt_required()
def list_customs_clearances_route(args=None):
    return _handle_list_customs_clearances(args)



@customs_clearance_bp.route("/<int:clearance_id>", methods=["PATCH"])
@customs_clearance_bp.doc(
    summary="Update Customs Clearance",
    description="Update an existing customs clearance record and optionally upload new attachments.",
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_UPDATE_DOC,
)
@customs_clearance_bp.response(200, CustomsClearanceResponseSchema)
@jwt_required()
def update_customs_clearance_route(clearance_id: int):
    return _handle_update_customs_clearance(clearance_id)


@customs_clearance_bp.route("/<int:clearance_id>", methods=["DELETE"])
@customs_clearance_bp.doc(
    summary="Delete Customs Clearance",
    description="Delete a customs clearance record and its associated document attachments.",
    security=[{"BearerAuth": []}],
)
@jwt_required()
def delete_customs_clearance_route(clearance_id: int):
    return _handle_delete_customs_clearance(clearance_id)
