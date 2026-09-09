import json

from flask import current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.models import TransportDetail
from app.schemas.transport_detail import (
    TransportDetailCreateSchema,
    TransportDetailQuerySchema,
    TransportDetailResponseSchema,
    TransportDetailUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
)
from app.services.storage.factory import get_storage
from app.services.transport_detail_service import (
    ProjectNotFoundError,
    TransportDetailNotFoundError,
    create_transport_detail_transaction,
    delete_transport_detail_transaction,
    get_transport_detail_record,
    list_transport_detail_records,
    update_transport_detail_transaction,
)

transport_detail_bp = Blueprint(
    "transport_details",
    __name__,
    url_prefix="/api/v1/transport-details",
    description="Operations on transport details",
)


def _error(code: str, message: str, status_code: int):
    return (
        jsonify(
            {
                "success": False,
                "code": code,
                "message": message,
                "error": {"code": code, "message": message},
            }
        ),
        status_code,
    )


def _transport_detail_response(detail: TransportDetail) -> dict:
    from app.models import Attachment

    attachments = (
        Attachment.query.filter_by(
            entity_type="transport_detail",
            entity_id=detail.id,
        )
        .order_by(Attachment.id.asc())
        .all()
    )

    return {
        "id": detail.id,
        "project_id": detail.project_id,
        "transport_mode": detail.transport_mode,
        "transportation_mode": detail.transport_mode,
        "date": detail.date,
        "transport_date": detail.date,
        "from_location": detail.from_location,
        "to_location": detail.to_location,
        "lr_no": detail.lr_no,
        "lr_number": detail.lr_no,
        "rr_no": detail.rr_no,
        "awb_no": detail.awb_no,
        "transport_charges": detail.transport_charges,
        "remark": detail.remark,
        "remarks": detail.remark,
        "created_at": detail.created_at,
        "updated_at": detail.updated_at,
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


def _handle_create_transport_detail():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = TransportDetailCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        detail = create_transport_detail_transaction(data=validated_data)

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="transport_detail",
                entity_id=detail.id,
                uploaded_by=user_id,
            )
            if storage_key:
                storage_keys.append(storage_key)

        db.session.commit()
        return _transport_detail_response(detail), 201
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
        current_app.logger.exception("Failed to create transport detail")
        return _error(
            "TRANSPORT_DETAIL_CREATE_FAILED",
            "Failed to create transport detail.",
            500,
        )


def _handle_list_transport_details(args=None):
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

    transport_mode = (
        args.get("transport_mode")
        or request.args.get("transport_mode")
        or request.args.get("transportMode")
        or request.args.get("transportation_mode")
    )

    lr_no = (
        args.get("lr_no")
        or request.args.get("lr_no")
        or request.args.get("lrNo")
        or request.args.get("lr_number")
    )

    try:
        details = list_transport_detail_records(
            project_id=project_id,
            transport_mode=transport_mode,
            lr_no=lr_no,
        )
        return [_transport_detail_response(d) for d in details], 200
    except Exception:
        current_app.logger.exception("Failed to list transport details")
        return _error(
            "TRANSPORT_DETAIL_LIST_FAILED",
            "Failed to list transport details.",
            500,
        )


def _handle_get_transport_detail(transport_detail_id: int):
    try:
        detail = get_transport_detail_record(transport_detail_id)
        return _transport_detail_response(detail), 200
    except TransportDetailNotFoundError as exc:
        return _error("TRANSPORT_DETAIL_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get transport detail")
        return _error(
            "TRANSPORT_DETAIL_GET_FAILED",
            "Failed to get transport detail.",
            500,
        )


def _handle_update_transport_detail(transport_detail_id: int):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = TransportDetailUpdateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        detail = update_transport_detail_transaction(
            transport_detail_id=transport_detail_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="transport_detail",
                entity_id=detail.id,
                uploaded_by=user_id,
            )
            if storage_key:
                storage_keys.append(storage_key)

        db.session.commit()
        return _transport_detail_response(detail), 200
    except TransportDetailNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("TRANSPORT_DETAIL_NOT_FOUND", str(exc), 404)
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
        current_app.logger.exception("Failed to update transport detail")
        return _error(
            "TRANSPORT_DETAIL_UPDATE_FAILED",
            "Failed to update transport detail.",
            500,
        )


def _handle_delete_transport_detail(transport_detail_id: int):
    try:
        storage_keys = delete_transport_detail_transaction(
            transport_detail_id
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
                    "message": "Transport detail deleted successfully.",
                }
            ),
            200,
        )
    except TransportDetailNotFoundError as exc:
        db.session.rollback()
        return _error("TRANSPORT_DETAIL_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete transport detail")
        return _error(
            "TRANSPORT_DETAIL_DELETE_FAILED",
            "Failed to delete transport detail.",
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
                        "description": "Serialized JSON string matching TransportDetailCreateSchema",
                        "example": (
                            '{"project_id":1,"transport_mode":"road","lr_no":"SADFDSF","date":"2026-09-09","from_location":"FDSFW","to_location":"WRDCDC","transport_charges":21}'
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
            "schema": TransportDetailCreateSchema,
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
                        "description": "Serialized JSON string matching TransportDetailUpdateSchema",
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                },
            },
        },
        "application/json": {
            "schema": TransportDetailUpdateSchema,
        },
    },
}


@transport_detail_bp.post("")
@transport_detail_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_CREATE_DOC,
)
@transport_detail_bp.response(201, TransportDetailResponseSchema)
@jwt_required()
def create_transport_detail():
    return _handle_create_transport_detail()


@transport_detail_bp.get("")
@transport_detail_bp.doc(security=[{"BearerAuth": []}])
@transport_detail_bp.arguments(
    TransportDetailQuerySchema, location="query"
)
@transport_detail_bp.response(
    200, TransportDetailResponseSchema(many=True)
)
@jwt_required()
def list_transport_details(args=None):
    return _handle_list_transport_details(args)


@transport_detail_bp.patch("/<int:transport_detail_id>")
@transport_detail_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_UPDATE_DOC,
)
@transport_detail_bp.response(200, TransportDetailResponseSchema)
@jwt_required()
def update_transport_detail(transport_detail_id):
    return _handle_update_transport_detail(transport_detail_id)


@transport_detail_bp.delete("/<int:transport_detail_id>")
@transport_detail_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_transport_detail(transport_detail_id):
    return _handle_delete_transport_detail(transport_detail_id)
