import json

from flask import current_app, jsonify, make_response, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.models import Attachment
from app.schemas.bid_submission import (
    BidSubmissionCreateSchema,
    BidSubmissionQuerySchema,
    BidSubmissionResponseSchema,
    BidSubmissionUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
    delete_attachment,
    list_attachments,
)
from app.services.bid_submission_service import (
    BidSubmissionNotFoundError,
    ProjectNotFoundError,
    TenderNotFoundError,
    create_bid_submission_transaction,
    delete_bid_submission_transaction,
    get_bid_submission_record,
    list_bid_submission_records,
    update_bid_submission_transaction,
)
from app.services.storage.factory import get_storage

bid_submission_bp = Blueprint(
    "bid_submissions",
    __name__,
    url_prefix="/api/v1/bid-submissions",
    description="Bid Submission APIs",
)


def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _bid_submission_response(bid_submission):
    attachments = list_attachments(
        entity_type="bid_submission",
        entity_id=bid_submission.id,
    )
    return {
        "id": bid_submission.id,
        "project_id": bid_submission.project_id,
        "tender_id": bid_submission.tender_id,
        "tender_title": bid_submission.tender_title,
        "tender_name": bid_submission.tender_title,
        "submission_date": bid_submission.submission_date,
        "tender_number": bid_submission.tender_number,
        "submission_number": bid_submission.tender_number,
        "delivery_term": bid_submission.delivery_term,
        "delivery_terms": bid_submission.delivery_term,
        "period": bid_submission.period,
        "payment_term": bid_submission.payment_term,
        "payment_terms": bid_submission.payment_term,
        "validity": bid_submission.validity,
        "warranty_period": bid_submission.warranty_period,
        "gst_rate": bid_submission.gst_rate,
        "remark": bid_submission.remark,
        "created_at": bid_submission.created_at,
        "updated_at": bid_submission.updated_at,
        "items": [
            {
                "id": item.id,
                "bid_submission_id": item.bid_submission_id,
                "description": item.description,
                "material_name": item.description,
                "hsn_sac": item.hsn_sac,
                "unit_price": item.unit_price,
                "quantity": item.quantity,
                "net_total": item.net_total,
                "net_amount": item.net_total,
                "total": item.total,
                "total_amount": item.total,
                "created_at": item.created_at,
            }
            for item in bid_submission.items
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


@bid_submission_bp.post("")
@bid_submission_bp.doc(
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
                            "description": "Serialized JSON string matching BidSubmissionCreateSchema",
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
                "schema": BidSubmissionCreateSchema,
            },
        },
    },
)
@bid_submission_bp.response(201, BidSubmissionResponseSchema)
@jwt_required()
def create_bid_submission():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = BidSubmissionCreateSchema()
        validated_data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    try:
        bid_submission = create_bid_submission_transaction(data=validated_data)

        # Handle file attachments safely
        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            create_attachment(
                file=file,
                entity_type="bid_submission",
                entity_id=bid_submission.id,
                uploaded_by=user_id,
            )

        db.session.commit()
        return _bid_submission_response(bid_submission), 201

    except ProjectNotFoundError as exc:
        db.session.rollback()
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except TenderNotFoundError as exc:
        db.session.rollback()
        return _error("TENDER_NOT_FOUND", str(exc), 404)
    except AttachmentValidationError as exc:
        db.session.rollback()
        return _error("ATTACHMENT_VALIDATION_ERROR", str(exc), 400)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to create bid submission")
        return _error("BID_SUBMISSION_CREATE_FAILED", "Failed to create bid submission.", 500)


@bid_submission_bp.get("")
@bid_submission_bp.doc(security=[{"BearerAuth": []}])
@bid_submission_bp.arguments(BidSubmissionQuerySchema, location="query")
@bid_submission_bp.response(200, BidSubmissionResponseSchema(many=True))
@jwt_required()
def list_bid_submissions(args=None):
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
        submissions = list_bid_submission_records(
            project_id=project_id,
        )
        return [_bid_submission_response(bs) for bs in submissions], 200
    except Exception:
        current_app.logger.exception("Failed to list bid submissions")
        return _error("BID_SUBMISSION_LIST_FAILED", "Failed to list bid submissions.", 500)





@bid_submission_bp.patch("/<int:bid_submission_id>")
@bid_submission_bp.doc(
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
                            "description": "Serialized JSON string matching BidSubmissionUpdateSchema",
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
                "schema": BidSubmissionUpdateSchema,
            },
        },
    },
)
@bid_submission_bp.response(200, BidSubmissionResponseSchema)
@jwt_required()
def update_bid_submission(bid_submission_id):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("UNAUTHORIZED", "Invalid user token.", 401)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = BidSubmissionUpdateSchema()
        validated_data = schema.load(raw_payload) if raw_payload else {}
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    try:
        bid_submission = update_bid_submission_transaction(
            bid_submission_id=bid_submission_id,
            data=validated_data,
        )

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            create_attachment(
                file=file,
                entity_type="bid_submission",
                entity_id=bid_submission.id,
                uploaded_by=user_id,
            )

        db.session.commit()
        return _bid_submission_response(bid_submission), 200

    except BidSubmissionNotFoundError as exc:
        db.session.rollback()
        return _error("BID_SUBMISSION_NOT_FOUND", str(exc), 404)
    except ProjectNotFoundError as exc:
        db.session.rollback()
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except TenderNotFoundError as exc:
        db.session.rollback()
        return _error("TENDER_NOT_FOUND", str(exc), 404)
    except AttachmentValidationError as exc:
        db.session.rollback()
        return _error("ATTACHMENT_VALIDATION_ERROR", str(exc), 400)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to update bid submission")
        return _error("BID_SUBMISSION_UPDATE_FAILED", "Failed to update bid submission.", 500)


@bid_submission_bp.delete("/<int:bid_submission_id>")
@bid_submission_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_bid_submission(bid_submission_id):
    try:
        storage_keys = delete_bid_submission_transaction(bid_submission_id)
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

        return jsonify({"success": True, "message": "Bid submission deleted successfully."}), 200
    except BidSubmissionNotFoundError as exc:
        db.session.rollback()
        return _error("BID_SUBMISSION_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete bid submission")
        return _error("BID_SUBMISSION_DELETE_FAILED", "Failed to delete bid submission.", 500)


