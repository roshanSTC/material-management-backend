import json

from flask import current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from app.extensions.database import db
from app.schemas.supplier_quotation import (
    SupplierQuotationCreateSchema,
    SupplierQuotationResponseSchema,
    SupplierQuotationUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    list_attachments,
)
from app.services.storage.factory import get_storage
from app.services.supplier_quotation_service import (
    ProjectNotFoundError,
    SupplierNotFoundError,
    SupplierProjectMismatchError,
    SupplierQuotationNotFoundError,
    create_supplier_quotation_transaction,
    get_supplier_quotation_record,
    list_supplier_quotation_records,
    update_supplier_quotation_transaction,
)


supplier_quotation_bp = Blueprint(
    "supplier_quotations",
    __name__,
    url_prefix="/api/v1/supplier-quotations",
    description="Supplier Quotation APIs",
)


def _supplier_quotation_response(supplier_quotation):
    attachments = list_attachments(
        entity_type="supplier_quotation",
        entity_id=supplier_quotation.id,
    )
    return {
        "id": supplier_quotation.id,
        "project_id": supplier_quotation.project_id,
        "supplier_id": supplier_quotation.supplier_id,
        "quotation_number": supplier_quotation.quotation_number,
        "quotation_date": supplier_quotation.quotation_date,
        "quotation_value": supplier_quotation.quotation_value,
        "validity": supplier_quotation.validity,
        "incoterms": supplier_quotation.incoterms,
        "payment_terms": supplier_quotation.payment_terms,
        "delivery_period": supplier_quotation.delivery_period,
        "remark": supplier_quotation.remark,
        "created_at": supplier_quotation.created_at,
        "updated_at": supplier_quotation.updated_at,
        "items": [
            {
                "id": item.id,
                "material_name": item.material_name,
                "quantity": item.quantity,
            }
            for item in supplier_quotation.items
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
                "updated_at": attachment.updated_at,
            }
            for attachment in attachments
        ],
    }


def _parse_form_data(schema):
    data_raw = request.form.get("data")
    if not data_raw:
        return None, _error("DATA_REQUIRED", "data is required.", 422)
    try:
        data = json.loads(data_raw)
    except json.JSONDecodeError:
        return None, _error("INVALID_DATA", "data must contain valid JSON.", 422)

    try:
        return schema.load(data), None
    except Exception as exc:
        return None, _error("VALIDATION_ERROR", str(exc), 422)


def _error(code: str, message: str, status: int):
    return {"success": False, "error": {"code": code, "message": message}}, status


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


def _attach_files(
    *,
    supplier_quotation_id: int,
    uploaded_by: int,
    storage_keys: list[str],
) -> None:
    for file in request.files.getlist("file"):
        if not file or not file.filename:
            continue
        _, storage_key = create_attachment(
            file=file,
            entity_type="supplier_quotation",
            entity_id=supplier_quotation_id,
            uploaded_by=uploaded_by,
        )
        storage_keys.append(storage_key)


def _positive_query_int(name: str):
    value = request.args.get(name)
    if value is None:
        return None, None
    try:
        parsed_value = int(value)
    except ValueError:
        return None, _error("VALIDATION_ERROR", f"{name} must be an integer.", 422)
    if parsed_value < 1:
        return None, _error("VALIDATION_ERROR", f"{name} must be positive.", 422)
    return parsed_value, None


@supplier_quotation_bp.post("")
@supplier_quotation_bp.doc(
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
                            "example": ('{"project_id":1,"supplier_id":1,"quotation_number":"SQ-2026-00891","quotation_date":"2026-09-02","quotation_value":"15000.00","validity":"60 Days","incoterms":"FOB","payment_terms":"50% Advance, 50% against Delivery","delivery_period":"5 Weeks","remark":"Prices include standard 1-year operational warranty.","items":[{"material_name":"High-Pressure Hydraulic Valve","quantity":10},{"material_name":"Stainless Steel Connecting Pipe","quantity":50}]}'),
                        },
                        "file": {
                            "type": "array",
                            "items": {"type": "string", "format": "binary"},
                        },
                    },
                },
            },
        },
    },
)
# @supplier_quotation_bp.response(201, SupplierQuotationResponseSchema)
@jwt_required()
def create():
    data, error = _parse_form_data(SupplierQuotationCreateSchema())
    if error:
        return error

    storage_keys = []
    try:
        supplier_quotation = create_supplier_quotation_transaction(data=data)
        _attach_files(
            supplier_quotation_id=supplier_quotation.id,
            uploaded_by=int(get_jwt_identity()),
            storage_keys=storage_keys,
        )
        db.session.commit()
        return _supplier_quotation_response(supplier_quotation), 201
    except (ProjectNotFoundError, SupplierNotFoundError) as exc:
        db.session.rollback()
        code = "PROJECT_NOT_FOUND" if isinstance(exc, ProjectNotFoundError) else "SUPPLIER_NOT_FOUND"
        return _error(code, str(exc), 404)
    except SupplierProjectMismatchError as exc:
        db.session.rollback()
        return _error("SUPPLIER_PROJECT_MISMATCH", str(exc), 409)
    except AttachmentValidationError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("INVALID_ATTACHMENT", str(exc), 422)
    except Exception:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        current_app.logger.exception("Supplier quotation creation failed")
        return _error(
            "SUPPLIER_QUOTATION_CREATE_FAILED",
            "Unable to create supplier quotation.",
            500,
        )


