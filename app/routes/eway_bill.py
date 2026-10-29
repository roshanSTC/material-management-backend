from datetime import datetime
import json

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.models import Project, ProjectStep
from app.models.eway_bill import EWayBill
from app.repositories.eway_bill_repository import (
    create_eway_bill,
    delete_eway_bill,
    get_eway_bill,
    list_eway_bills,
    update_eway_bill,
)
from app.schemas.eway_bill import (
    EWayBillCreateSchema,
    EWayBillQuerySchema,
    EWayBillResponseSchema,
    EWayBillUpdateSchema,
)
from app.services.attachment_service import (
    create_attachment,
    delete_attachment,
    list_attachments,
)
from app.services.step_remark_service import sync_step_remarks
from app.services.storage.factory import get_storage
from app.utils.remark_utils import get_step_remarks_for_response

eway_bill_bp = Blueprint(
    "eway_bills",
    __name__,
    url_prefix="/api/v1/eway-bills",
    description="E-Way Bill APIs",
)


def _error(code: str, message: str, status_code: int = 400):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status_code,
    )


def _get_user_id() -> int:
    try:
        identity = get_jwt_identity()
        return int(identity) if identity is not None else 1
    except Exception:
        return 1


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

        for key in ["file", "files", "attachments"]:
            if key in request.files:
                files.extend(request.files.getlist(key))
    else:
        raw_payload = request.get_json(silent=True) or {}

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


def _serialize_attachments(entity_id: int):
    atts = list_attachments(entity_type="eway_bill", entity_id=entity_id)
    return [
        {
            "id": a.id,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "file_name": a.file_name,
            "storage_key": a.storage_key,
            "content_type": a.content_type,
            "file_size": a.file_size,
            "uploaded_by": a.uploaded_by,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in atts
    ]


def _serialize_eway_bill(rec: EWayBill) -> dict:
    atts = _serialize_attachments(rec.id)
    remarks = get_step_remarks_for_response(
        rec.project_id,
        32,
        fallback_raw=rec.remark,
        entity_id=rec.id,
    )
    items = [
        {
            "id": it.id,
            "sr_no": it.sr_no,
            "description": it.description,
            "material_name": it.material_name or it.description,
            "hsn_sac": it.hsn_sac,
            "quantity": float(it.quantity) if it.quantity is not None else None,
            "unit": it.unit or "NOS",
            "unit_price": float(it.unit_price) if it.unit_price is not None else None,
            "total_amount": float(it.total_amount) if it.total_amount is not None else None,
        }
        for it in (rec.items or [])
    ]
    return {
        "id": rec.id,
        "project_id": rec.project_id,
        "eway_bill_no": rec.eway_bill_no,
        "eway_bill_number": rec.eway_bill_no,
        "eway_bill_date": rec.eway_bill_date.isoformat() if rec.eway_bill_date else None,
        "valid_from": rec.valid_from.isoformat() if rec.valid_from else None,
        "valid_until": rec.valid_until.isoformat() if rec.valid_until else None,
        "document_no": rec.document_no,
        "document_number": rec.document_no,
        "document_date": rec.document_date.isoformat() if rec.document_date else None,
        "value": float(rec.value) if rec.value is not None else None,
        "place_of_dispatch": rec.place_of_dispatch,
        "place_of_delivery": rec.place_of_delivery,
        "transporter": rec.transporter,
        "mode": rec.mode,
        "vehicle_trans_doc_no": rec.vehicle_trans_doc_no,
        "remark": rec.remark,
        "remarks": remarks,
        "items": items,
        "attachments": atts,
        "attachments_count": len(atts),
        "status": rec.status or "completed",
        "form_code": "FORM_32_EWAY_BILL",
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


def _make_json_serializable(obj):
    from datetime import date, datetime
    from decimal import Decimal
    if obj is None:
        return None
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): _make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_json_serializable(v) for v in obj]
    return obj


def _sync_step(project_id: int, form_code: str, status: str, data_dict: dict):
    try:
        from app.routes.project_step import sync_project_steps_from_records
        project = db.session.get(Project, project_id)
        if not project:
            return
        sync_project_steps_from_records(project)
        step = ProjectStep.query.filter_by(project_id=project_id, form_code=form_code).first()
        if step:
            step.status = status or "completed"
            step.progress_percentage = 100 if step.status == "completed" else 50
            if step.status == "completed" and not step.completed_at:
                step.completed_at = datetime.utcnow()
            s_data = dict(step.data or {}) if isinstance(step.data, dict) else {}
            s_data.update(_make_json_serializable(data_dict) or {})
            s_data["_is_attached"] = True
            s_data["_synced_from_record"] = True
            step.data = s_data
            db.session.commit()
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning(f"Failed to sync step {form_code} for project {project_id}: {exc}")


def _save_attachments(files, entity_id: int, user_id: int) -> list[str]:
    storage_keys = []
    for f in files:
        if not f or not getattr(f, "filename", None):
            continue
        try:
            _, sk = create_attachment(
                file=f,
                entity_type="eway_bill",
                entity_id=entity_id,
                uploaded_by=user_id,
            )
            if sk:
                storage_keys.append(sk)
        except Exception as exc:
            current_app.logger.warning(f"Error saving attachment for eway_bill {entity_id}: {exc}")
    return storage_keys


