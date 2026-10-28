import json
from datetime import datetime

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.models import (
    BidDocumentLte,
    BidDocumentLteItem,
    BidDocumentTechnoCommercial,
    BidDocumentTechnoCommercialItem,
    Project,
    ProjectStep,
    TechnoCommercialTender,
    TechnoCommercialTenderItem,
)
from app.schemas.phase1 import (
    BidDocumentLteCreateSchema,
    BidDocumentLteUpdateSchema,
    BidDocumentTechnoCommercialCreateSchema,
    BidDocumentTechnoCommercialUpdateSchema,
    TechnoCommercialTenderCreateSchema,
    TechnoCommercialTenderUpdateSchema,
)
from app.services.attachment_service import (
    create_attachment,
    delete_attachment,
    list_attachments,
)
from app.utils.remark_utils import get_step_remarks_for_response

# =========================================================================
# BLUEPRINTS DEFINITIONS
# =========================================================================
# 1. Bid Document Techno-Commercial
bid_document_techno_commercial_bp = Blueprint(
    "bid_document_techno_commercial",
    __name__,
    url_prefix="/api/v1/bid-document-techno-commercial",
    description="Bid Document Techno-Commercial APIs",
)

bid_document_techno_commercial_plural_bp = Blueprint(
    "bid_document_techno_commercial_plural",
    __name__,
    url_prefix="/api/v1/bid-document-techno-commercials",
    description="Bid Document Techno-Commercials APIs (Plural)",
)

# 2. Techno-Commercial Tender
techno_commercial_tender_bp = Blueprint(
    "techno_commercial_tenders",
    __name__,
    url_prefix="/api/v1/techno-commercial-tenders",
    description="Techno-Commercial Tenders APIs",
)

techno_commercial_tender_singular_bp = Blueprint(
    "techno_commercial_tender_singular",
    __name__,
    url_prefix="/api/v1/techno-commercial-tender",
    description="Techno-Commercial Tender APIs (Singular)",
)

# 3. Bid Document LTE
bid_document_lte_bp = Blueprint(
    "bid_document_lte",
    __name__,
    url_prefix="/api/v1/bid-document-lte",
    description="Bid Document LTE APIs",
)

bid_document_lte_plural_bp = Blueprint(
    "bid_document_lte_plural",
    __name__,
    url_prefix="/api/v1/bid-document-ltes",
    description="Bid Document LTE APIs (Plural)",
)


EXTRA_BLUEPRINTS = [
    bid_document_techno_commercial_bp,
    bid_document_techno_commercial_plural_bp,
    techno_commercial_tender_bp,
    techno_commercial_tender_singular_bp,
    bid_document_lte_bp,
    bid_document_lte_plural_bp,
]


# =========================================================================
# COMMON HELPERS
# =========================================================================
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

        for key in ("file", "files", "attachments", "upload_bid_document", "upload_tender_document"):
            if key in request.files:
                files.extend(request.files.getlist(key))
    else:
        raw_payload = request.get_json(silent=True) or {}

    return raw_payload, files


def _get_user_id():
    try:
        identity = get_jwt_identity()
        return int(identity) if identity is not None else 1
    except (TypeError, ValueError):
        return 1


def _save_attachments(files, entity_type: str, entity_id: int, user_id: int):
    for f in files:
        if not f or not getattr(f, "filename", None):
            continue
        try:
            create_attachment(
                file=f,
                entity_type=entity_type,
                entity_id=entity_id,
                uploaded_by=user_id,
            )
        except Exception as e:
            current_app.logger.warning(f"Error saving attachment: {e}")


