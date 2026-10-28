import json
from datetime import datetime

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.models import (
    ConsultancyInvoice,
    Corrigendum,
    ExpressionOfInterest,
    ExpressionOfInterestItem,
    LimitedTenderEnquiry,
    LimitedTenderEnquiryItem,
    NotificationAward,
    NotificationAwardItem,
    PqbBidDocument,
    PqbBidDocumentItem,
    PreQualificationBid,
    PreQualificationBidItem,
    Project,
)
from app.schemas.phase1 import (
    ConsultancyInvoiceCreateSchema,
    ConsultancyInvoiceUpdateSchema,
    CorrigendumCreateSchema,
    CorrigendumUpdateSchema,
    ExpressionOfInterestCreateSchema,
    ExpressionOfInterestUpdateSchema,
    LimitedTenderEnquiryCreateSchema,
    LimitedTenderEnquiryUpdateSchema,
    NotificationAwardCreateSchema,
    NotificationAwardUpdateSchema,
    PqbBidDocumentCreateSchema,
    PqbBidDocumentUpdateSchema,
    PreQualificationBidCreateSchema,
    PreQualificationBidUpdateSchema,
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
pre_qualification_bid_bp = Blueprint(
    "pre_qualification_bids",
    __name__,
    url_prefix="/api/v1/pre-qualification-bids",
    description="Pre-Qualification Bids APIs",
)

pqb_bid_document_bp = Blueprint(
    "pqb_bid_documents",
    __name__,
    url_prefix="/api/v1/pqb-bid-documents",
    description="PQB Bid Documents APIs",
)

pqb_bid_document_singular_bp = Blueprint(
    "pqb_bid_document_singular",
    __name__,
    url_prefix="/api/v1/pqb-bid-document",
    description="PQB Bid Document APIs (Singular)",
)

corrigendum_bp = Blueprint(
    "corrigendums",
    __name__,
    url_prefix="/api/v1/corrigendums",
    description="Corrigendums APIs",
)

limited_tender_enquiry_bp = Blueprint(
    "limited_tender_enquiries",
    __name__,
    url_prefix="/api/v1/limited-tender-enquiries",
    description="Limited Tender Enquiries APIs",
)

notification_award_bp = Blueprint(
    "notification_awards",
    __name__,
    url_prefix="/api/v1/notification-awards",
    description="Notification Awards APIs",
)

consultancy_invoice_bp = Blueprint(
    "consultancy_invoices",
    __name__,
    url_prefix="/api/v1/consultancy-invoices",
    description="Consultancy Invoices APIs",
)

expression_of_interest_bp = Blueprint(
    "expressions_of_interest",
    __name__,
    url_prefix="/api/v1/expressions-of-interest",
    description="Expressions of Interest APIs",
)

PHASE1_BLUEPRINTS = [
    pre_qualification_bid_bp,
    pqb_bid_document_bp,
    pqb_bid_document_singular_bp,
    corrigendum_bp,
    limited_tender_enquiry_bp,
    notification_award_bp,
    consultancy_invoice_bp,
    expression_of_interest_bp,
]


# =========================================================================
# HELPER FUNCTIONS
# =========================================================================
def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


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
        for k in request.files:
            if k not in ("file", "files", "attachments", "upload_bid_document", "upload_tender_document"):
                files.extend(request.files.getlist(k))
    else:
        raw_payload = request.get_json(silent=True) or {}

    return raw_payload, files


def _get_user_id():
    try:
        return int(get_jwt_identity())
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
            current_app.logger.warning(f"Error syncing remarks for step {step_number}: {e}")


def _serialize_attachments(entity_type: str, entity_id: int):
    atts = list_attachments(entity_type=entity_type, entity_id=entity_id)
    return [
        {
            "id": a.id,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "upload_key": getattr(a, "upload_key", None),
            "file_name": a.file_name,
            "filename": a.file_name,
            "file_size": a.to_dict()["file_size"] if hasattr(a, "to_dict") else a.file_size,
            "file_size_bytes": a.file_size,
            "storage_key": a.storage_key,
            "download_url": f"/api/v1/attachments/{a.id}/download",
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in atts
    ]


# =========================================================================
# 1. PRE-QUALIFICATION BID (FORM_01_PQB)
# =========================================================================
def _serialize_pqb(rec):
    return {
        "id": rec.id,
        "project_id": rec.project_id,
        "pqb_title": rec.pqb_title,
        "pqb_no": rec.pqb_no,
        "bid_number": rec.pqb_no,
        "pqb_issuing_date": rec.pqb_issuing_date.isoformat() if rec.pqb_issuing_date else None,
        "pqb_closing_date_time": rec.pqb_closing_date_time.isoformat() if rec.pqb_closing_date_time else None,
        "pqb_opening_date_time": rec.pqb_opening_date_time.isoformat() if rec.pqb_opening_date_time else None,
        "mode_of_bid_submission": rec.mode_of_bid_submission,
        "supply_location": rec.supply_location,
        "remark": rec.remark,
        "remarks": get_step_remarks_for_response(rec.project_id, 1, fallback_raw=rec.remark, entity_id=rec.id),
        "items": [
            {
                "id": it.id,
                "sr_no": it.sr_no,
                "description": it.description,
                "unit": it.unit,
                "quantity": float(it.quantity) if it.quantity is not None else None,
            }
            for it in (rec.items or [])
        ],
        "attachments": _serialize_attachments("pre_qualification_bid", rec.id),
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


@pre_qualification_bid_bp.get("")
@jwt_required()
def list_pqbs():
    project_id = request.args.get("project_id", type=int)
    query = PreQualificationBid.query
    if project_id:
        query = query.filter_by(project_id=project_id)
    records = query.order_by(PreQualificationBid.id.desc()).all()
    return jsonify([_serialize_pqb(r) for r in records]), 200


@pre_qualification_bid_bp.get("/<int:rec_id>")
@jwt_required()
def get_pqb(rec_id):
    rec = db.session.get(PreQualificationBid, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"PreQualificationBid {rec_id} not found.", 404)
    return jsonify(_serialize_pqb(rec)), 200


@pre_qualification_bid_bp.post("")
@jwt_required()
def create_pqb():
    user_id = _get_user_id()
    try:
        raw_payload, files = _extract_payload_and_files()
        data = PreQualificationBidCreateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    project = db.session.get(Project, data["project_id"])
    if not project:
        return _error("PROJECT_NOT_FOUND", f"Project {data['project_id']} not found.", 404)

    items_data = data.pop("items", None) or data.pop("requirements", None) or []
    remarks_data = data.pop("remarks", None) or data.get("remark")

    pqb_fields = {k: v for k, v in data.items() if hasattr(PreQualificationBid, k)}
    if not pqb_fields.get("pqb_no") and data.get("bid_number"):
        pqb_fields["pqb_no"] = data["bid_number"]

    rec = PreQualificationBid(**pqb_fields)
    for idx, it in enumerate(items_data, start=1):
        desc = it.get("description") or it.get("material_name") or f"Item {idx}"
        rec.items.append(PreQualificationBidItem(
            sr_no=it.get("sr_no") or idx,
            description=desc,
            unit=it.get("unit"),
            quantity=it.get("quantity"),
        ))

    db.session.add(rec)
    db.session.flush()

    _save_attachments(files, "pre_qualification_bid", rec.id, user_id)
    _save_remarks(rec.project_id, 1, rec.id, remarks_data, user_id)
    db.session.commit()
    return jsonify(_serialize_pqb(rec)), 201


@pre_qualification_bid_bp.patch("/<int:rec_id>")
@jwt_required()
def update_pqb(rec_id):
    user_id = _get_user_id()
    rec = db.session.get(PreQualificationBid, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"PreQualificationBid {rec_id} not found.", 404)

    try:
        raw_payload, files = _extract_payload_and_files()
        data = PreQualificationBidUpdateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    items_data = data.pop("items", None) if "items" in data else data.pop("requirements", None)
    remarks_data = data.pop("remarks", None) if "remarks" in data else data.get("remark")

    for k, v in data.items():
        if hasattr(rec, k):
            setattr(rec, k, v)
    if "bid_number" in data and data["bid_number"]:
        rec.pqb_no = data["bid_number"]

    if items_data is not None:
        rec.items.clear()
        for it in items_data:
            rec.items.append(PreQualificationBidItem(
                sr_no=it.get("sr_no"),
                description=it.get("description", ""),
                unit=it.get("unit"),
                quantity=it.get("quantity"),
            ))

    _save_attachments(files, "pre_qualification_bid", rec.id, user_id)
    if remarks_data is not None:
        _save_remarks(rec.project_id, 1, rec.id, remarks_data, user_id)

    rec.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_serialize_pqb(rec)), 200


@pre_qualification_bid_bp.delete("/<int:rec_id>")
@jwt_required()
def delete_pqb(rec_id):
    rec = db.session.get(PreQualificationBid, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"PreQualificationBid {rec_id} not found.", 404)
    db.session.delete(rec)
    db.session.commit()
    return jsonify({"success": True, "message": "Pre-qualification bid deleted successfully."}), 200


# =========================================================================
# 2. BID DOCUMENT FOR PQB (FORM_02_PQB_BID_DOCUMENT)
# =========================================================================
def _serialize_pqb_doc(rec):
    atts = _serialize_attachments("pqb_bid_document", rec.id)
    return {
        "id": rec.id,
        "project_id": rec.project_id,
        "pqb_title": rec.pqb_title,
        "pqb_no": rec.pqb_no,
        "pqb_issue_date": rec.pqb_issue_date.isoformat() if rec.pqb_issue_date else None,
        "pqb_closing_date_time": rec.pqb_closing_date_time.isoformat() if rec.pqb_closing_date_time else None,
        "pqb_opening_date_time": rec.pqb_opening_date_time.isoformat() if rec.pqb_opening_date_time else None,
        "total_corrigendum_issued": rec.total_corrigendum_issued,
        "total_no_corrigendum_issued": rec.total_corrigendum_issued,
        "remark": rec.remark,
        "remarks": get_step_remarks_for_response(rec.project_id, 2, fallback_raw=rec.remark, entity_id=rec.id),
        "attachments": atts,
        "attachments_count": len(atts),
        "status": getattr(rec, "status", "completed") or "completed",
        "form_code": "FORM_02_PQB_BID_DOCUMENT",
        "items": [
            {
                "id": it.id,
                "pqb_bid_document_id": it.pqb_bid_document_id,
                "sr_no": it.sr_no,
                "description": it.description,
                "material_name": it.material_name or it.description,
                "hsn_sac": it.hsn_sac,
                "quantity": float(it.quantity) if it.quantity is not None else None,
                "unit_price": float(it.unit_price) if it.unit_price is not None else None,
                "total_amount": float(it.total_amount) if it.total_amount is not None else None,
                "created_at": it.created_at.isoformat() if it.created_at else None,
                "updated_at": it.updated_at.isoformat() if it.updated_at else None,
            }
            for it in (rec.items or [])
        ],
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


def list_pqb_docs():
    project_id = request.args.get("project_id", type=int)
    query = PqbBidDocument.query
    if project_id:
        query = query.filter_by(project_id=project_id)
    records = query.order_by(PqbBidDocument.id.desc()).all()
    return jsonify([_serialize_pqb_doc(r) for r in records]), 200


def get_pqb_doc(rec_id):
    rec = db.session.get(PqbBidDocument, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"PqbBidDocument {rec_id} not found.", 404)
    return jsonify(_serialize_pqb_doc(rec)), 200


def create_pqb_doc():
    user_id = _get_user_id()
    try:
        raw_payload, files = _extract_payload_and_files()
        data = PqbBidDocumentCreateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    project = db.session.get(Project, data["project_id"])
    if not project:
        return _error("PROJECT_NOT_FOUND", f"Project {data['project_id']} not found.", 404)

    items_data = data.pop("items", None) or []
    remarks_data = data.pop("remarks", None) or data.get("remark")

    if "total_no_corrigendum_issued" in data and data["total_no_corrigendum_issued"] is not None:
        if not data.get("total_corrigendum_issued"):
            data["total_corrigendum_issued"] = data["total_no_corrigendum_issued"]

    rec = PqbBidDocument(**{k: v for k, v in data.items() if hasattr(PqbBidDocument, k)})
    for idx, it in enumerate(items_data, start=1):
        rec.items.append(PqbBidDocumentItem(
            sr_no=it.get("sr_no") or idx,
            description=it.get("description", ""),
            material_name=it.get("material_name") or it.get("description", ""),
            hsn_sac=it.get("hsn_sac"),
            quantity=it.get("quantity"),
            unit_price=it.get("unit_price"),
            total_amount=it.get("total_amount") or ((float(it.get("unit_price") or 0) * float(it.get("quantity") or 0)) if it.get("unit_price") and it.get("quantity") else None),
        ))

    db.session.add(rec)
    db.session.flush()

    _save_attachments(files, "pqb_bid_document", rec.id, user_id)
    _save_remarks(rec.project_id, 2, rec.id, remarks_data, user_id)
    db.session.commit()

    from app.routes.project_step import sync_project_steps_from_records
    sync_project_steps_from_records(project)

    return jsonify(_serialize_pqb_doc(rec)), 201


def update_pqb_doc(rec_id):
    user_id = _get_user_id()
    rec = db.session.get(PqbBidDocument, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"PqbBidDocument {rec_id} not found.", 404)

    try:
        raw_payload, files = _extract_payload_and_files()
        data = PqbBidDocumentUpdateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    remarks_data = data.pop("remarks", None) if "remarks" in data else data.get("remark")
    items_data = data.pop("items", None)

    if "total_no_corrigendum_issued" in data and data["total_no_corrigendum_issued"] is not None:
        if not data.get("total_corrigendum_issued"):
            data["total_corrigendum_issued"] = data["total_no_corrigendum_issued"]

    for k, v in data.items():
        if hasattr(rec, k):
            setattr(rec, k, v)
    if "bid_number" in data and data["bid_number"]:
        rec.pqb_no = data["bid_number"]

    if items_data is not None:
        rec.items.clear()
        for idx, it in enumerate(items_data, start=1):
            rec.items.append(PqbBidDocumentItem(
                sr_no=it.get("sr_no") or idx,
                description=it.get("description", ""),
                material_name=it.get("material_name") or it.get("description", ""),
                hsn_sac=it.get("hsn_sac"),
                quantity=it.get("quantity"),
                unit_price=it.get("unit_price"),
                total_amount=it.get("total_amount") or ((float(it.get("unit_price") or 0) * float(it.get("quantity") or 0)) if it.get("unit_price") and it.get("quantity") else None),
            ))

    _save_attachments(files, "pqb_bid_document", rec.id, user_id)
    if remarks_data is not None:
        _save_remarks(rec.project_id, 2, rec.id, remarks_data, user_id)

    rec.updated_at = datetime.utcnow()
    db.session.commit()

    from app.routes.project_step import sync_project_steps_from_records
    proj = db.session.get(Project, rec.project_id)
    if proj:
        sync_project_steps_from_records(proj)

    return jsonify(_serialize_pqb_doc(rec)), 200


def delete_pqb_doc(rec_id):
    rec = db.session.get(PqbBidDocument, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"PqbBidDocument {rec_id} not found.", 404)
    project_id = rec.project_id
    atts = list_attachments(entity_type="pqb_bid_document", entity_id=rec_id)
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

    return jsonify({"success": True, "message": "PQB Bid document deleted successfully."}), 200


for bp in (pqb_bid_document_bp, pqb_bid_document_singular_bp):
    bp.route("", methods=["GET"])(jwt_required()(list_pqb_docs))
    bp.route("/<int:rec_id>", methods=["GET"])(jwt_required()(get_pqb_doc))
    bp.route("", methods=["POST"])(jwt_required()(create_pqb_doc))
    bp.route("/<int:rec_id>", methods=["PATCH", "PUT"])(jwt_required()(update_pqb_doc))
    bp.route("/<int:rec_id>", methods=["DELETE"])(jwt_required()(delete_pqb_doc))


# =========================================================================
# 3. CORRIGENDUM (FORM_03_CORRIGENDUM)
# =========================================================================
def _serialize_corrigendum(rec):
    return {
        "id": rec.id,
        "project_id": rec.project_id,
        "corrigendum_no": rec.corrigendum_no,
        "against_tender_no": rec.against_tender_no,
        "against_ref_no": rec.against_tender_no,
        "tender_title": rec.tender_title,
        "ref_title": rec.tender_title,
        "issue_date": rec.issue_date.isoformat() if rec.issue_date else None,
        "remark": rec.remark,
        "remarks": get_step_remarks_for_response(rec.project_id, 3, fallback_raw=rec.remark, entity_id=rec.id),
        "attachments": _serialize_attachments("corrigendum", rec.id),
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


@corrigendum_bp.get("")
@jwt_required()
def list_corrigendums():
    project_id = request.args.get("project_id", type=int)
    query = Corrigendum.query
    if project_id:
        query = query.filter_by(project_id=project_id)
    records = query.order_by(Corrigendum.id.desc()).all()
    return jsonify([_serialize_corrigendum(r) for r in records]), 200


@corrigendum_bp.get("/<int:rec_id>")
@jwt_required()
def get_corrigendum(rec_id):
    rec = db.session.get(Corrigendum, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"Corrigendum {rec_id} not found.", 404)
    return jsonify(_serialize_corrigendum(rec)), 200


@corrigendum_bp.post("")
@jwt_required()
def create_corrigendum():
    user_id = _get_user_id()
    try:
        raw_payload, files = _extract_payload_and_files()
        data = CorrigendumCreateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    project = db.session.get(Project, data["project_id"])
    if not project:
        return _error("PROJECT_NOT_FOUND", f"Project {data['project_id']} not found.", 404)

    remarks_data = data.pop("remarks", None) or data.get("remark")
    rec = Corrigendum(**{k: v for k, v in data.items() if hasattr(Corrigendum, k)})
    db.session.add(rec)
    db.session.flush()

    _save_attachments(files, "corrigendum", rec.id, user_id)
    _save_remarks(rec.project_id, 3, rec.id, remarks_data, user_id)
    db.session.commit()
    return jsonify(_serialize_corrigendum(rec)), 201


@corrigendum_bp.patch("/<int:rec_id>")
@jwt_required()
def update_corrigendum(rec_id):
    user_id = _get_user_id()
    rec = db.session.get(Corrigendum, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"Corrigendum {rec_id} not found.", 404)

    try:
        raw_payload, files = _extract_payload_and_files()
        data = CorrigendumUpdateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    remarks_data = data.pop("remarks", None) if "remarks" in data else data.get("remark")
    for k, v in data.items():
        if hasattr(rec, k):
            setattr(rec, k, v)
    if "bid_number" in data and data["bid_number"]:
        rec.pqb_no = data["bid_number"]

    _save_attachments(files, "corrigendum", rec.id, user_id)
    if remarks_data is not None:
        _save_remarks(rec.project_id, 3, rec.id, remarks_data, user_id)

    rec.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_serialize_corrigendum(rec)), 200


@corrigendum_bp.delete("/<int:rec_id>")
@jwt_required()
def delete_corrigendum(rec_id):
    rec = db.session.get(Corrigendum, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"Corrigendum {rec_id} not found.", 404)
    db.session.delete(rec)
    db.session.commit()
    return jsonify({"success": True, "message": "Corrigendum deleted successfully."}), 200


# =========================================================================
# 4. LIMITED TENDER ENQUIRY (FORM_04_LTE)
# =========================================================================
def _serialize_lte(rec):
    return {
        "id": rec.id,
        "project_id": rec.project_id,
        "pqb_no": rec.pqb_no,
        "tender_title": rec.tender_title,
        "tender_enquiry_no": rec.tender_enquiry_no,
        "tender_issue_date": rec.tender_issue_date.isoformat() if rec.tender_issue_date else None,
        "bid_submission_due_date_time": rec.bid_submission_due_date_time.isoformat() if rec.bid_submission_due_date_time else None,
        "bid_opening_date_time": rec.bid_opening_date_time.isoformat() if rec.bid_opening_date_time else None,
        "tender_fee": float(rec.tender_fee) if rec.tender_fee is not None else None,
        "emd": float(rec.emd) if rec.emd is not None else None,
        "tender_validity": rec.tender_validity,
        "remark": rec.remark,
        "remarks": get_step_remarks_for_response(rec.project_id, 4, fallback_raw=rec.remark, entity_id=rec.id),
        "items": [
            {
                "id": it.id,
                "sr_no": it.sr_no,
                "description": it.description,
                "unit": it.unit,
                "quantity": float(it.quantity) if it.quantity is not None else None,
            }
            for it in (rec.items or [])
        ],
        "attachments": _serialize_attachments("limited_tender_enquiry", rec.id),
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


@limited_tender_enquiry_bp.get("")
@jwt_required()
def list_ltes():
    project_id = request.args.get("project_id", type=int)
    query = LimitedTenderEnquiry.query
    if project_id:
        query = query.filter_by(project_id=project_id)
    records = query.order_by(LimitedTenderEnquiry.id.desc()).all()
    return jsonify([_serialize_lte(r) for r in records]), 200


@limited_tender_enquiry_bp.get("/<int:rec_id>")
@jwt_required()
def get_lte(rec_id):
    rec = db.session.get(LimitedTenderEnquiry, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"LimitedTenderEnquiry {rec_id} not found.", 404)
    return jsonify(_serialize_lte(rec)), 200


@limited_tender_enquiry_bp.post("")
@jwt_required()
def create_lte():
    user_id = _get_user_id()
    try:
        raw_payload, files = _extract_payload_and_files()
        data = LimitedTenderEnquiryCreateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    project = db.session.get(Project, data["project_id"])
    if not project:
        return _error("PROJECT_NOT_FOUND", f"Project {data['project_id']} not found.", 404)

    items_data = data.pop("items", None) or data.pop("requirements", None) or []
    remarks_data = data.pop("remarks", None) or data.get("remark")

    rec = LimitedTenderEnquiry(**{k: v for k, v in data.items() if hasattr(LimitedTenderEnquiry, k)})
    for it in items_data:
        rec.items.append(LimitedTenderEnquiryItem(
            sr_no=it.get("sr_no"),
            description=it.get("description", ""),
            unit=it.get("unit"),
            quantity=it.get("quantity"),
        ))

    db.session.add(rec)
    db.session.flush()

    _save_attachments(files, "limited_tender_enquiry", rec.id, user_id)
    _save_remarks(rec.project_id, 4, rec.id, remarks_data, user_id)
    db.session.commit()
    return jsonify(_serialize_lte(rec)), 201


@limited_tender_enquiry_bp.patch("/<int:rec_id>")
@jwt_required()
def update_lte(rec_id):
    user_id = _get_user_id()
    rec = db.session.get(LimitedTenderEnquiry, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"LimitedTenderEnquiry {rec_id} not found.", 404)

    try:
        raw_payload, files = _extract_payload_and_files()
        data = LimitedTenderEnquiryUpdateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    items_data = data.pop("items", None) if "items" in data else data.pop("requirements", None)
    remarks_data = data.pop("remarks", None) if "remarks" in data else data.get("remark")

    for k, v in data.items():
        if hasattr(rec, k):
            setattr(rec, k, v)
    if "bid_number" in data and data["bid_number"]:
        rec.pqb_no = data["bid_number"]

    if items_data is not None:
        rec.items.clear()
        for it in items_data:
            rec.items.append(LimitedTenderEnquiryItem(
                sr_no=it.get("sr_no"),
                description=it.get("description", ""),
                unit=it.get("unit"),
                quantity=it.get("quantity"),
            ))

    _save_attachments(files, "limited_tender_enquiry", rec.id, user_id)
    if remarks_data is not None:
        _save_remarks(rec.project_id, 4, rec.id, remarks_data, user_id)

    rec.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_serialize_lte(rec)), 200


@limited_tender_enquiry_bp.delete("/<int:rec_id>")
@jwt_required()
def delete_lte(rec_id):
    rec = db.session.get(LimitedTenderEnquiry, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"LimitedTenderEnquiry {rec_id} not found.", 404)
    db.session.delete(rec)
    db.session.commit()
    return jsonify({"success": True, "message": "Limited tender enquiry deleted successfully."}), 200


# =========================================================================
# 5. NOTIFICATION OF AWARD OF CONTRACT (FORM_05_NAC)
# =========================================================================
def _serialize_nac(rec):
    return {
        "id": rec.id,
        "project_id": rec.project_id,
        "nac_no": rec.nac_no,
        "nac_date": rec.nac_date.isoformat() if rec.nac_date else None,
        "nac_title": rec.nac_title,
        "remark": rec.remark,
        "remarks": get_step_remarks_for_response(rec.project_id, 5, fallback_raw=rec.remark, entity_id=rec.id),
        "items": [
            {
                "id": it.id,
                "sr_no": it.sr_no,
                "description": it.description,
                "quantity": float(it.quantity) if it.quantity is not None else None,
                "per_unit_price": float(it.per_unit_price) if it.per_unit_price is not None else None,
                "total_amount": float(it.total_amount) if it.total_amount is not None else None,
            }
            for it in (rec.items or [])
        ],
        "awarded_materials": [
            {
                "id": it.id,
                "sr_no": it.sr_no,
                "description": it.description,
                "quantity": float(it.quantity) if it.quantity is not None else None,
                "per_unit_price": float(it.per_unit_price) if it.per_unit_price is not None else None,
                "total_amount": float(it.total_amount) if it.total_amount is not None else None,
            }
            for it in (rec.items or [])
        ],
        "attachments": _serialize_attachments("notification_award", rec.id),
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


@notification_award_bp.get("")
@jwt_required()
def list_nacs():
    project_id = request.args.get("project_id", type=int)
    query = NotificationAward.query
    if project_id:
        query = query.filter_by(project_id=project_id)
    records = query.order_by(NotificationAward.id.desc()).all()
    return jsonify([_serialize_nac(r) for r in records]), 200


@notification_award_bp.get("/<int:rec_id>")
@jwt_required()
def get_nac(rec_id):
    rec = db.session.get(NotificationAward, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"NotificationAward {rec_id} not found.", 404)
    return jsonify(_serialize_nac(rec)), 200


@notification_award_bp.post("")
@jwt_required()
def create_nac():
    user_id = _get_user_id()
    try:
        raw_payload, files = _extract_payload_and_files()
        data = NotificationAwardCreateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    project = db.session.get(Project, data["project_id"])
    if not project:
        return _error("PROJECT_NOT_FOUND", f"Project {data['project_id']} not found.", 404)

    items_data = data.pop("items", None) or data.pop("awarded_materials", None) or []
    remarks_data = data.pop("remarks", None) or data.get("remark")

    rec = NotificationAward(**{k: v for k, v in data.items() if hasattr(NotificationAward, k)})
    for it in items_data:
        rec.items.append(NotificationAwardItem(
            sr_no=it.get("sr_no"),
            description=it.get("description", ""),
            quantity=it.get("quantity"),
            per_unit_price=it.get("per_unit_price"),
            total_amount=it.get("total_amount"),
        ))

    db.session.add(rec)
    db.session.flush()

    _save_attachments(files, "notification_award", rec.id, user_id)
    _save_remarks(rec.project_id, 5, rec.id, remarks_data, user_id)
    db.session.commit()
    return jsonify(_serialize_nac(rec)), 201


@notification_award_bp.patch("/<int:rec_id>")
@jwt_required()
def update_nac(rec_id):
    user_id = _get_user_id()
    rec = db.session.get(NotificationAward, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"NotificationAward {rec_id} not found.", 404)

    try:
        raw_payload, files = _extract_payload_and_files()
        data = NotificationAwardUpdateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    items_data = data.pop("items", None) if "items" in data else data.pop("awarded_materials", None)
    remarks_data = data.pop("remarks", None) if "remarks" in data else data.get("remark")

    for k, v in data.items():
        if hasattr(rec, k):
            setattr(rec, k, v)
    if "bid_number" in data and data["bid_number"]:
        rec.pqb_no = data["bid_number"]

    if items_data is not None:
        rec.items.clear()
        for it in items_data:
            rec.items.append(NotificationAwardItem(
                sr_no=it.get("sr_no"),
                description=it.get("description", ""),
                quantity=it.get("quantity"),
                per_unit_price=it.get("per_unit_price"),
                total_amount=it.get("total_amount"),
            ))

    _save_attachments(files, "notification_award", rec.id, user_id)
    if remarks_data is not None:
        _save_remarks(rec.project_id, 5, rec.id, remarks_data, user_id)

    rec.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_serialize_nac(rec)), 200


@notification_award_bp.delete("/<int:rec_id>")
@jwt_required()
def delete_nac(rec_id):
    rec = db.session.get(NotificationAward, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"NotificationAward {rec_id} not found.", 404)
    db.session.delete(rec)
    db.session.commit()
    return jsonify({"success": True, "message": "Notification of award deleted successfully."}), 200


# =========================================================================
# 6. CONSULTANCY INVOICE (FORM_06_CONSULTANCY_INVOICE)
# =========================================================================
def _serialize_consultancy_invoice(rec):
    return {
        "id": rec.id,
        "project_id": rec.project_id,
        "invoice_no": rec.invoice_no,
        "invoice_date": rec.invoice_date.isoformat() if rec.invoice_date else None,
        "party_name": rec.party_name,
        "invoice_reference": rec.invoice_reference,
        "total_value_eur": float(rec.total_value_eur) if rec.total_value_eur is not None else None,
        "remark": rec.remark,
        "remarks": get_step_remarks_for_response(rec.project_id, 6, fallback_raw=rec.remark, entity_id=rec.id),
        "attachments": _serialize_attachments("consultancy_invoice", rec.id),
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


@consultancy_invoice_bp.get("")
@jwt_required()
def list_consultancy_invoices():
    project_id = request.args.get("project_id", type=int)
    query = ConsultancyInvoice.query
    if project_id:
        query = query.filter_by(project_id=project_id)
    records = query.order_by(ConsultancyInvoice.id.desc()).all()
    return jsonify([_serialize_consultancy_invoice(r) for r in records]), 200


@consultancy_invoice_bp.get("/<int:rec_id>")
@jwt_required()
def get_consultancy_invoice(rec_id):
    rec = db.session.get(ConsultancyInvoice, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"ConsultancyInvoice {rec_id} not found.", 404)
    return jsonify(_serialize_consultancy_invoice(rec)), 200


@consultancy_invoice_bp.post("")
@jwt_required()
def create_consultancy_invoice():
    user_id = _get_user_id()
    try:
        raw_payload, files = _extract_payload_and_files()
        data = ConsultancyInvoiceCreateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    project = db.session.get(Project, data["project_id"])
    if not project:
        return _error("PROJECT_NOT_FOUND", f"Project {data['project_id']} not found.", 404)

    remarks_data = data.pop("remarks", None) or data.get("remark")
    rec = ConsultancyInvoice(**{k: v for k, v in data.items() if hasattr(ConsultancyInvoice, k)})
    db.session.add(rec)
    db.session.flush()

    _save_attachments(files, "consultancy_invoice", rec.id, user_id)
    _save_remarks(rec.project_id, 6, rec.id, remarks_data, user_id)
    db.session.commit()
    return jsonify(_serialize_consultancy_invoice(rec)), 201


@consultancy_invoice_bp.patch("/<int:rec_id>")
@jwt_required()
def update_consultancy_invoice(rec_id):
    user_id = _get_user_id()
    rec = db.session.get(ConsultancyInvoice, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"ConsultancyInvoice {rec_id} not found.", 404)

    try:
        raw_payload, files = _extract_payload_and_files()
        data = ConsultancyInvoiceUpdateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    remarks_data = data.pop("remarks", None) if "remarks" in data else data.get("remark")
    for k, v in data.items():
        if hasattr(rec, k):
            setattr(rec, k, v)
    if "bid_number" in data and data["bid_number"]:
        rec.pqb_no = data["bid_number"]

    _save_attachments(files, "consultancy_invoice", rec.id, user_id)
    if remarks_data is not None:
        _save_remarks(rec.project_id, 6, rec.id, remarks_data, user_id)

    rec.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_serialize_consultancy_invoice(rec)), 200


@consultancy_invoice_bp.delete("/<int:rec_id>")
@jwt_required()
def delete_consultancy_invoice(rec_id):
    rec = db.session.get(ConsultancyInvoice, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"ConsultancyInvoice {rec_id} not found.", 404)
    db.session.delete(rec)
    db.session.commit()
    return jsonify({"success": True, "message": "Consultancy invoice deleted successfully."}), 200


# =========================================================================
# 7. EXPRESSION OF INTEREST (FORM_07_EOI)
# =========================================================================
def _serialize_eoi(rec):
    return {
        "id": rec.id,
        "project_id": rec.project_id,
        "eoi_title": rec.eoi_title,
        "eoi_no": rec.eoi_no,
        "eoi_date": rec.eoi_date.isoformat() if rec.eoi_date else None,
        "eoi_closing_date_time": rec.eoi_closing_date_time.isoformat() if rec.eoi_closing_date_time else None,
        "eoi_opening_date_time": rec.eoi_opening_date_time.isoformat() if rec.eoi_opening_date_time else None,
        "mode_of_submission": rec.mode_of_submission,
        "supply_location": rec.supply_location,
        "remark": rec.remark,
        "remarks": get_step_remarks_for_response(rec.project_id, 7, fallback_raw=rec.remark, entity_id=rec.id),
        "items": [
            {
                "id": it.id,
                "sr_no": it.sr_no,
                "description": it.description,
                "unit": it.unit,
                "quantity": float(it.quantity) if it.quantity is not None else None,
            }
            for it in (rec.items or [])
        ],
        "attachments": _serialize_attachments("expression_of_interest", rec.id),
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


@expression_of_interest_bp.get("")
@jwt_required()
def list_eois():
    project_id = request.args.get("project_id", type=int)
    query = ExpressionOfInterest.query
    if project_id:
        query = query.filter_by(project_id=project_id)
    records = query.order_by(ExpressionOfInterest.id.desc()).all()
    return jsonify([_serialize_eoi(r) for r in records]), 200


@expression_of_interest_bp.get("/<int:rec_id>")
@jwt_required()
def get_eoi(rec_id):
    rec = db.session.get(ExpressionOfInterest, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"ExpressionOfInterest {rec_id} not found.", 404)
    return jsonify(_serialize_eoi(rec)), 200


@expression_of_interest_bp.post("")
@jwt_required()
def create_eoi():
    user_id = _get_user_id()
    try:
        raw_payload, files = _extract_payload_and_files()
        data = ExpressionOfInterestCreateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    project = db.session.get(Project, data["project_id"])
    if not project:
        return _error("PROJECT_NOT_FOUND", f"Project {data['project_id']} not found.", 404)

    items_data = data.pop("items", None) or data.pop("requirements", None) or []
    remarks_data = data.pop("remarks", None) or data.get("remark")

    rec = ExpressionOfInterest(**{k: v for k, v in data.items() if hasattr(ExpressionOfInterest, k)})
    for it in items_data:
        rec.items.append(ExpressionOfInterestItem(
            sr_no=it.get("sr_no"),
            description=it.get("description", ""),
            unit=it.get("unit"),
            quantity=it.get("quantity"),
        ))

    db.session.add(rec)
    db.session.flush()

    _save_attachments(files, "expression_of_interest", rec.id, user_id)
    _save_remarks(rec.project_id, 7, rec.id, remarks_data, user_id)
    db.session.commit()
    return jsonify(_serialize_eoi(rec)), 201


@expression_of_interest_bp.patch("/<int:rec_id>")
@jwt_required()
def update_eoi(rec_id):
    user_id = _get_user_id()
    rec = db.session.get(ExpressionOfInterest, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"ExpressionOfInterest {rec_id} not found.", 404)

    try:
        raw_payload, files = _extract_payload_and_files()
        data = ExpressionOfInterestUpdateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    items_data = data.pop("items", None) if "items" in data else data.pop("requirements", None)
    remarks_data = data.pop("remarks", None) if "remarks" in data else data.get("remark")

    for k, v in data.items():
        if hasattr(rec, k):
            setattr(rec, k, v)
    if "bid_number" in data and data["bid_number"]:
        rec.pqb_no = data["bid_number"]

    if items_data is not None:
        rec.items.clear()
        for it in items_data:
            rec.items.append(ExpressionOfInterestItem(
                sr_no=it.get("sr_no"),
                description=it.get("description", ""),
                unit=it.get("unit"),
                quantity=it.get("quantity"),
            ))

    _save_attachments(files, "expression_of_interest", rec.id, user_id)
    if remarks_data is not None:
        _save_remarks(rec.project_id, 7, rec.id, remarks_data, user_id)

    rec.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_serialize_eoi(rec)), 200


@expression_of_interest_bp.delete("/<int:rec_id>")
@jwt_required()
def delete_eoi(rec_id):
    rec = db.session.get(ExpressionOfInterest, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"ExpressionOfInterest {rec_id} not found.", 404)
    db.session.delete(rec)
    db.session.commit()
    return jsonify({"success": True, "message": "Expression of interest deleted successfully."}), 200
