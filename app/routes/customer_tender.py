import json

from flask import current_app, jsonify, make_response, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.models import Attachment
from app.schemas.customer_tender import (
    CustomerTenderCreateSchema,
    CustomerTenderQuerySchema,
    CustomerTenderResponseSchema,
    CustomerTenderUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    delete_attachment,
    list_attachments,
)
from app.services.customer_tender_service import (
    CustomerNotFoundError,
    CustomerProjectMismatchError,
    CustomerTenderNotFoundError,
    ProjectNotFoundError,
    create_customer_tender_transaction,
    delete_customer_tender_transaction,
    get_customer_tender_record,
    list_customer_tender_records,
    update_customer_tender_transaction,
)
from app.services.storage.factory import get_storage

customer_tender_bp = Blueprint(
    "customer_tenders",
    __name__,
    url_prefix="/api/v1/customer-tenders",
    description="Customer Tender APIs",
)


def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _customer_tender_response(customer_tender):
    attachments = list_attachments(
        entity_type="customer_tender",
        entity_id=customer_tender.id,
    )
    return {
        "id": customer_tender.id,
        "project_id": customer_tender.project_id,
        "customer_id": customer_tender.customer_id,
        "officer_name": customer_tender.officer_name,
        "company_business_name": customer_tender.officer_name,
        "email": customer_tender.email,
        "address": customer_tender.address,
        "website": customer_tender.website,
        "contact_number": customer_tender.contact_number,
        "tender_title": customer_tender.tender_title,
        "tender_number": customer_tender.tender_number,
        "tender_date": customer_tender.tender_date,
        "opening_date_time": customer_tender.opening_date_time,
        "closing_date_time": customer_tender.closing_date_time,
        "tender_fee": customer_tender.tender_fee,
        "validity": customer_tender.validity,
        "delivery_terms": customer_tender.delivery_terms,
        "incoterms": customer_tender.delivery_terms,
        "delivery_period": customer_tender.delivery_period,
        "payment_terms": customer_tender.payment_terms,
        "warranty_period": customer_tender.warranty_period,
        "remark": customer_tender.remark,
        "created_at": customer_tender.created_at,
        "updated_at": customer_tender.updated_at,
        "items": [
            {
                "id": item.id,
                "customer_tender_id": item.customer_tender_id,
                "item_code": item.item_code,
                "description": item.description,
                "material_name": item.description,
                "quantity": item.quantity,
                "created_at": item.created_at,
            }
            for item in customer_tender.items
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


@customer_tender_bp.post("")
@customer_tender_bp.doc(
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
                            "description": "Serialized JSON string matching CustomerTenderCreateSchema",
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
                "schema": CustomerTenderCreateSchema,
            },
        },
    },
)
@customer_tender_bp.response(201, CustomerTenderResponseSchema)
@jwt_required()
def create_customer_tender():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = CustomerTenderCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    try:
        customer_tender = create_customer_tender_transaction(data=validated_data)

        # Handle file attachments safely
        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            create_attachment(
                file=file,
                entity_type="customer_tender",
                entity_id=customer_tender.id,
                uploaded_by=user_id,
            )

        db.session.commit()
        return _customer_tender_response(customer_tender), 201

    except ProjectNotFoundError as exc:
        db.session.rollback()
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except CustomerNotFoundError as exc:
        db.session.rollback()
        return _error("CUSTOMER_NOT_FOUND", str(exc), 404)
    except CustomerProjectMismatchError as exc:
        db.session.rollback()
        return _error("CUSTOMER_PROJECT_MISMATCH", str(exc), 400)
    except AttachmentValidationError as exc:
        db.session.rollback()
        return _error("ATTACHMENT_VALIDATION_ERROR", str(exc), 400)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to create customer tender")
        return _error("CUSTOMER_TENDER_CREATE_FAILED", "Failed to create customer tender.", 500)


@customer_tender_bp.get("")
@customer_tender_bp.doc(security=[{"BearerAuth": []}])
@customer_tender_bp.arguments(CustomerTenderQuerySchema, location="query")
@customer_tender_bp.response(200, CustomerTenderResponseSchema(many=True))
@jwt_required()
def list_customer_tenders(args=None):
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
        tenders = list_customer_tender_records(
            project_id=project_id,
        )
        return [_customer_tender_response(ct) for ct in tenders], 200
    except Exception:
        current_app.logger.exception("Failed to list customer tenders")
        return _error("CUSTOMER_TENDER_LIST_FAILED", "Failed to list customer tenders.", 500)


@customer_tender_bp.patch("/<int:customer_tender_id>")
@customer_tender_bp.doc(
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
                            "description": "Serialized JSON string matching CustomerTenderUpdateSchema",
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
                "schema": CustomerTenderUpdateSchema,
            },
        },
    },
)
@customer_tender_bp.response(200, CustomerTenderResponseSchema)
@jwt_required()
def update_customer_tender(customer_tender_id):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = CustomerTenderUpdateSchema()
        validated_data = schema.load(raw_payload) if raw_payload else {}
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    try:
        customer_tender = update_customer_tender_transaction(
            customer_tender_id=customer_tender_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            create_attachment(
                file=file,
                entity_type="customer_tender",
                entity_id=customer_tender.id,
                uploaded_by=user_id,
            )

        db.session.commit()
        return _customer_tender_response(customer_tender), 200

    except CustomerTenderNotFoundError as exc:
        db.session.rollback()
        return _error("CUSTOMER_TENDER_NOT_FOUND", str(exc), 404)
    except ProjectNotFoundError as exc:
        db.session.rollback()
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except CustomerNotFoundError as exc:
        db.session.rollback()
        return _error("CUSTOMER_NOT_FOUND", str(exc), 404)
    except CustomerProjectMismatchError as exc:
        db.session.rollback()
        return _error("CUSTOMER_PROJECT_MISMATCH", str(exc), 400)
    except AttachmentValidationError as exc:
        db.session.rollback()
        return _error("ATTACHMENT_VALIDATION_ERROR", str(exc), 400)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to update customer tender")
        return _error("CUSTOMER_TENDER_UPDATE_FAILED", "Failed to update customer tender.", 500)


@customer_tender_bp.delete("/<int:customer_tender_id>")
@customer_tender_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_customer_tender(customer_tender_id):
    try:
        storage_keys = delete_customer_tender_transaction(customer_tender_id)
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

        return jsonify({"success": True, "message": "Customer tender deleted successfully."}), 200
    except CustomerTenderNotFoundError as exc:
        db.session.rollback()
        return _error("CUSTOMER_TENDER_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete customer tender")
        return _error("CUSTOMER_TENDER_DELETE_FAILED", "Failed to delete customer tender.", 500)