def _serialize_attachments(entity_type: str, entity_id: int):
    try:
        atts = list_attachments(entity_type=entity_type, entity_id=entity_id)
        return [
            {
                "id": a.id,
                "file_name": a.file_name,
                "filename": a.file_name,
                "file_url": f"/api/v1/attachments/{a.id}/download",
                "content_type": a.content_type,
                "file_size": a.file_size,
                "uploaded_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in atts
        ]
    except Exception:
        return []


def _save_remarks(project_id: int, step_number: int, entity_id: int, remarks_data, user_id: int):
    if not remarks_data:
        return
    from app.services.step_remark_service import sync_step_remarks
    if isinstance(remarks_data, str) and remarks_data.strip():
        remarks_list = [{"remark": remarks_data.strip(), "user_id": user_id}]
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
            current_app.logger.warning(f"Error saving remarks: {e}")


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
            s_data.update(data_dict)
            s_data["_is_attached"] = True
            s_data["_synced_from_record"] = True
            step.data = s_data
            db.session.commit()
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning(f"Failed to sync step {form_code} for project {project_id}: {exc}")


def _error(code: str, message: str, status_code: int = 400):
    return make_response(jsonify({"success": False, "error": {"code": code, "message": message}}), status_code)


# =========================================================================
# 1. FORM_29_BID_DOC_TECHNO_COMMERCIAL
# =========================================================================
def _serialize_bid_doc_techno_commercial(rec):
    atts = _serialize_attachments("bid_document_techno_commercial", rec.id)
    remarks = get_step_remarks_for_response(
        rec.project_id,
        29,
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
            "unit_price": float(it.unit_price) if it.unit_price is not None else None,
            "total_amount": float(it.total_amount) if it.total_amount is not None else None,
        }
        for it in (rec.items or [])
    ]
    return {
        "id": rec.id,
        "project_id": rec.project_id,
        "customer_name": rec.customer_name,
        "tender_title": rec.tender_title,
        "tender_no": rec.tender_no,
        "tender_number": rec.tender_no,
        "tender_issue_date": rec.tender_issue_date.isoformat() if rec.tender_issue_date else None,
        "total_no_corrigendum_issued": rec.total_no_corrigendum_issued,
        "total_corrigendum_issued": rec.total_no_corrigendum_issued,
        "bid_submission_date": rec.bid_submission_date.isoformat() if rec.bid_submission_date else None,
        "delivery_terms": rec.delivery_terms,
        "delivery_term": rec.delivery_terms,
        "delivery_period": rec.delivery_period,
        "bid_validity": rec.bid_validity,
        "payment_terms": rec.payment_terms,
        "warranty_period": rec.warranty_period,
        "gst_pct": float(rec.gst_pct) if rec.gst_pct is not None else None,
        "gst_rate": float(rec.gst_pct) if rec.gst_pct is not None else None,
        "remark": rec.remark,
        "remarks": remarks,
        "items": items,
        "attachments": atts,
        "attachments_count": len(atts),
        "status": rec.status or "completed",
        "form_code": "FORM_29_BID_DOC_TECHNO_COMMERCIAL",
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


def handle_create_bid_doc_techno_commercial():
    user_id = _get_user_id()
    try:
        raw_payload, files = _extract_payload_and_files()
        data = BidDocumentTechnoCommercialCreateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    project = db.session.get(Project, data["project_id"])
    if not project:
        return _error("PROJECT_NOT_FOUND", f"Project {data['project_id']} not found.", 404)

    items_data = data.pop("items", None) or []
    remarks_data = data.pop("remarks", None) or data.get("remark")
    status_val = data.pop("status", None) or raw_payload.get("status") or "completed"
    data.pop("attachments_count", None)
    data.pop("form_code", None)

    # Normalize aliases
    if "tender_number" in data and not data.get("tender_no"):
        data["tender_no"] = data.pop("tender_number")
    else:
        data.pop("tender_number", None)

    if "total_corrigendum_issued" in data and data.get("total_no_corrigendum_issued") is None:
        data["total_no_corrigendum_issued"] = data.pop("total_corrigendum_issued")
    else:
        data.pop("total_corrigendum_issued", None)

    if "gst_rate" in data and data.get("gst_pct") is None:
        data["gst_pct"] = data.pop("gst_rate")
    else:
        data.pop("gst_rate", None)

    rec = BidDocumentTechnoCommercial(**{k: v for k, v in data.items() if hasattr(BidDocumentTechnoCommercial, k)})
    rec.status = status_val

    for it in items_data:
        rec.items.append(BidDocumentTechnoCommercialItem(
            sr_no=it.get("sr_no"),
            description=it.get("description", ""),
            material_name=it.get("material_name") or it.get("description", ""),
            hsn_sac=it.get("hsn_sac"),
            quantity=it.get("quantity"),
            unit_price=it.get("unit_price"),
            total_amount=it.get("total_amount") or ((float(it.get("unit_price") or 0) * float(it.get("quantity") or 0)) if it.get("unit_price") and it.get("quantity") else None),
        ))

    db.session.add(rec)
    db.session.flush()

    _save_attachments(files, "bid_document_techno_commercial", rec.id, user_id)
    _save_remarks(rec.project_id, 29, rec.id, remarks_data, user_id)
    db.session.commit()

    serialized = _serialize_bid_doc_techno_commercial(rec)
    _sync_step(rec.project_id, "FORM_29_BID_DOC_TECHNO_COMMERCIAL", status_val, serialized)
    return jsonify(serialized), 201


def handle_get_bid_doc_techno_commercial(rec_id=None):
    if rec_id is not None:
        rec = db.session.get(BidDocumentTechnoCommercial, rec_id)
        if not rec:
            return _error("NOT_FOUND", f"BidDocumentTechnoCommercial {rec_id} not found.", 404)
        return jsonify(_serialize_bid_doc_techno_commercial(rec)), 200

    project_id = request.args.get("project_id", type=int)
    q = BidDocumentTechnoCommercial.query
    if project_id:
        q = q.filter_by(project_id=project_id)
    records = q.order_by(BidDocumentTechnoCommercial.id.desc()).all()
    return jsonify([_serialize_bid_doc_techno_commercial(r) for r in records]), 200


def handle_update_bid_doc_techno_commercial(rec_id: int):
    user_id = _get_user_id()
    rec = db.session.get(BidDocumentTechnoCommercial, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"BidDocumentTechnoCommercial {rec_id} not found.", 404)

    try:
        raw_payload, files = _extract_payload_and_files()
        data = BidDocumentTechnoCommercialUpdateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    items_data = data.pop("items", None) if "items" in data else None
    remarks_data = data.pop("remarks", None) if "remarks" in data else data.get("remark")
    status_val = data.pop("status", None) or raw_payload.get("status")
    data.pop("attachments_count", None)
    data.pop("form_code", None)

    if "tender_number" in data and not data.get("tender_no"):
        data["tender_no"] = data.pop("tender_number")
    else:
        data.pop("tender_number", None)

    if "total_corrigendum_issued" in data and data.get("total_no_corrigendum_issued") is None:
        data["total_no_corrigendum_issued"] = data.pop("total_corrigendum_issued")
    else:
        data.pop("total_corrigendum_issued", None)

    if "gst_rate" in data and data.get("gst_pct") is None:
        data["gst_pct"] = data.pop("gst_rate")
    else:
        data.pop("gst_rate", None)

    for k, v in data.items():
        if hasattr(rec, k):
            setattr(rec, k, v)
    if status_val:
        rec.status = status_val

    if items_data is not None:
        rec.items.clear()
        for it in items_data:
            rec.items.append(BidDocumentTechnoCommercialItem(
                sr_no=it.get("sr_no"),
                description=it.get("description", ""),
                material_name=it.get("material_name") or it.get("description", ""),
                hsn_sac=it.get("hsn_sac"),
                quantity=it.get("quantity"),
                unit_price=it.get("unit_price"),
                total_amount=it.get("total_amount") or ((float(it.get("unit_price") or 0) * float(it.get("quantity") or 0)) if it.get("unit_price") and it.get("quantity") else None),
            ))

    _save_attachments(files, "bid_document_techno_commercial", rec.id, user_id)
    _save_remarks(rec.project_id, 29, rec.id, remarks_data, user_id)
    db.session.commit()

    serialized = _serialize_bid_doc_techno_commercial(rec)
    _sync_step(rec.project_id, "FORM_29_BID_DOC_TECHNO_COMMERCIAL", rec.status, serialized)
    return jsonify(serialized), 200


def handle_delete_bid_doc_techno_commercial(rec_id: int):
    rec = db.session.get(BidDocumentTechnoCommercial, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"BidDocumentTechnoCommercial {rec_id} not found.", 404)
    project_id = rec.project_id
    atts = list_attachments(entity_type="bid_document_techno_commercial", entity_id=rec_id)
    for a in atts:
        try:
            delete_attachment(a.id)
        except Exception:
            pass
    db.session.delete(rec)
    db.session.commit()

    from app.routes.project_step import sync_project_steps_from_records
    proj = db.session.get(Project, project_id)
    if proj:
        sync_project_steps_from_records(proj)
    return jsonify({"success": True, "message": "Bid Document Techno-Commercial deleted successfully."}), 200


# Wire routes to blueprints
for bp in (bid_document_techno_commercial_bp, bid_document_techno_commercial_plural_bp):
    bp.route("", methods=["GET"])(jwt_required()(handle_get_bid_doc_techno_commercial))
    bp.route("/<int:rec_id>", methods=["GET"])(jwt_required()(handle_get_bid_doc_techno_commercial))
    bp.route("", methods=["POST"])(jwt_required()(handle_create_bid_doc_techno_commercial))
    bp.route("/<int:rec_id>", methods=["PATCH", "PUT"])(jwt_required()(handle_update_bid_doc_techno_commercial))
    bp.route("/<int:rec_id>", methods=["DELETE"])(jwt_required()(handle_delete_bid_doc_techno_commercial))


# =========================================================================
# 2. FORM_30_TECHNO_COMMERCIAL_TENDER
# =========================================================================
def _serialize_techno_commercial_tender(rec):
    atts = _serialize_attachments("techno_commercial_tender", rec.id)
    remarks = get_step_remarks_for_response(
        rec.project_id,
        30,
        fallback_raw=rec.remark,
        entity_id=rec.id,
    )
    items = [
        {
            "id": it.id,
            "sr_no": it.sr_no,
            "description": it.description,
            "material_name": it.material_name or it.description,
            "unit": it.unit,
            "quantity": float(it.quantity) if it.quantity is not None else None,
        }
        for it in (rec.items or [])
    ]
    return {
        "id": rec.id,
        "project_id": rec.project_id,
        "pqb_no": rec.pqb_no,
        "tender_title": rec.tender_title,
        "tender_no": rec.tender_no,
        "tender_number": rec.tender_no,
        "tender_enquiry_no": rec.tender_no,
        "tender_issue_date": rec.tender_issue_date.isoformat() if rec.tender_issue_date else None,
        "bid_submission_due_date_time": rec.bid_submission_due_date_time.isoformat() if rec.bid_submission_due_date_time else None,
        "bid_opening_date_time": rec.bid_opening_date_time.isoformat() if rec.bid_opening_date_time else None,
        "tender_fee": float(rec.tender_fee) if rec.tender_fee is not None else None,
        "emd": float(rec.emd) if rec.emd is not None else None,
        "tender_validity": rec.tender_validity,
        "remark": rec.remark,
        "remarks": remarks,
        "items": items,
        "attachments": atts,
        "attachments_count": len(atts),
        "status": rec.status or "completed",
        "form_code": "FORM_30_TECHNO_COMMERCIAL_TENDER",
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


def handle_create_techno_commercial_tender():
    user_id = _get_user_id()
    try:
        raw_payload, files = _extract_payload_and_files()
        data = TechnoCommercialTenderCreateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    project = db.session.get(Project, data["project_id"])
    if not project:
        return _error("PROJECT_NOT_FOUND", f"Project {data['project_id']} not found.", 404)

    items_data = data.pop("items", None) or []
    remarks_data = data.pop("remarks", None) or data.get("remark")
    status_val = data.pop("status", None) or raw_payload.get("status") or "completed"
    data.pop("attachments_count", None)
    data.pop("form_code", None)

    if "tender_number" in data and not data.get("tender_no"):
        data["tender_no"] = data.pop("tender_number")
    elif "tender_enquiry_no" in data and not data.get("tender_no"):
        data["tender_no"] = data.pop("tender_enquiry_no")
    else:
        data.pop("tender_number", None)
        data.pop("tender_enquiry_no", None)

    rec = TechnoCommercialTender(**{k: v for k, v in data.items() if hasattr(TechnoCommercialTender, k)})
    rec.status = status_val

    for it in items_data:
        rec.items.append(TechnoCommercialTenderItem(
            sr_no=it.get("sr_no"),
            description=it.get("description", ""),
            material_name=it.get("material_name") or it.get("description", ""),
            unit=it.get("unit"),
            quantity=it.get("quantity"),
        ))

    db.session.add(rec)
    db.session.flush()

    _save_attachments(files, "techno_commercial_tender", rec.id, user_id)
    _save_remarks(rec.project_id, 30, rec.id, remarks_data, user_id)
    db.session.commit()

    serialized = _serialize_techno_commercial_tender(rec)
    _sync_step(rec.project_id, "FORM_30_TECHNO_COMMERCIAL_TENDER", status_val, serialized)
    return jsonify(serialized), 201


def handle_get_techno_commercial_tender(rec_id=None):
    if rec_id is not None:
        rec = db.session.get(TechnoCommercialTender, rec_id)
        if not rec:
            return _error("NOT_FOUND", f"TechnoCommercialTender {rec_id} not found.", 404)
        return jsonify(_serialize_techno_commercial_tender(rec)), 200

    project_id = request.args.get("project_id", type=int)
    q = TechnoCommercialTender.query
    if project_id:
        q = q.filter_by(project_id=project_id)
    records = q.order_by(TechnoCommercialTender.id.desc()).all()
    return jsonify([_serialize_techno_commercial_tender(r) for r in records]), 200


def handle_update_techno_commercial_tender(rec_id: int):
    user_id = _get_user_id()
    rec = db.session.get(TechnoCommercialTender, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"TechnoCommercialTender {rec_id} not found.", 404)

    try:
        raw_payload, files = _extract_payload_and_files()
        data = TechnoCommercialTenderUpdateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    items_data = data.pop("items", None) if "items" in data else None
    remarks_data = data.pop("remarks", None) if "remarks" in data else data.get("remark")
    status_val = data.pop("status", None) or raw_payload.get("status")
    data.pop("attachments_count", None)
    data.pop("form_code", None)

    if "tender_number" in data and not data.get("tender_no"):
        data["tender_no"] = data.pop("tender_number")
    elif "tender_enquiry_no" in data and not data.get("tender_no"):
        data["tender_no"] = data.pop("tender_enquiry_no")
    else:
        data.pop("tender_number", None)
        data.pop("tender_enquiry_no", None)

    for k, v in data.items():
        if hasattr(rec, k):
            setattr(rec, k, v)
    if status_val:
        rec.status = status_val

    if items_data is not None:
        rec.items.clear()
        for it in items_data:
            rec.items.append(TechnoCommercialTenderItem(
                sr_no=it.get("sr_no"),
                description=it.get("description", ""),
                material_name=it.get("material_name") or it.get("description", ""),
                unit=it.get("unit"),
                quantity=it.get("quantity"),
            ))

    _save_attachments(files, "techno_commercial_tender", rec.id, user_id)
    _save_remarks(rec.project_id, 30, rec.id, remarks_data, user_id)
    db.session.commit()

    serialized = _serialize_techno_commercial_tender(rec)
    _sync_step(rec.project_id, "FORM_30_TECHNO_COMMERCIAL_TENDER", rec.status, serialized)
    return jsonify(serialized), 200


def handle_delete_techno_commercial_tender(rec_id: int):
    rec = db.session.get(TechnoCommercialTender, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"TechnoCommercialTender {rec_id} not found.", 404)
    project_id = rec.project_id
    atts = list_attachments(entity_type="techno_commercial_tender", entity_id=rec_id)
    for a in atts:
        try:
            delete_attachment(a.id)
        except Exception:
            pass
    db.session.delete(rec)
    db.session.commit()

    from app.routes.project_step import sync_project_steps_from_records
    proj = db.session.get(Project, project_id)
    if proj:
        sync_project_steps_from_records(proj)
    return jsonify({"success": True, "message": "Techno-Commercial Tender deleted successfully."}), 200


# Wire routes to blueprints
for bp in (techno_commercial_tender_bp, techno_commercial_tender_singular_bp):
    bp.route("", methods=["GET"])(jwt_required()(handle_get_techno_commercial_tender))
    bp.route("/<int:rec_id>", methods=["GET"])(jwt_required()(handle_get_techno_commercial_tender))
    bp.route("", methods=["POST"])(jwt_required()(handle_create_techno_commercial_tender))
    bp.route("/<int:rec_id>", methods=["PATCH", "PUT"])(jwt_required()(handle_update_techno_commercial_tender))
    bp.route("/<int:rec_id>", methods=["DELETE"])(jwt_required()(handle_delete_techno_commercial_tender))


# =========================================================================
# 3. FORM_31_BID_DOC_LTE
# =========================================================================
def _serialize_bid_doc_lte(rec):
    atts = _serialize_attachments("bid_document_lte", rec.id)
    remarks = get_step_remarks_for_response(
        rec.project_id,
        31,
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
            "unit_price": float(it.unit_price) if it.unit_price is not None else None,
            "total_amount": float(it.total_amount) if it.total_amount is not None else None,
        }
        for it in (rec.items or [])
    ]
    return {
        "id": rec.id,
        "project_id": rec.project_id,
        "customer_name": rec.customer_name,
        "tender_title": rec.tender_title,
        "tender_no": rec.tender_no,
        "tender_number": rec.tender_no,
        "tender_issue_date": rec.tender_issue_date.isoformat() if rec.tender_issue_date else None,
        "total_no_corrigendum_issued": rec.total_no_corrigendum_issued,
        "total_corrigendum_issued": rec.total_no_corrigendum_issued,
        "bid_submission_date": rec.bid_submission_date.isoformat() if rec.bid_submission_date else None,
        "delivery_terms": rec.delivery_terms,
        "delivery_term": rec.delivery_terms,
        "delivery_period": rec.delivery_period,
        "bid_validity": rec.bid_validity,
        "payment_terms": rec.payment_terms,
        "warranty_period": rec.warranty_period,
        "gst_pct": float(rec.gst_pct) if rec.gst_pct is not None else None,
        "gst_rate": float(rec.gst_pct) if rec.gst_pct is not None else None,
        "remark": rec.remark,
        "remarks": remarks,
        "items": items,
        "attachments": atts,
        "attachments_count": len(atts),
        "status": rec.status or "completed",
        "form_code": "FORM_31_BID_DOC_LTE",
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


def handle_create_bid_doc_lte():
    user_id = _get_user_id()
    try:
        raw_payload, files = _extract_payload_and_files()
        data = BidDocumentLteCreateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    project = db.session.get(Project, data["project_id"])
    if not project:
        return _error("PROJECT_NOT_FOUND", f"Project {data['project_id']} not found.", 404)

    items_data = data.pop("items", None) or []
    remarks_data = data.pop("remarks", None) or data.get("remark")
    status_val = data.pop("status", None) or raw_payload.get("status") or "completed"
    data.pop("attachments_count", None)
    data.pop("form_code", None)

    if "tender_number" in data and not data.get("tender_no"):
        data["tender_no"] = data.pop("tender_number")
    else:
        data.pop("tender_number", None)

    if "total_corrigendum_issued" in data and data.get("total_no_corrigendum_issued") is None:
        data["total_no_corrigendum_issued"] = data.pop("total_corrigendum_issued")
    else:
        data.pop("total_corrigendum_issued", None)

    if "gst_rate" in data and data.get("gst_pct") is None:
        data["gst_pct"] = data.pop("gst_rate")
    else:
        data.pop("gst_rate", None)

    rec = BidDocumentLte(**{k: v for k, v in data.items() if hasattr(BidDocumentLte, k)})
    rec.status = status_val

    for it in items_data:
        rec.items.append(BidDocumentLteItem(
            sr_no=it.get("sr_no"),
            description=it.get("description", ""),
            material_name=it.get("material_name") or it.get("description", ""),
            hsn_sac=it.get("hsn_sac"),
            quantity=it.get("quantity"),
            unit_price=it.get("unit_price"),
            total_amount=it.get("total_amount") or ((float(it.get("unit_price") or 0) * float(it.get("quantity") or 0)) if it.get("unit_price") and it.get("quantity") else None),
        ))

    db.session.add(rec)
    db.session.flush()

    _save_attachments(files, "bid_document_lte", rec.id, user_id)
    _save_remarks(rec.project_id, 31, rec.id, remarks_data, user_id)
    db.session.commit()

    serialized = _serialize_bid_doc_lte(rec)
    _sync_step(rec.project_id, "FORM_31_BID_DOC_LTE", status_val, serialized)
    return jsonify(serialized), 201


def handle_get_bid_doc_lte(rec_id=None):
    if rec_id is not None:
        rec = db.session.get(BidDocumentLte, rec_id)
        if not rec:
            return _error("NOT_FOUND", f"BidDocumentLte {rec_id} not found.", 404)
        return jsonify(_serialize_bid_doc_lte(rec)), 200

    project_id = request.args.get("project_id", type=int)
    q = BidDocumentLte.query
    if project_id:
        q = q.filter_by(project_id=project_id)
    records = q.order_by(BidDocumentLte.id.desc()).all()
    return jsonify([_serialize_bid_doc_lte(r) for r in records]), 200


def handle_update_bid_doc_lte(rec_id: int):
    user_id = _get_user_id()
    rec = db.session.get(BidDocumentLte, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"BidDocumentLte {rec_id} not found.", 404)

    try:
        raw_payload, files = _extract_payload_and_files()
        data = BidDocumentLteUpdateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    items_data = data.pop("items", None) if "items" in data else None
    remarks_data = data.pop("remarks", None) if "remarks" in data else data.get("remark")
    status_val = data.pop("status", None) or raw_payload.get("status")
    data.pop("attachments_count", None)
    data.pop("form_code", None)

    if "tender_number" in data and not data.get("tender_no"):
        data["tender_no"] = data.pop("tender_number")
    else:
        data.pop("tender_number", None)

    if "total_corrigendum_issued" in data and data.get("total_no_corrigendum_issued") is None:
        data["total_no_corrigendum_issued"] = data.pop("total_corrigendum_issued")
    else:
        data.pop("total_corrigendum_issued", None)

    if "gst_rate" in data and data.get("gst_pct") is None:
        data["gst_pct"] = data.pop("gst_rate")
    else:
        data.pop("gst_rate", None)

    for k, v in data.items():
        if hasattr(rec, k):
            setattr(rec, k, v)
    if status_val:
        rec.status = status_val

    if items_data is not None:
        rec.items.clear()
        for it in items_data:
            rec.items.append(BidDocumentLteItem(
                sr_no=it.get("sr_no"),
                description=it.get("description", ""),
                material_name=it.get("material_name") or it.get("description", ""),
                hsn_sac=it.get("hsn_sac"),
                quantity=it.get("quantity"),
                unit_price=it.get("unit_price"),
                total_amount=it.get("total_amount") or ((float(it.get("unit_price") or 0) * float(it.get("quantity") or 0)) if it.get("unit_price") and it.get("quantity") else None),
            ))

    _save_attachments(files, "bid_document_lte", rec.id, user_id)
    _save_remarks(rec.project_id, 31, rec.id, remarks_data, user_id)
    db.session.commit()

    serialized = _serialize_bid_doc_lte(rec)
    _sync_step(rec.project_id, "FORM_31_BID_DOC_LTE", rec.status, serialized)
    return jsonify(serialized), 200


def handle_delete_bid_doc_lte(rec_id: int):
    rec = db.session.get(BidDocumentLte, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"BidDocumentLte {rec_id} not found.", 404)
    project_id = rec.project_id
    atts = list_attachments(entity_type="bid_document_lte", entity_id=rec_id)
    for a in atts:
        try:
            delete_attachment(a.id)
        except Exception:
            pass
    db.session.delete(rec)
    db.session.commit()

    from app.routes.project_step import sync_project_steps_from_records
    proj = db.session.get(Project, project_id)
    if proj:
        sync_project_steps_from_records(proj)
    return jsonify({"success": True, "message": "Bid Document LTE deleted successfully."}), 200


# Wire routes to blueprints
for bp in (bid_document_lte_bp, bid_document_lte_plural_bp):
    bp.route("", methods=["GET"])(jwt_required()(handle_get_bid_doc_lte))
    bp.route("/<int:rec_id>", methods=["GET"])(jwt_required()(handle_get_bid_doc_lte))
    bp.route("", methods=["POST"])(jwt_required()(handle_create_bid_doc_lte))
    bp.route("/<int:rec_id>", methods=["PATCH", "PUT"])(jwt_required()(handle_update_bid_doc_lte))
    bp.route("/<int:rec_id>", methods=["DELETE"])(jwt_required()(handle_delete_bid_doc_lte))