def _save_remarks(project_id: int, step_number: int, entity_id: int, remarks_data, user_id: int):
    if not remarks_data:
        return
    if isinstance(remarks_data, str):
        remarks_list = [remarks_data]
    elif isinstance(remarks_data, list):
        remarks_list = remarks_data
    else:
        remarks_list = []
    if remarks_list:
        try:
            sync_step_remarks(
                project_id=project_id,
                step_number=step_number,
                remarks_data=remarks_list,
                default_user_id=user_id,
                entity_id=entity_id,
            )
        except Exception as e:
            current_app.logger.warning(f"Error saving remarks for eway_bill {entity_id}: {e}")


# =========================================================================
# ROUTE HANDLERS
# =========================================================================
def handle_create_eway_bill():
    user_id = _get_user_id()
    try:
        raw_payload, files = _extract_payload_and_files()
        schema = EWayBillCreateSchema()
        data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    project = db.session.get(Project, data["project_id"])
    if not project:
        return _error("PROJECT_NOT_FOUND", f"Project {data['project_id']} not found.", 404)

    remarks_data = data.get("remarks") or data.get("remark") or raw_payload.get("remarks") or raw_payload.get("remark")
    status_val = data.get("status") or raw_payload.get("status") or "completed"

    storage_keys = []
    try:
        rec = create_eway_bill(data=data)
        db.session.flush()

        storage_keys = _save_attachments(files, rec.id, user_id)
        _save_remarks(rec.project_id, 32, rec.id, remarks_data, user_id)

        db.session.commit()

        serialized = _serialize_eway_bill(rec)
        _sync_step(rec.project_id, "FORM_32_EWAY_BILL", status_val, serialized)
        return jsonify(serialized), 201
    except Exception as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        current_app.logger.exception("Failed to create eway bill")
        return _error("EWAY_BILL_CREATE_FAILED", str(exc), 500)


def handle_get_eway_bills(rec_id=None):
    if rec_id is not None:
        rec = get_eway_bill(rec_id)
        if not rec:
            return _error("NOT_FOUND", f"EWayBill {rec_id} not found.", 404)
        return jsonify(_serialize_eway_bill(rec)), 200

    project_id = request.args.get("project_id", type=int) or request.args.get("projectId", type=int)
    eway_bill_no = request.args.get("eway_bill_no") or request.args.get("eway_bill_number")
    records = list_eway_bills(project_id=project_id, eway_bill_no=eway_bill_no)
    return jsonify([_serialize_eway_bill(r) for r in records]), 200


def handle_update_eway_bill(rec_id):
    user_id = _get_user_id()
    rec = get_eway_bill(rec_id)
    if not rec:
        return _error("NOT_FOUND", f"EWayBill {rec_id} not found.", 404)

    try:
        raw_payload, files = _extract_payload_and_files()
        schema = EWayBillUpdateSchema()
        data = schema.load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", str(err.messages), 422)

    remarks_data = data.get("remarks") or data.get("remark") or raw_payload.get("remarks") or raw_payload.get("remark")
    status_val = data.get("status") or raw_payload.get("status") or rec.status or "completed"

    storage_keys = []
    try:
        update_eway_bill(rec, data=data)
        db.session.flush()

        storage_keys = _save_attachments(files, rec.id, user_id)
        if remarks_data:
            _save_remarks(rec.project_id, 32, rec.id, remarks_data, user_id)

        db.session.commit()

        serialized = _serialize_eway_bill(rec)
        _sync_step(rec.project_id, "FORM_32_EWAY_BILL", status_val, serialized)
        return jsonify(serialized), 200
    except Exception as exc:
        db.session.rollback()
        _cleanup_uploaded_files(storage_keys)
        current_app.logger.exception("Failed to update eway bill")
        return _error("EWAY_BILL_UPDATE_FAILED", str(exc), 500)


def handle_delete_eway_bill(rec_id):
    rec = get_eway_bill(rec_id)
    if not rec:
        return _error("NOT_FOUND", f"EWayBill {rec_id} not found.", 404)

    project_id = rec.project_id
    try:
        atts = list_attachments(entity_type="eway_bill", entity_id=rec.id)
        for a in atts:
            try:
                delete_attachment(a.id)
            except Exception:
                pass

        delete_eway_bill(rec)
        db.session.commit()

        # Update step if no more records exist
        remaining = list_eway_bills(project_id=project_id)
        if not remaining:
            try:
                from app.routes.project_step import sync_project_steps_from_records
                project = db.session.get(Project, project_id)
                if project:
                    sync_project_steps_from_records(project)
            except Exception:
                pass

        return jsonify({"success": True, "message": f"EWayBill {rec_id} deleted."}), 200
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Failed to delete eway bill")
        return _error("EWAY_BILL_DELETE_FAILED", str(exc), 500)


# =========================================================================
# BIND ROUTES
# =========================================================================
for bp in [eway_bill_bp]:
    bp.route("", methods=["POST"])(jwt_required()(handle_create_eway_bill))
    bp.route("", methods=["GET"])(jwt_required()(lambda: handle_get_eway_bills()))
    bp.route("/<int:rec_id>", methods=["GET"])(jwt_required()(handle_get_eway_bills))
    bp.route("/<int:rec_id>", methods=["PUT", "PATCH"])(jwt_required()(handle_update_eway_bill))
    bp.route("/<int:rec_id>", methods=["DELETE"])(jwt_required()(handle_delete_eway_bill))