@supplier_quotation_bp.get("")
@supplier_quotation_bp.doc(security=[{"BearerAuth": []}])
@supplier_quotation_bp.response(200, SupplierQuotationResponseSchema(many=True))
@jwt_required()
def list_all():
    project_id, error = _positive_query_int("project_id")
    if error:
        return error
    supplier_id, error = _positive_query_int("supplier_id")
    if error:
        return error

    supplier_quotations = list_supplier_quotation_records(
        project_id=project_id,
        supplier_id=supplier_id,
    )
    return [
        _supplier_quotation_response(supplier_quotation)
        for supplier_quotation in supplier_quotations
    ], 200


# @supplier_quotation_bp.get("/<int:supplier_quotation_id>")
# @supplier_quotation_bp.doc(security=[{"BearerAuth": []}])
# # @supplier_quotation_bp.response(200, SupplierQuotationResponseSchema)
# @jwt_required()
# def get(supplier_quotation_id):
#     try:
#         supplier_quotation = get_supplier_quotation_record(supplier_quotation_id)
#     except SupplierQuotationNotFoundError as exc:
#         return _error("SUPPLIER_QUOTATION_NOT_FOUND", str(exc), 404)
#     return _supplier_quotation_response(supplier_quotation), 200


@supplier_quotation_bp.patch("/<int:supplier_quotation_id>")
@supplier_quotation_bp.doc(
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
                            "example": ('{"project_id":1,"supplier_id":1,"quotation_number":"SQ-2026-00891","quotation_date":"2026-09-02","quotation_value":"15000.00","validity":"60 Days","incoterms":"FOB","payment_terms":"50% Advance, 50% against Delivery","delivery_period":"5 Weeks","remark":"Prices include standard 1-year operational warranty.","items":[{"material_name":"High-Pressure Hydraulic Valve","quantity":10},{"material_name":"Stainless Steel Connecting Pipe","quantity":50}]}'),
                        },
                        "file": {
                            "type": "array",
                            "items": {"type": "string", "format": "binary"},
                        },
                    },
                },
            },
        },
    },
)
@supplier_quotation_bp.response(200, SupplierQuotationResponseSchema)
@jwt_required()
def update(supplier_quotation_id):
    data, error = _parse_form_data(SupplierQuotationUpdateSchema())
    if error:
        return error

    storage_keys = []
    try:
        supplier_quotation = update_supplier_quotation_transaction(
            supplier_quotation_id=supplier_quotation_id,
            data=data,
        )
        _attach_files(
            supplier_quotation_id=supplier_quotation.id,
            uploaded_by=int(get_jwt_identity()),
            storage_keys=storage_keys,
        )
        db.session.commit()
        return _supplier_quotation_response(supplier_quotation), 200
    except SupplierQuotationNotFoundError as exc:
        db.session.rollback()
        return _error("SUPPLIER_QUOTATION_NOT_FOUND", str(exc), 404)
    except (ProjectNotFoundError, SupplierNotFoundError) as exc:
        db.session.rollback()
        code = "PROJECT_NOT_FOUND" if isinstance(exc, ProjectNotFoundError) else "SUPPLIER_NOT_FOUND"
        return _error(code, str(exc), 404)
    except SupplierProjectMismatchError as exc:
        db.session.rollback()
        return _error("SUPPLIER_PROJECT_MISMATCH", str(exc), 409)
    except AttachmentValidationError as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        return _error("INVALID_ATTACHMENT", str(exc), 422)
    except Exception:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        current_app.logger.exception("Supplier quotation update failed")
        return _error(
            "SUPPLIER_QUOTATION_UPDATE_FAILED",
            "Unable to update supplier quotation.",
            500,
        )
