import json

from flask import current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.models import WarrantyCertificate
from app.schemas.warranty_certificate import (
    WarrantyCertificateCreateSchema,
    WarrantyCertificateQuerySchema,
    WarrantyCertificateResponseSchema,
    WarrantyCertificateUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
)
from app.services.storage.factory import get_storage
from app.services.warranty_certificate_service import (
    ProjectNotFoundError,
    WarrantyCertificateNotFoundError,
    create_warranty_certificate_transaction,
    delete_warranty_certificate_transaction,
    get_warranty_certificate_record,
    list_warranty_certificate_records,
    update_warranty_certificate_transaction,
)

warranty_certificate_bp = Blueprint(
    "warranty_certificates",
    __name__,
    url_prefix="/api/v1/warranty-certificates",
    description="Operations on warranty certificates",
)


def _error(code: str, message: str, status_code: int):
    return jsonify({"code": code, "message": message}), status_code


def _warranty_certificate_response(cert: WarrantyCertificate) -> dict:
    from app.models import Attachment

    attachments = (
        Attachment.query.filter_by(
            entity_type="warranty_certificate",
            entity_id=cert.id,
        )
        .order_by(Attachment.id.asc())
        .all()
    )

    return {
        "id": cert.id,
        "project_id": cert.project_id,
        "certificate_date": cert.certificate_date,
        "warranty_period": cert.warranty_period,
        "po_no": cert.po_no,
        "po_number": cert.po_no,
        "po_date": cert.po_date,
        "invoice_no": cert.invoice_no,
        "invoice_number": cert.invoice_no,
        "invoice_date": cert.invoice_date,
        "remark": cert.remark,
        "remarks": cert.remark,
        "created_at": cert.created_at,
        "updated_at": cert.updated_at,
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


def _handle_create_warranty_certificate():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = WarrantyCertificateCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        cert = create_warranty_certificate_transaction(data=validated_data)

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="warranty_certificate",
                entity_id=cert.id,
                uploaded_by=user_id,
            )
            if storage_key:
                storage_keys.append(storage_key)

        db.session.commit()
        return _warranty_certificate_response(cert), 201
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
        current_app.logger.exception("Failed to create warranty certificate")
        return _error(
            "WARRANTY_CERTIFICATE_CREATE_FAILED",
            "Failed to create warranty certificate.",
            500,
        )


def _handle_list_warranty_certificates(args=None):
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

    po_no = (
        args.get("po_no")
        or request.args.get("po_no")
        or request.args.get("poNo")
        or request.args.get("po_number")
    )

    invoice_no = (
        args.get("invoice_no")
        or request.args.get("invoice_no")
        or request.args.get("invoiceNo")
        or request.args.get("invoice_number")
    )

    try:
        certs = list_warranty_certificate_records(
            project_id=project_id,
            po_no=po_no,
            invoice_no=invoice_no,
        )
        return [_warranty_certificate_response(c) for c in certs], 200
    except Exception:
        current_app.logger.exception("Failed to list warranty certificates")
        return _error(
            "WARRANTY_CERTIFICATE_LIST_FAILED",
            "Failed to list warranty certificates.",
            500,
        )


def _handle_get_warranty_certificate(warranty_certificate_id: int):
    try:
        cert = get_warranty_certificate_record(warranty_certificate_id)
        return _warranty_certificate_response(cert), 200
    except WarrantyCertificateNotFoundError as exc:
        return _error("WARRANTY_CERTIFICATE_NOT_FOUND", str(exc), 404)
    except Exception:
        current_app.logger.exception("Failed to get warranty certificate")
        return _error(
            "WARRANTY_CERTIFICATE_GET_FAILED",
            "Failed to get warranty certificate.",
            500,
        )


def _handle_update_warranty_certificate(warranty_certificate_id: int):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = WarrantyCertificateUpdateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    storage_keys = []
    try:
        cert = update_warranty_certificate_transaction(
            warranty_certificate_id=warranty_certificate_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            _, storage_key = create_attachment(
                file=file,
                entity_type="warranty_certificate",
                entity_id=cert.id,
                uploaded_by=user_id,
            )
            if storage_key:
                storage_keys.append(storage_key)

        db.session.commit()
        return _warranty_certificate_response(cert), 200
    except WarrantyCertificateNotFoundError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("WARRANTY_CERTIFICATE_NOT_FOUND", str(exc), 404)
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
        current_app.logger.exception("Failed to update warranty certificate")
        return _error(
            "WARRANTY_CERTIFICATE_UPDATE_FAILED",
            "Failed to update warranty certificate.",
            500,
        )


def _handle_delete_warranty_certificate(warranty_certificate_id: int):
    try:
        storage_keys = delete_warranty_certificate_transaction(
            warranty_certificate_id
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
                    "message": "Warranty certificate deleted successfully.",
                }
            ),
            200,
        )
    except WarrantyCertificateNotFoundError as exc:
        db.session.rollback()
        return _error("WARRANTY_CERTIFICATE_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete warranty certificate")
        return _error(
            "WARRANTY_CERTIFICATE_DELETE_FAILED",
            "Failed to delete warranty certificate.",
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
                        "description": "Serialized JSON string matching WarrantyCertificateCreateSchema",
                        "example": (
                            '{"project_id":2,"certificate_date":"2026-09-09","warranty_period":"3 months","po_no":"162837","po_date":"2026-09-15","invoice_no":"237r98ufh","invoice_date":"2026-09-15","remark":"http://127.0.0.1:5000/api/v1/delivery-challans"}'
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
            "schema": WarrantyCertificateCreateSchema,
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
                        "description": "Serialized JSON string matching WarrantyCertificateUpdateSchema",
                    },
                    "file": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                },
            },
        },
        "application/json": {
            "schema": WarrantyCertificateUpdateSchema,
        },
    },
}


@warranty_certificate_bp.post("")
@warranty_certificate_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_CREATE_DOC,
)
@warranty_certificate_bp.response(201, WarrantyCertificateResponseSchema)
@jwt_required()
def create_warranty_certificate():
    return _handle_create_warranty_certificate()


@warranty_certificate_bp.get("")
@warranty_certificate_bp.doc(security=[{"BearerAuth": []}])
@warranty_certificate_bp.arguments(
    WarrantyCertificateQuerySchema, location="query"
)
@warranty_certificate_bp.response(
    200, WarrantyCertificateResponseSchema(many=True)
)
@jwt_required()
def list_warranty_certificates(args=None):
    return _handle_list_warranty_certificates(args)


@warranty_certificate_bp.patch("/<int:warranty_certificate_id>")
@warranty_certificate_bp.doc(
    security=[{"BearerAuth": []}],
    requestBody=_REQUEST_BODY_UPDATE_DOC,
)
@warranty_certificate_bp.response(200, WarrantyCertificateResponseSchema)
@jwt_required()
def update_warranty_certificate(warranty_certificate_id):
    return _handle_update_warranty_certificate(warranty_certificate_id)


@warranty_certificate_bp.delete("/<int:warranty_certificate_id>")
@warranty_certificate_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_warranty_certificate(warranty_certificate_id):
    return _handle_delete_warranty_certificate(warranty_certificate_id)
