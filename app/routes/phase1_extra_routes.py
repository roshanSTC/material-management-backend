import json
from datetime import date, datetime
from decimal import Decimal

from flask import current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions.database import db
from app.models import (
    BidDocumentIcb,
    BidDocumentIcbItem,
    BidDocumentLte,
    BidDocumentLteItem,
    BidDocumentSte,
    BidDocumentSteItem,
    BidDocumentTechnoCommercial,
    BidDocumentTechnoCommercialItem,
    InternationalCompetitiveBidding,
    InternationalCompetitiveBiddingItem,
    Project,
    ProjectStep,
    TechnoCommercialTender,
    TechnoCommercialTenderItem,
)
from app.schemas.phase1 import (
    BidDocumentIcbCreateSchema,
    BidDocumentIcbUpdateSchema,
    BidDocumentLteCreateSchema,
    BidDocumentLteUpdateSchema,
    BidDocumentSteCreateSchema,
    BidDocumentSteUpdateSchema,
    BidDocumentTechnoCommercialCreateSchema,
    BidDocumentTechnoCommercialUpdateSchema,
    InternationalCompetitiveBiddingCreateSchema,
    InternationalCompetitiveBiddingUpdateSchema,
    LatestBidDocumentLteQuerySchema,
    LatestBidDocumentLteResponseSchema,
    LatestBidDocumentSteQuerySchema,
    LatestBidDocumentSteResponseSchema,
    LatestInternationalCompetitiveBiddingQuerySchema,
    LatestInternationalCompetitiveBiddingResponseSchema,
    LatestSingleTenderEnquiryQuerySchema,
    LatestSingleTenderEnquiryResponseSchema,
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
    description="Bid Document Techno-Commercials (Plural) APIs",
)


# 2. Form 30/33: Techno-Commercial Tender / Single Tender Enquiry (STE)
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
    description="Techno-Commercial Tender (Singular) APIs",
)

single_tender_enquiries_bp = Blueprint(
    "single_tender_enquiries",
    __name__,
    url_prefix="/api/v1/single-tender-enquiries",
    description="Single Tender Enquiry APIs",
)

single_tender_enquiry_bp = Blueprint(
    "single_tender_enquiry",
    __name__,
    url_prefix="/api/v1/single-tender-enquiry",
    description="Single Tender Enquiry (Singular) APIs",
)

single_tender_enquiry_ste_bp = Blueprint(
    "single_tender_enquiry_ste",
    __name__,
    url_prefix="/api/v1/single-tender-enquiry-ste",
    description="Single Tender Enquiry STE APIs",
)

ste_bp = Blueprint(
    "ste",
    __name__,
    url_prefix="/api/v1/ste",
    description="STE APIs",
)

stes_bp = Blueprint(
    "stes",
    __name__,
    url_prefix="/api/v1/stes",
    description="STEs APIs",
)

tct_bp = Blueprint(
    "tct",
    __name__,
    url_prefix="/api/v1/tct",
    description="TCT APIs",
)

tcts_bp = Blueprint(
    "tcts",
    __name__,
    url_prefix="/api/v1/tcts",
    description="TCTs APIs",
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
    description="Bid Document LTE (Plural) APIs",
)


# 4. Form 34: Bid Document STE
bid_document_ste_bp = Blueprint(
    "bid_document_ste",
    __name__,
    url_prefix="/api/v1/bid-document-ste",
    description="Bid Document STE APIs",
)

bid_document_stes_bp = Blueprint(
    "bid_document_stes",
    __name__,
    url_prefix="/api/v1/bid-document-stes",
    description="Bid Document STEs (Plural) APIs",
)

bid_document_for_ste_bp = Blueprint(
    "bid_document_for_ste",
    __name__,
    url_prefix="/api/v1/bid-document-for-ste",
    description="Bid Document for STE APIs",
)


# 5. Form 35: International Competitive Bidding (ICB)
international_competitive_biddings_bp = Blueprint(
    "international_competitive_biddings",
    __name__,
    url_prefix="/api/v1/international-competitive-biddings",
    description="International Competitive Biddings APIs",
)

international_competitive_bidding_bp = Blueprint(
    "international_competitive_bidding",
    __name__,
    url_prefix="/api/v1/international-competitive-bidding",
    description="International Competitive Bidding (Singular) APIs",
)

icb_bp = Blueprint(
    "icb",
    __name__,
    url_prefix="/api/v1/icb",
    description="ICB APIs",
)

icbs_bp = Blueprint(
    "icbs",
    __name__,
    url_prefix="/api/v1/icbs",
    description="ICBs APIs",
)


# 6. Form 36: Bid Document ICB
bid_document_icb_bp = Blueprint(
    "bid_document_icb",
    __name__,
    url_prefix="/api/v1/bid-document-icb",
    description="Bid Document ICB APIs",
)

bid_document_icbs_bp = Blueprint(
    "bid_document_icbs",
    __name__,
    url_prefix="/api/v1/bid-document-icbs",
    description="Bid Document ICBs (Plural) APIs",
)

bid_document_for_icb_bp = Blueprint(
    "bid_document_for_icb",
    __name__,
    url_prefix="/api/v1/bid-document-for-icb",
    description="Bid Document for ICB APIs",
)


EXTRA_BLUEPRINTS = [
    bid_document_techno_commercial_bp,
    bid_document_techno_commercial_plural_bp,
    techno_commercial_tender_bp,
    techno_commercial_tender_singular_bp,
    single_tender_enquiries_bp,
    single_tender_enquiry_bp,
    single_tender_enquiry_ste_bp,
    ste_bp,
    stes_bp,
    tct_bp,
    tcts_bp,
    bid_document_lte_bp,
    bid_document_lte_plural_bp,
    bid_document_ste_bp,
    bid_document_stes_bp,
    bid_document_for_ste_bp,
    international_competitive_biddings_bp,
    international_competitive_bidding_bp,
    icb_bp,
    icbs_bp,
    bid_document_icb_bp,
    bid_document_icbs_bp,
    bid_document_for_icb_bp,
]


# =========================================================================
# COMMON HELPERS
# =========================================================================
def _make_json_serializable(obj):
    if obj is None:
        return None
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {str(k): _make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_json_serializable(v) for v in obj]
    return obj


def _get_step_num_for_form(project_id: int, possible_codes: list[str], default: int) -> int:
    try:
        step = ProjectStep.query.filter(
            ProjectStep.project_id == project_id,
            ProjectStep.form_code.in_(possible_codes),
        ).first()
        if step and step.step_number:
            return step.step_number
    except Exception:
        pass
    return default


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

        for key in request.files:
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

        possible_codes = [form_code]
        if form_code in ("FORM_30_TECHNO_COMMERCIAL_TENDER", "FORM_30_TCT", "FORM_30"):
            possible_codes = ["FORM_30_TECHNO_COMMERCIAL_TENDER", "FORM_30_TCT", "FORM_30"]
        elif form_code in ("FORM_33_STE", "FORM_33_SINGLE_TENDER_ENQUIRY", "FORM_33", "FORM_STE", "FORM_30_SINGLE_TENDER_ENQUIRY", "FORM_30_STE"):
            possible_codes = ["FORM_33_STE", "FORM_33_SINGLE_TENDER_ENQUIRY", "FORM_33", "FORM_STE", "FORM_30_SINGLE_TENDER_ENQUIRY", "FORM_30_STE"]
            # Canonical single tender enquiry codes
        elif form_code in ("FORM_29_BID_DOC_TECHNO_COMMERCIAL", "FORM_29_BID_DOCUMENT_TECHNO_COMMERCIAL"):
            possible_codes = ["FORM_29_BID_DOC_TECHNO_COMMERCIAL", "FORM_29_BID_DOCUMENT_TECHNO_COMMERCIAL"]
        elif form_code in ("FORM_31_BID_DOC_LTE", "FORM_31_BID_DOCUMENT_LTE"):
            possible_codes = ["FORM_31_BID_DOC_LTE", "FORM_31_BID_DOCUMENT_LTE"]
        elif form_code in ("FORM_34_BID_DOC_STE", "FORM_34_BID_DOCUMENT_STE"):
            possible_codes = ["FORM_34_BID_DOC_STE", "FORM_34_BID_DOCUMENT_STE"]

        step = ProjectStep.query.filter(
            ProjectStep.project_id == project_id,
            ProjectStep.form_code.in_(possible_codes),
        ).first()

        if not step:
            from app.models.form_definition import FormDefinition
            fdef = FormDefinition.query.filter(FormDefinition.form_code.in_(possible_codes)).first()
            max_order = (
                db.session.query(db.func.max(ProjectStep.step_order))
                .filter_by(project_id=project_id)
                .scalar()
                or 0
            )
            max_step_num = (
                db.session.query(db.func.max(ProjectStep.step_number))
                .filter_by(project_id=project_id)
                .scalar()
                or 0
            )
            step = ProjectStep(
                project_id=project_id,
                step_order=max_order + 1,
                step_number=max(max_order + 1, max_step_num + 1),
                form_code=form_code,
                step_name=fdef.name if fdef else form_code,
                description=fdef.description if fdef else "",
                status=status or "completed",
                progress_percentage=100 if (status or "completed") == "completed" else 50,
                completed_at=datetime.utcnow() if (status or "completed") == "completed" else None,
                data={},
            )
            db.session.add(step)
            db.session.flush()

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


def _error(code: str, message: str, status_code: int = 400):
    return make_response(jsonify({"success": False, "error": {"code": code, "message": message}}), status_code)


# =========================================================================
# 1. FORM_29_BID_DOC_TECHNO_COMMERCIAL
# =========================================================================
def _serialize_bid_doc_techno_commercial(rec):
    atts = _serialize_attachments("bid_document_techno_commercial", rec.id)
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_29_BID_DOC_TECHNO_COMMERCIAL", "FORM_29_BID_DOCUMENT_TECHNO_COMMERCIAL"],
        default=29,
    )
    remarks = get_step_remarks_for_response(
        rec.project_id,
        step_num,
        fallback_raw=rec.remark,
        entity_id=rec.id,
    )
    if not remarks and step_num != 29:
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
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_29_BID_DOC_TECHNO_COMMERCIAL", "FORM_29_BID_DOCUMENT_TECHNO_COMMERCIAL"],
        default=29,
    )
    _save_remarks(rec.project_id, step_num, rec.id, remarks_data, user_id)
    if step_num != 29:
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
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_29_BID_DOC_TECHNO_COMMERCIAL", "FORM_29_BID_DOCUMENT_TECHNO_COMMERCIAL"],
        default=29,
    )
    _save_remarks(rec.project_id, step_num, rec.id, remarks_data, user_id)
    if step_num != 29:
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
    bp.route("", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_get_bid_doc_techno_commercial)))
    bp.route("/<int:rec_id>", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_get_bid_doc_techno_commercial)))
    bp.route("", methods=["POST"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_create_bid_doc_techno_commercial)))
    bp.route("/<int:rec_id>", methods=["PATCH", "PUT"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_update_bid_doc_techno_commercial)))
    bp.route("/<int:rec_id>", methods=["DELETE"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_delete_bid_doc_techno_commercial)))


# =========================================================================
# 2. FORM_30 / FORM_33: SINGLE TENDER ENQUIRY (STE) / TECHNO-COMMERCIAL TENDER
# =========================================================================
def _serialize_techno_commercial_tender(rec):
    atts = _serialize_attachments("techno_commercial_tender", rec.id)
    if not atts:
        atts = _serialize_attachments("single_tender_enquiry", rec.id)

    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_33_STE", "FORM_33_SINGLE_TENDER_ENQUIRY", "FORM_33", "FORM_STE", "FORM_30_SINGLE_TENDER_ENQUIRY", "FORM_30_STE"] if (rec.form_code and any(k in rec.form_code.upper() for k in ("33", "STE"))) else ["FORM_30_TECHNO_COMMERCIAL_TENDER", "FORM_30_TCT", "FORM_30"],
        default=30,
    )
    remarks = get_step_remarks_for_response(
        rec.project_id,
        step_num,
        fallback_raw=rec.remark,
        entity_id=rec.id,
    )
    if not remarks and step_num != 30:
        remarks = get_step_remarks_for_response(
            rec.project_id,
            30,
            fallback_raw=rec.remark,
            entity_id=rec.id,
        )
    if not remarks and step_num != 33:
        remarks = get_step_remarks_for_response(
            rec.project_id,
            33,
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
        "pqb_number": rec.pqb_no,
        "tender_title": rec.tender_title,
        "tender_no": rec.tender_no,
        "tender_number": rec.tender_no,
        "tender_enquiry_no": rec.tender_no,
        "ste_no": rec.tender_no,
        "tender_issue_date": rec.tender_issue_date.isoformat() if rec.tender_issue_date else None,
        "bid_submission_due_date_time": rec.bid_submission_due_date_time.isoformat() if rec.bid_submission_due_date_time else None,
        "bid_opening_date_time": rec.bid_opening_date_time.isoformat() if rec.bid_opening_date_time else None,
        "tender_fee": float(rec.tender_fee) if rec.tender_fee is not None else None,
        "emd": float(rec.emd) if rec.emd is not None else None,
        "tender_validity": rec.tender_validity,
        "validity": rec.tender_validity,
        "remark": rec.remark,
        "remarks": remarks,
        "items": items,
        "requirements": items,
        "attachments": atts,
        "attachments_count": len(atts),
        "status": rec.status or "completed",
        "form_code": rec.form_code or ("FORM_33_STE" if (request and any(k in getattr(request, "path", "") for k in ("single-tender", "ste"))) else "FORM_30_TECHNO_COMMERCIAL_TENDER"),
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

    items_data = data.pop("items", None) or data.pop("requirements", None) or []
    data.pop("requirements", None)
    remarks_data = raw_payload.get("remarks") or data.pop("remarks", None) or data.get("remark") or raw_payload.get("remark")
    data.pop("remarks", None)
    data.pop("remark", None)
    status_val = data.pop("status", None) or raw_payload.get("status") or "completed"
    form_code_val = raw_payload.get("form_code") or data.pop("form_code", None) or ("FORM_30_TECHNO_COMMERCIAL_TENDER" if "techno-commercial" in getattr(request, "path", "") else "FORM_33_STE")
    data.pop("attachments_count", None)
    data.pop("form_code", None)

    # Normalize aliases
    if not data.get("tender_no"):
        for alias in ("ste_no", "tender_number", "tender_enquiry_no"):
            if data.get(alias):
                data["tender_no"] = data.pop(alias)
                break
    for alias in ("ste_no", "tender_number", "tender_enquiry_no"):
        data.pop(alias, None)

    if not data.get("pqb_no") and data.get("pqb_number"):
        data["pqb_no"] = data.pop("pqb_number")
    data.pop("pqb_number", None)

    if not data.get("tender_validity") and data.get("validity"):
        data["tender_validity"] = data.pop("validity")
    data.pop("validity", None)

    if not data.get("bid_submission_due_date_time"):
        for alias in ("submission_due_date_time", "bid_submission_due_date"):
            if data.get(alias):
                data["bid_submission_due_date_time"] = data.pop(alias)
                break
    data.pop("submission_due_date_time", None)
    data.pop("bid_submission_due_date", None)

    if not data.get("bid_opening_date_time") and data.get("opening_date_time"):
        data["bid_opening_date_time"] = data.pop("opening_date_time")
    data.pop("opening_date_time", None)

    rec = TechnoCommercialTender(**{k: v for k, v in data.items() if hasattr(TechnoCommercialTender, k)})
    rec.status = status_val
    rec.form_code = form_code_val

    if not rec.remark and remarks_data:
        if isinstance(remarks_data, list) and remarks_data:
            first_rem = remarks_data[0]
            rec.remark = first_rem.get("remark") if isinstance(first_rem, dict) else str(first_rem)
        elif isinstance(remarks_data, str):
            rec.remark = remarks_data

    for it in items_data:
        rec.items.append(TechnoCommercialTenderItem(
            sr_no=it.get("sr_no"),
            description=it.get("description", "") or it.get("material_name", ""),
            material_name=it.get("material_name") or it.get("description", ""),
            unit=it.get("unit"),
            quantity=it.get("quantity"),
        ))

    db.session.add(rec)
    db.session.flush()

    _save_attachments(files, "techno_commercial_tender", rec.id, user_id)
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_33_STE", "FORM_33_SINGLE_TENDER_ENQUIRY", "FORM_33", "FORM_STE", "FORM_30_SINGLE_TENDER_ENQUIRY", "FORM_30_STE"] if (rec.form_code and any(k in rec.form_code.upper() for k in ("33", "STE"))) else ["FORM_30_TECHNO_COMMERCIAL_TENDER", "FORM_30_TCT", "FORM_30"],
        default=30,
    )
    _save_remarks(rec.project_id, step_num, rec.id, remarks_data, user_id)
    if step_num != 30:
        _save_remarks(rec.project_id, 30, rec.id, remarks_data, user_id)
    db.session.commit()

    serialized = _serialize_techno_commercial_tender(rec)
    _sync_step(rec.project_id, form_code_val, status_val, serialized)
    return jsonify(serialized), 201


def handle_get_latest_techno_commercial_tender(args=None):
    if args is None:
        args = {}
    project_id = (
        args.get("project_id")
        or request.args.get("project_id")
        or request.args.get("projectId")
    )
    query = TechnoCommercialTender.query
    if project_id is not None:
        try:
            pid = int(project_id)
            if pid <= 0:
                return _error("INVALID_PROJECT_ID", "project_id must be a positive integer.", 400)
        except (ValueError, TypeError):
            return _error("INVALID_PROJECT_ID", "project_id must be an integer.", 400)

        project = db.session.get(Project, pid)
        if not project:
            return _error("PROJECT_NOT_FOUND", f"Project {pid} not found.", 404)
        query = query.filter_by(project_id=pid)

    rec = query.order_by(TechnoCommercialTender.id.desc()).first()
    if not rec:
        return _error("NOT_FOUND", "Single tender enquiry not found.", 404)

    return jsonify({
        "tender_title": rec.tender_title,
        "tender_enquiry_no": rec.tender_enquiry_no or rec.tender_no,
    }), 200


def handle_get_techno_commercial_tender(rec_id=None):
    if request.args.get("latest") in ("true", "1"):
        return handle_get_latest_techno_commercial_tender()
    if rec_id is not None:
        rec = db.session.get(TechnoCommercialTender, rec_id)
        if not rec:
            step = db.session.get(ProjectStep, rec_id)
            if step and step.project_id:
                rec = TechnoCommercialTender.query.filter_by(project_id=step.project_id).order_by(TechnoCommercialTender.id.desc()).first()
        if not rec:
            return _error("NOT_FOUND", f"TechnoCommercialTender {rec_id} not found.", 404)
        return jsonify(_serialize_techno_commercial_tender(rec)), 200

    project_id = request.args.get("project_id", type=int)
    q = TechnoCommercialTender.query
    if project_id:
        q = q.filter_by(project_id=project_id)







    form_filter = request.args.get("form_code")
    if form_filter:
        q = q.filter(TechnoCommercialTender.form_code == form_filter)
    elif any(k in getattr(request, "path", "") for k in ("single-tender", "/ste")):
        q = q.filter(TechnoCommercialTender.form_code.in_(["FORM_33_STE", "FORM_33_SINGLE_TENDER_ENQUIRY", "FORM_33", "FORM_STE", "FORM_30_SINGLE_TENDER_ENQUIRY", "FORM_30_STE"]))
    elif "techno-commercial" in getattr(request, "path", ""):
        q = q.filter(TechnoCommercialTender.form_code.in_(["FORM_30_TECHNO_COMMERCIAL_TENDER", "FORM_30_TCT", "FORM_30"]))
    records = q.order_by(TechnoCommercialTender.id.desc()).all()
    return jsonify([_serialize_techno_commercial_tender(r) for r in records]), 200


def handle_update_techno_commercial_tender(rec_id: int):
    user_id = _get_user_id()
    rec = db.session.get(TechnoCommercialTender, rec_id)
    if not rec:
        step = db.session.get(ProjectStep, rec_id)
        if step and step.project_id:
            rec = TechnoCommercialTender.query.filter_by(project_id=step.project_id).order_by(TechnoCommercialTender.id.desc()).first()
    if not rec:
        return _error("NOT_FOUND", f"TechnoCommercialTender {rec_id} not found.", 404)

    try:
        raw_payload, files = _extract_payload_and_files()
        data = TechnoCommercialTenderUpdateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    items_data = data.pop("items", None) if "items" in data else (data.pop("requirements", None) if "requirements" in data else None)
    data.pop("requirements", None)
    remarks_data = raw_payload.get("remarks") if "remarks" in raw_payload else (data.pop("remarks", None) if "remarks" in data else data.get("remark"))
    data.pop("remarks", None)
    data.pop("remark", None)
    status_val = data.pop("status", None) or raw_payload.get("status")
    form_code_val = raw_payload.get("form_code") or data.pop("form_code", None)
    data.pop("attachments_count", None)
    data.pop("form_code", None)

    if not data.get("tender_no"):
        for alias in ("ste_no", "tender_number", "tender_enquiry_no"):
            if data.get(alias):
                data["tender_no"] = data.pop(alias)
                break
    for alias in ("ste_no", "tender_number", "tender_enquiry_no"):
        data.pop(alias, None)

    if "pqb_number" in data and not data.get("pqb_no"):
        data["pqb_no"] = data.pop("pqb_number")
    data.pop("pqb_number", None)

    if "validity" in data and not data.get("tender_validity"):
        data["tender_validity"] = data.pop("validity")
    data.pop("validity", None)

    if not data.get("bid_submission_due_date_time"):
        for alias in ("submission_due_date_time", "bid_submission_due_date"):
            if data.get(alias):
                data["bid_submission_due_date_time"] = data.pop(alias)
                break
    data.pop("submission_due_date_time", None)
    data.pop("bid_submission_due_date", None)

    if not data.get("bid_opening_date_time") and data.get("opening_date_time"):
        data["bid_opening_date_time"] = data.pop("opening_date_time")
    data.pop("opening_date_time", None)

    for k, v in data.items():
        if hasattr(rec, k):
            setattr(rec, k, v)
    if status_val:
        rec.status = status_val
    if form_code_val:
        rec.form_code = form_code_val

    if remarks_data:
        if isinstance(remarks_data, list) and remarks_data:
            first_rem = remarks_data[0]
            rec.remark = first_rem.get("remark") if isinstance(first_rem, dict) else str(first_rem)
        elif isinstance(remarks_data, str):
            rec.remark = remarks_data

    if items_data is not None:
        rec.items.clear()
        for it in items_data:
            rec.items.append(TechnoCommercialTenderItem(
                sr_no=it.get("sr_no"),
                description=it.get("description", "") or it.get("material_name", ""),
                material_name=it.get("material_name") or it.get("description", ""),
                unit=it.get("unit"),
                quantity=it.get("quantity"),
            ))

    _save_attachments(files, "techno_commercial_tender", rec.id, user_id)
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_33_STE", "FORM_33_SINGLE_TENDER_ENQUIRY", "FORM_33", "FORM_STE", "FORM_30_SINGLE_TENDER_ENQUIRY", "FORM_30_STE"] if (rec.form_code and any(k in rec.form_code.upper() for k in ("33", "STE"))) else ["FORM_30_TECHNO_COMMERCIAL_TENDER", "FORM_30_TCT", "FORM_30"],
        default=30,
    )
    _save_remarks(rec.project_id, step_num, rec.id, remarks_data, user_id)
    if step_num != 30:
        _save_remarks(rec.project_id, 30, rec.id, remarks_data, user_id)
    db.session.commit()

    serialized = _serialize_techno_commercial_tender(rec)
    _sync_step(rec.project_id, rec.form_code or "FORM_33_STE", rec.status, serialized)
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
    return jsonify({"success": True, "message": "Single Tender Enquiry (STE) deleted successfully."}), 200


# Wire routes to blueprints
for bp in (
    techno_commercial_tender_bp,
    techno_commercial_tender_singular_bp,
    single_tender_enquiries_bp,
    single_tender_enquiry_bp,
    single_tender_enquiry_ste_bp,
    ste_bp,
    stes_bp,
    tct_bp,
    tcts_bp,
):
    bp.route("/latest", methods=["GET"])(
        bp.doc(
            security=[{"BearerAuth": []}],
            summary="Get Latest Single Tender Enquiry",
            description="Retrieve only tender_title and tender_enquiry_no for the latest single tender enquiry.",
        )(
            bp.arguments(LatestSingleTenderEnquiryQuerySchema, location="query")(
                bp.response(200, LatestSingleTenderEnquiryResponseSchema)(
                    jwt_required()(handle_get_latest_techno_commercial_tender)
                )
            )
        )
    )
    bp.route("", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_get_techno_commercial_tender)))
    bp.route("/<int:rec_id>", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_get_techno_commercial_tender)))
    bp.route("", methods=["POST"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_create_techno_commercial_tender)))
    bp.route("/<int:rec_id>", methods=["PATCH", "PUT"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_update_techno_commercial_tender)))
    bp.route("/<int:rec_id>", methods=["DELETE"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_delete_techno_commercial_tender)))


# =========================================================================
# 3. FORM_31_BID_DOC_LTE
# =========================================================================
def _serialize_bid_doc_lte(rec):
    atts = _serialize_attachments("bid_document_lte", rec.id)
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_31_BID_DOC_LTE", "FORM_31_BID_DOCUMENT_LTE"],
        default=31,
    )
    remarks = get_step_remarks_for_response(
        rec.project_id,
        step_num,
        fallback_raw=rec.remark,
        entity_id=rec.id,
    )
    if not remarks and step_num != 31:
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
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_31_BID_DOC_LTE", "FORM_31_BID_DOCUMENT_LTE"],
        default=31,
    )
    _save_remarks(rec.project_id, step_num, rec.id, remarks_data, user_id)
    if step_num != 31:
        _save_remarks(rec.project_id, 31, rec.id, remarks_data, user_id)
    db.session.commit()

    serialized = _serialize_bid_doc_lte(rec)
    _sync_step(rec.project_id, "FORM_31_BID_DOC_LTE", status_val, serialized)
    return jsonify(serialized), 201


def handle_get_latest_bid_doc_lte(args=None):
    if args is None:
        args = {}
    project_id = (
        args.get("project_id")
        or request.args.get("project_id")
        or request.args.get("projectId")
    )
    query = BidDocumentLte.query
    if project_id is not None:
        try:
            pid = int(project_id)
            if pid <= 0:
                return _error("INVALID_PROJECT_ID", "project_id must be a positive integer.", 400)
        except (ValueError, TypeError):
            return _error("INVALID_PROJECT_ID", "project_id must be an integer.", 400)

        project = db.session.get(Project, pid)
        if not project:
            return _error("PROJECT_NOT_FOUND", f"Project {pid} not found.", 404)
        query = query.filter_by(project_id=pid)

    rec = query.order_by(BidDocumentLte.id.desc()).first()
    if not rec:
        return _error("NOT_FOUND", "Bid document LTE not found.", 404)

    return jsonify({
        "delivery_term": rec.delivery_terms,
        "gst_pct": float(rec.gst_pct) if rec.gst_pct is not None else None,
        "payment_terms": rec.payment_terms,
        "warranty_period": rec.warranty_period,
        "items": [
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
        ],
    }), 200


def handle_get_bid_doc_lte(rec_id=None):
    if request.args.get("latest") in ("true", "1"):
        return handle_get_latest_bid_doc_lte()
    if rec_id is not None:
        rec = db.session.get(BidDocumentLte, rec_id)
        if not rec:
            step = db.session.get(ProjectStep, rec_id)
            if step and step.project_id:
                rec = BidDocumentLte.query.filter_by(project_id=step.project_id).order_by(BidDocumentLte.id.desc()).first()
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
        step = db.session.get(ProjectStep, rec_id)
        if step and step.project_id:
            rec = BidDocumentLte.query.filter_by(project_id=step.project_id).order_by(BidDocumentLte.id.desc()).first()
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
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_31_BID_DOC_LTE", "FORM_31_BID_DOCUMENT_LTE"],
        default=31,
    )
    _save_remarks(rec.project_id, step_num, rec.id, remarks_data, user_id)
    if step_num != 31:
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
    bp.route("/latest", methods=["GET"])(
        bp.doc(
            security=[{"BearerAuth": []}],
            summary="Get Latest Bid Document LTE",
            description="Retrieve only delivery_term, gst_pct, payment_terms, warranty_period, and items for the latest bid document LTE.",
        )(
            bp.arguments(LatestBidDocumentLteQuerySchema, location="query")(
                bp.response(200, LatestBidDocumentLteResponseSchema)(
                    jwt_required()(handle_get_latest_bid_doc_lte)
                )
            )
        )
    )
    bp.route("", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_get_bid_doc_lte)))
    bp.route("/<int:rec_id>", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_get_bid_doc_lte)))
    bp.route("", methods=["POST"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_create_bid_doc_lte)))
    bp.route("/<int:rec_id>", methods=["PATCH", "PUT"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_update_bid_doc_lte)))
    bp.route("/<int:rec_id>", methods=["DELETE"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_delete_bid_doc_lte)))


# =========================================================================
# 4. FORM_34_BID_DOC_STE (BID DOCUMENT FOR SINGLE TENDER ENQUIRY)
# =========================================================================
def _serialize_bid_doc_ste(rec):
    atts = _serialize_attachments("bid_document_ste", rec.id)
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_34_BID_DOC_STE", "FORM_34_BID_DOCUMENT_STE"],
        default=34,
    )
    remarks = get_step_remarks_for_response(
        rec.project_id,
        step_num,
        fallback_raw=rec.remark,
        entity_id=rec.id,
    )
    if not remarks and step_num != 34:
        remarks = get_step_remarks_for_response(
            rec.project_id,
            34,
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
        "payment_term": rec.payment_terms,
        "warranty_period": rec.warranty_period,
        "gst_pct": float(rec.gst_pct) if rec.gst_pct is not None else None,
        "gst_rate": float(rec.gst_pct) if rec.gst_pct is not None else None,
        "gst_rate_pct": float(rec.gst_pct) if rec.gst_pct is not None else None,
        "total_net_amount": float(rec.total_net_amount) if rec.total_net_amount is not None else None,
        "total_gross_amount": float(rec.total_gross_amount) if rec.total_gross_amount is not None else None,
        "gst_amount": float(rec.gst_amount) if rec.gst_amount is not None else None,
        "total_amount": float(rec.total_amount) if rec.total_amount is not None else None,
        "remark": rec.remark,
        "remarks": remarks,
        "items": items,
        "attachments": atts,
        "attachments_count": len(atts),
        "status": rec.status or "completed",
        "form_code": rec.form_code or "FORM_34_BID_DOC_STE",
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


def handle_create_bid_doc_ste():
    user_id = _get_user_id()
    try:
        raw_payload, files = _extract_payload_and_files()
        data = BidDocumentSteCreateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    project = db.session.get(Project, data["project_id"])
    if not project:
        return _error("PROJECT_NOT_FOUND", f"Project {data['project_id']} not found.", 404)

    items_data = data.pop("items", None) or data.pop("requirements", None) or []
    data.pop("requirements", None)
    remarks_data = raw_payload.get("remarks") or data.pop("remarks", None) or data.get("remark") or raw_payload.get("remark")
    data.pop("remarks", None)
    data.pop("remark", None)
    data.pop("form_code", None)
    status_val = data.pop("status", None) or raw_payload.get("status") or "completed"
    form_code_val = raw_payload.get("form_code") or data.pop("form_code", None) or "FORM_34_BID_DOC_STE"
    data.pop("attachments_count", None)

    # Normalize aliases
    if "tender_number" in data and not data.get("tender_no"):
        data["tender_no"] = data.pop("tender_number")
    else:
        data.pop("tender_number", None)

    if "total_corrigendum_issued" in data and data.get("total_no_corrigendum_issued") is None:
        data["total_no_corrigendum_issued"] = data.pop("total_corrigendum_issued")
    else:
        data.pop("total_corrigendum_issued", None)

    if "delivery_term" in data and not data.get("delivery_terms"):
        data["delivery_terms"] = data.pop("delivery_term")
    else:
        data.pop("delivery_term", None)

    if "payment_term" in data and not data.get("payment_terms"):
        data["payment_terms"] = data.pop("payment_term")
    else:
        data.pop("payment_term", None)

    if data.get("gst_pct") is None:
        if data.get("gst_rate") is not None:
            data["gst_pct"] = data.pop("gst_rate")
        elif data.get("gst_rate_pct") is not None:
            data["gst_pct"] = data.pop("gst_rate_pct")
    data.pop("gst_rate", None)
    data.pop("gst_rate_pct", None)

    # Calculate item amounts and auto-calculate totals if not supplied
    calc_net = 0.0
    for it in items_data:
        q = float(it.get("quantity") or 0)
        p = float(it.get("unit_price") or 0)
        tot = float(it.get("total_amount") or (q * p if q and p else 0))
        calc_net += tot

    if data.get("total_net_amount") is None and calc_net > 0:
        data["total_net_amount"] = calc_net

    gst_p = float(data.get("gst_pct") or 0)
    net_val = float(data.get("total_net_amount") or 0)
    if data.get("gst_amount") is None and net_val > 0 and gst_p > 0:
        data["gst_amount"] = round(net_val * gst_p / 100.0, 2)

    gst_val = float(data.get("gst_amount") or 0)
    if data.get("total_gross_amount") is None and net_val > 0:
        data["total_gross_amount"] = round(net_val + gst_val, 2)

    if data.get("total_amount") is None:
        data["total_amount"] = data.get("total_gross_amount") or net_val

    rec = BidDocumentSte(**{k: v for k, v in data.items() if hasattr(BidDocumentSte, k)})
    rec.status = status_val
    rec.form_code = form_code_val

    if not rec.remark and remarks_data:
        if isinstance(remarks_data, list) and remarks_data:
            first_rem = remarks_data[0]
            rec.remark = first_rem.get("remark") if isinstance(first_rem, dict) else str(first_rem)
        elif isinstance(remarks_data, str):
            rec.remark = remarks_data

    for it in items_data:
        q = it.get("quantity")
        p = it.get("unit_price")
        tot = it.get("total_amount")
        if tot is None and p is not None and q is not None:
            tot = float(p) * float(q)
        rec.items.append(BidDocumentSteItem(
            sr_no=it.get("sr_no"),
            description=it.get("description", "") or it.get("material_name", ""),
            material_name=it.get("material_name") or it.get("description", ""),
            hsn_sac=it.get("hsn_sac"),
            quantity=q,
            unit_price=p,
            total_amount=tot,
        ))

    db.session.add(rec)
    db.session.flush()

    _save_attachments(files, "bid_document_ste", rec.id, user_id)
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_34_BID_DOC_STE", "FORM_34_BID_DOCUMENT_STE"],
        default=34,
    )
    _save_remarks(rec.project_id, step_num, rec.id, remarks_data, user_id)
    if step_num != 34:
        _save_remarks(rec.project_id, 34, rec.id, remarks_data, user_id)
    db.session.commit()

    serialized = _serialize_bid_doc_ste(rec)
    _sync_step(rec.project_id, form_code_val, status_val, serialized)
    return jsonify(serialized), 201


def handle_get_latest_bid_doc_ste(args=None):
    if args is None:
        args = {}
    project_id = (
        args.get("project_id")
        or request.args.get("project_id")
        or request.args.get("projectId")
    )
    query = BidDocumentSte.query
    if project_id is not None:
        try:
            pid = int(project_id)
            if pid <= 0:
                return _error("INVALID_PROJECT_ID", "project_id must be a positive integer.", 400)
        except (ValueError, TypeError):
            return _error("INVALID_PROJECT_ID", "project_id must be an integer.", 400)

        project = db.session.get(Project, pid)
        if not project:
            return _error("PROJECT_NOT_FOUND", f"Project {pid} not found.", 404)
        query = query.filter_by(project_id=pid)

    rec = query.order_by(BidDocumentSte.id.desc()).first()
    if not rec:
        return _error("NOT_FOUND", "Bid document STE not found.", 404)

    return jsonify({
        "delivery_term": rec.delivery_terms,
        "gst_pct": float(rec.gst_pct) if rec.gst_pct is not None else None,
        "payment_terms": rec.payment_terms,
        "warranty_period": rec.warranty_period,
        "items": [
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
        ],
    }), 200


def handle_get_bid_doc_ste(rec_id=None):
    if request.args.get("latest") in ("true", "1"):
        return handle_get_latest_bid_doc_ste()
    if rec_id is not None:
        rec = db.session.get(BidDocumentSte, rec_id)
        if not rec:
            return _error("NOT_FOUND", f"BidDocumentSte {rec_id} not found.", 404)
        return jsonify(_serialize_bid_doc_ste(rec)), 200

    project_id = request.args.get("project_id", type=int)
    q = BidDocumentSte.query
    if project_id:
        q = q.filter_by(project_id=project_id)







    records = q.order_by(BidDocumentSte.id.desc()).all()
    return jsonify([_serialize_bid_doc_ste(r) for r in records]), 200


def handle_update_bid_doc_ste(rec_id: int):
    user_id = _get_user_id()
    rec = db.session.get(BidDocumentSte, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"BidDocumentSte {rec_id} not found.", 404)

    try:
        raw_payload, files = _extract_payload_and_files()
        data = BidDocumentSteUpdateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    items_data = data.pop("items", None) if "items" in data else (data.pop("requirements", None) if "requirements" in data else None)
    data.pop("requirements", None)
    remarks_data = raw_payload.get("remarks") if "remarks" in raw_payload else (data.pop("remarks", None) if "remarks" in data else data.get("remark"))
    data.pop("remarks", None)
    data.pop("remark", None)
    status_val = data.pop("status", None) or raw_payload.get("status")
    form_code_val = raw_payload.get("form_code") or data.pop("form_code", None)
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

    if "delivery_term" in data and not data.get("delivery_terms"):
        data["delivery_terms"] = data.pop("delivery_term")
    else:
        data.pop("delivery_term", None)

    if "payment_term" in data and not data.get("payment_terms"):
        data["payment_terms"] = data.pop("payment_term")
    else:
        data.pop("payment_term", None)

    if data.get("gst_pct") is None:
        if data.get("gst_rate") is not None:
            data["gst_pct"] = data.pop("gst_rate")
        elif data.get("gst_rate_pct") is not None:
            data["gst_pct"] = data.pop("gst_rate_pct")
    data.pop("gst_rate", None)
    data.pop("gst_rate_pct", None)

    for k, v in data.items():
        if hasattr(rec, k):
            setattr(rec, k, v)
    if status_val:
        rec.status = status_val
    if form_code_val:
        rec.form_code = form_code_val

    if remarks_data:
        if isinstance(remarks_data, list) and remarks_data:
            first_rem = remarks_data[0]
            rec.remark = first_rem.get("remark") if isinstance(first_rem, dict) else str(first_rem)
        elif isinstance(remarks_data, str):
            rec.remark = remarks_data

    if items_data is not None:
        rec.items.clear()
        calc_net = 0.0
        for it in items_data:
            q = it.get("quantity")
            p = it.get("unit_price")
            tot = it.get("total_amount")
            if tot is None and p is not None and q is not None:
                tot = float(p) * float(q)
            if tot:
                calc_net += float(tot)
            rec.items.append(BidDocumentSteItem(
                sr_no=it.get("sr_no"),
                description=it.get("description", "") or it.get("material_name", ""),
                material_name=it.get("material_name") or it.get("description", ""),
                hsn_sac=it.get("hsn_sac"),
                quantity=q,
                unit_price=p,
                total_amount=tot,
            ))
        if "total_net_amount" not in data and calc_net > 0:
            rec.total_net_amount = calc_net

    _save_attachments(files, "bid_document_ste", rec.id, user_id)
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_34_BID_DOC_STE", "FORM_34_BID_DOCUMENT_STE"],
        default=34,
    )
    _save_remarks(rec.project_id, step_num, rec.id, remarks_data, user_id)
    if step_num != 34:
        _save_remarks(rec.project_id, 34, rec.id, remarks_data, user_id)
    db.session.commit()

    serialized = _serialize_bid_doc_ste(rec)
    _sync_step(rec.project_id, rec.form_code or "FORM_34_BID_DOC_STE", rec.status, serialized)
    return jsonify(serialized), 200


def handle_delete_bid_doc_ste(rec_id: int):
    rec = db.session.get(BidDocumentSte, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"BidDocumentSte {rec_id} not found.", 404)
    project_id = rec.project_id
    atts = list_attachments(entity_type="bid_document_ste", entity_id=rec_id)
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
    return jsonify({"success": True, "message": "Bid Document STE deleted successfully."}), 200


# Wire routes to blueprints
for bp in (bid_document_ste_bp, bid_document_stes_bp, bid_document_for_ste_bp):
    bp.route("/latest", methods=["GET"])(
        bp.doc(
            security=[{"BearerAuth": []}],
            summary="Get Latest Bid Document STE",
            description="Retrieve only delivery_term, gst_pct, payment_terms, warranty_period, and items for the latest bid document STE.",
        )(
            bp.arguments(LatestBidDocumentSteQuerySchema, location="query")(
                bp.response(200, LatestBidDocumentSteResponseSchema)(
                    jwt_required()(handle_get_latest_bid_doc_ste)
                )
            )
        )
    )
    bp.route("", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_get_bid_doc_ste)))
    bp.route("/<int:rec_id>", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_get_bid_doc_ste)))
    bp.route("", methods=["POST"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_create_bid_doc_ste)))
    bp.route("/<int:rec_id>", methods=["PATCH", "PUT"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_update_bid_doc_ste)))
    bp.route("/<int:rec_id>", methods=["DELETE"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_delete_bid_doc_ste)))


# =========================================================================
# 5. FORM_35_ICB (INTERNATIONAL COMPETITIVE BIDDING)
# =========================================================================
def _serialize_international_competitive_bidding(rec):
    atts = _serialize_attachments("international_competitive_bidding", rec.id)
    if not atts:
        atts = _serialize_attachments("icb", rec.id)

    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_35_ICB", "FORM_35_INTERNATIONAL_COMPETITIVE_BIDDING"],
        default=35,
    )
    remarks = get_step_remarks_for_response(
        rec.project_id,
        step_num,
        fallback_raw=rec.remark,
        entity_id=rec.id,
    )
    if not remarks and step_num != 35:
        remarks = get_step_remarks_for_response(
            rec.project_id,
            35,
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
        "pqb_number": rec.pqb_no,
        "tender_title": rec.tender_title,
        "tender_no": rec.tender_no,
        "tender_number": rec.tender_no,
        "tender_enquiry_no": rec.tender_no,
        "icb_no": rec.tender_no,
        "tender_issue_date": rec.tender_issue_date.isoformat() if rec.tender_issue_date else None,
        "bid_submission_due_date_time": rec.bid_submission_due_date_time.isoformat() if rec.bid_submission_due_date_time else None,
        "bid_opening_date_time": rec.bid_opening_date_time.isoformat() if rec.bid_opening_date_time else None,
        "tender_fee": float(rec.tender_fee) if rec.tender_fee is not None else None,
        "emd": float(rec.emd) if rec.emd is not None else None,
        "tender_validity": rec.tender_validity,
        "validity": rec.tender_validity,
        "remark": rec.remark,
        "remarks": remarks,
        "items": items,
        "requirements": items,
        "attachments": atts,
        "attachments_count": len(atts),
        "status": rec.status or "completed",
        "form_code": rec.form_code or "FORM_35_ICB",
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


def handle_create_international_competitive_bidding():
    user_id = _get_user_id()
    try:
        raw_payload, files = _extract_payload_and_files()
        data = InternationalCompetitiveBiddingCreateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    project = db.session.get(Project, data["project_id"])
    if not project:
        return _error("PROJECT_NOT_FOUND", f"Project {data['project_id']} not found.", 404)

    items_data = data.pop("items", None) or data.pop("requirements", None) or []
    data.pop("requirements", None)
    remarks_data = raw_payload.get("remarks") or data.pop("remarks", None) or data.get("remark") or raw_payload.get("remark")
    data.pop("remarks", None)
    data.pop("remark", None)
    status_val = data.pop("status", None) or raw_payload.get("status") or "completed"
    form_code_val = raw_payload.get("form_code") or data.pop("form_code", None) or "FORM_35_ICB"
    data.pop("attachments_count", None)
    data.pop("form_code", None)

    # Normalize aliases
    if not data.get("tender_no"):
        for alias in ("icb_no", "tender_number", "tender_enquiry_no"):
            if data.get(alias):
                data["tender_no"] = data.pop(alias)
                break
    for alias in ("icb_no", "tender_number", "tender_enquiry_no"):
        data.pop(alias, None)

    if not data.get("pqb_no") and data.get("pqb_number"):
        data["pqb_no"] = data.pop("pqb_number")
    data.pop("pqb_number", None)

    if not data.get("tender_validity") and data.get("validity"):
        data["tender_validity"] = data.pop("validity")
    data.pop("validity", None)

    if not data.get("bid_submission_due_date_time"):
        for alias in ("submission_due_date_time", "bid_submission_due_date"):
            if data.get(alias):
                data["bid_submission_due_date_time"] = data.pop(alias)
                break
    data.pop("submission_due_date_time", None)
    data.pop("bid_submission_due_date", None)

    if not data.get("bid_opening_date_time") and data.get("opening_date_time"):
        data["bid_opening_date_time"] = data.pop("opening_date_time")
    data.pop("opening_date_time", None)

    rec = InternationalCompetitiveBidding(**{k: v for k, v in data.items() if hasattr(InternationalCompetitiveBidding, k)})
    rec.status = status_val
    rec.form_code = form_code_val

    if not rec.remark and remarks_data:
        if isinstance(remarks_data, list) and remarks_data:
            first_rem = remarks_data[0]
            rec.remark = first_rem.get("remark") if isinstance(first_rem, dict) else str(first_rem)
        elif isinstance(remarks_data, str):
            rec.remark = remarks_data

    for it in items_data:
        rec.items.append(InternationalCompetitiveBiddingItem(
            sr_no=it.get("sr_no"),
            description=it.get("description", "") or it.get("material_name", ""),
            material_name=it.get("material_name") or it.get("description", ""),
            unit=it.get("unit"),
            quantity=it.get("quantity"),
        ))

    db.session.add(rec)
    db.session.flush()

    _save_attachments(files, "international_competitive_bidding", rec.id, user_id)
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_35_ICB", "FORM_35_INTERNATIONAL_COMPETITIVE_BIDDING"],
        default=35,
    )
    _save_remarks(rec.project_id, step_num, rec.id, remarks_data, user_id)
    if step_num != 35:
        _save_remarks(rec.project_id, 35, rec.id, remarks_data, user_id)
    db.session.commit()

    serialized = _serialize_international_competitive_bidding(rec)
    _sync_step(rec.project_id, form_code_val, status_val, serialized)
    return jsonify(serialized), 201


def handle_get_latest_international_competitive_bidding(args=None):
    if args is None:
        args = {}
    project_id = (
        args.get("project_id")
        or request.args.get("project_id")
        or request.args.get("projectId")
    )
    query = InternationalCompetitiveBidding.query
    if project_id is not None:
        try:
            pid = int(project_id)
            if pid <= 0:
                return _error("INVALID_PROJECT_ID", "project_id must be a positive integer.", 400)
        except (ValueError, TypeError):
            return _error("INVALID_PROJECT_ID", "project_id must be an integer.", 400)

        project = db.session.get(Project, pid)
        if not project:
            return _error("PROJECT_NOT_FOUND", f"Project {pid} not found.", 404)
        query = query.filter_by(project_id=pid)

    rec = query.order_by(InternationalCompetitiveBidding.id.desc()).first()
    if not rec:
        return _error("NOT_FOUND", "International competitive bidding not found.", 404)

    return jsonify({
        "tender_title": rec.tender_title,
        "tender_enquiry_no": rec.tender_no or rec.tender_number,
    }), 200


def handle_get_international_competitive_bidding(rec_id=None):
    if request.args.get("latest") in ("true", "1"):
        return handle_get_latest_international_competitive_bidding()
    if rec_id is not None:
        rec = db.session.get(InternationalCompetitiveBidding, rec_id)
        if not rec:
            return _error("NOT_FOUND", f"InternationalCompetitiveBidding {rec_id} not found.", 404)
        return jsonify(_serialize_international_competitive_bidding(rec)), 200

    project_id = request.args.get("project_id", type=int)
    q = InternationalCompetitiveBidding.query
    if project_id:
        q = q.filter_by(project_id=project_id)







    records = q.order_by(InternationalCompetitiveBidding.id.desc()).all()
    return jsonify([_serialize_international_competitive_bidding(r) for r in records]), 200


def handle_update_international_competitive_bidding(rec_id: int):
    user_id = _get_user_id()
    rec = db.session.get(InternationalCompetitiveBidding, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"InternationalCompetitiveBidding {rec_id} not found.", 404)

    try:
        raw_payload, files = _extract_payload_and_files()
        data = InternationalCompetitiveBiddingUpdateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    items_data = data.pop("items", None) if "items" in data else (data.pop("requirements", None) if "requirements" in data else None)
    data.pop("requirements", None)
    remarks_data = raw_payload.get("remarks") if "remarks" in raw_payload else (data.pop("remarks", None) if "remarks" in data else data.get("remark"))
    data.pop("remarks", None)
    data.pop("remark", None)
    status_val = data.pop("status", None) or raw_payload.get("status")
    form_code_val = raw_payload.get("form_code") or data.pop("form_code", None)
    data.pop("attachments_count", None)
    data.pop("form_code", None)

    if not data.get("tender_no"):
        for alias in ("icb_no", "tender_number", "tender_enquiry_no"):
            if data.get(alias):
                data["tender_no"] = data.pop(alias)
                break
    for alias in ("icb_no", "tender_number", "tender_enquiry_no"):
        data.pop(alias, None)

    if "pqb_number" in data and not data.get("pqb_no"):
        data["pqb_no"] = data.pop("pqb_number")
    data.pop("pqb_number", None)

    if "validity" in data and not data.get("tender_validity"):
        data["tender_validity"] = data.pop("validity")
    data.pop("validity", None)

    if not data.get("bid_submission_due_date_time"):
        for alias in ("submission_due_date_time", "bid_submission_due_date"):
            if data.get(alias):
                data["bid_submission_due_date_time"] = data.pop(alias)
                break
    data.pop("submission_due_date_time", None)
    data.pop("bid_submission_due_date", None)

    if not data.get("bid_opening_date_time") and data.get("opening_date_time"):
        data["bid_opening_date_time"] = data.pop("opening_date_time")
    data.pop("opening_date_time", None)

    for k, v in data.items():
        if hasattr(rec, k):
            setattr(rec, k, v)
    if status_val:
        rec.status = status_val
    if form_code_val:
        rec.form_code = form_code_val

    if remarks_data:
        if isinstance(remarks_data, list) and remarks_data:
            first_rem = remarks_data[0]
            rec.remark = first_rem.get("remark") if isinstance(first_rem, dict) else str(first_rem)
        elif isinstance(remarks_data, str):
            rec.remark = remarks_data

    if items_data is not None:
        rec.items.clear()
        for it in items_data:
            rec.items.append(InternationalCompetitiveBiddingItem(
                sr_no=it.get("sr_no"),
                description=it.get("description", "") or it.get("material_name", ""),
                material_name=it.get("material_name") or it.get("description", ""),
                unit=it.get("unit"),
                quantity=it.get("quantity"),
            ))

    _save_attachments(files, "international_competitive_bidding", rec.id, user_id)
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_35_ICB", "FORM_35_INTERNATIONAL_COMPETITIVE_BIDDING"],
        default=35,
    )
    _save_remarks(rec.project_id, step_num, rec.id, remarks_data, user_id)
    if step_num != 35:
        _save_remarks(rec.project_id, 35, rec.id, remarks_data, user_id)
    db.session.commit()

    serialized = _serialize_international_competitive_bidding(rec)
    _sync_step(rec.project_id, rec.form_code or "FORM_35_ICB", rec.status, serialized)
    return jsonify(serialized), 200


def handle_delete_international_competitive_bidding(rec_id: int):
    rec = db.session.get(InternationalCompetitiveBidding, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"InternationalCompetitiveBidding {rec_id} not found.", 404)
    project_id = rec.project_id
    atts = list_attachments(entity_type="international_competitive_bidding", entity_id=rec_id)
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
    return jsonify({"success": True, "message": "International Competitive Bidding deleted successfully."}), 200


# Wire routes to ICB blueprints
for bp in (international_competitive_biddings_bp, international_competitive_bidding_bp, icb_bp, icbs_bp):
    bp.route("/latest", methods=["GET"])(
        bp.doc(
            security=[{"BearerAuth": []}],
            summary="Get Latest International Competitive Bidding (ICB)",
            description="Retrieve only tender_title and tender_enquiry_no for the latest international competitive bidding.",
        )(
            bp.arguments(LatestInternationalCompetitiveBiddingQuerySchema, location="query")(
                bp.response(200, LatestInternationalCompetitiveBiddingResponseSchema)(
                    jwt_required()(handle_get_latest_international_competitive_bidding)
                )
            )
        )
    )
    bp.route("", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_get_international_competitive_bidding)))
    bp.route("/<int:rec_id>", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_get_international_competitive_bidding)))
    bp.route("", methods=["POST"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_create_international_competitive_bidding)))
    bp.route("/<int:rec_id>", methods=["PATCH", "PUT"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_update_international_competitive_bidding)))
    bp.route("/<int:rec_id>", methods=["DELETE"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_delete_international_competitive_bidding)))


# =========================================================================
# 6. FORM_36_BID_DOC_ICB (BID DOCUMENT FOR ICB)
# =========================================================================
def _serialize_bid_doc_icb(rec):
    atts = _serialize_attachments("bid_document_icb", rec.id)
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_36_BID_DOC_ICB", "FORM_36_BID_DOCUMENT_ICB"],
        default=36,
    )
    remarks = get_step_remarks_for_response(
        rec.project_id,
        step_num,
        fallback_raw=rec.remark,
        entity_id=rec.id,
    )
    if not remarks and step_num != 36:
        remarks = get_step_remarks_for_response(
            rec.project_id,
            36,
            fallback_raw=rec.remark,
            entity_id=rec.id,
        )
    items = [
        {
            "id": it.id,
            "sr_no": it.sr_no,
            "description": it.description,
            "material_name": it.material_name or it.description,
            "item_code": it.item_code,
            "hsn_sac": it.hsn_sac,
            "hsn_code": it.hsn_sac,
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
        "payment_term": rec.payment_terms,
        "warranty_period": rec.warranty_period,
        "gst_pct": float(rec.gst_pct) if rec.gst_pct is not None else None,
        "gst_rate": float(rec.gst_pct) if rec.gst_pct is not None else None,
        "gst_rate_pct": float(rec.gst_pct) if rec.gst_pct is not None else None,
        "total_net_amount": float(rec.total_net_amount) if rec.total_net_amount is not None else None,
        "total_gross_amount": float(rec.total_gross_amount) if rec.total_gross_amount is not None else None,
        "gst_amount": float(rec.gst_amount) if rec.gst_amount is not None else None,
        "total_amount": float(rec.total_amount) if rec.total_amount is not None else None,
        "remark": rec.remark,
        "remarks": remarks,
        "items": items,
        "attachments": atts,
        "attachments_count": len(atts),
        "status": rec.status or "completed",
        "form_code": rec.form_code or "FORM_36_BID_DOC_ICB",
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


def handle_create_bid_doc_icb():
    user_id = _get_user_id()
    try:
        raw_payload, files = _extract_payload_and_files()
        data = BidDocumentIcbCreateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    project = db.session.get(Project, data["project_id"])
    if not project:
        return _error("PROJECT_NOT_FOUND", f"Project {data['project_id']} not found.", 404)

    items_data = data.pop("items", None) or data.pop("requirements", None) or []
    data.pop("requirements", None)
    remarks_data = raw_payload.get("remarks") or data.pop("remarks", None) or data.get("remark") or raw_payload.get("remark")
    data.pop("remarks", None)
    data.pop("remark", None)
    data.pop("form_code", None)
    status_val = data.pop("status", None) or raw_payload.get("status") or "completed"
    form_code_val = raw_payload.get("form_code") or data.pop("form_code", None) or "FORM_36_BID_DOC_ICB"
    data.pop("attachments_count", None)

    # Normalize aliases
    if "tender_number" in data and not data.get("tender_no"):
        data["tender_no"] = data.pop("tender_number")
    else:
        data.pop("tender_number", None)

    if "total_corrigendum_issued" in data and data.get("total_no_corrigendum_issued") is None:
        data["total_no_corrigendum_issued"] = data.pop("total_corrigendum_issued")
    else:
        data.pop("total_corrigendum_issued", None)

    if "delivery_term" in data and not data.get("delivery_terms"):
        data["delivery_terms"] = data.pop("delivery_term")
    else:
        data.pop("delivery_term", None)

    if "payment_term" in data and not data.get("payment_terms"):
        data["payment_terms"] = data.pop("payment_term")
    else:
        data.pop("payment_term", None)

    if data.get("gst_pct") is None:
        if data.get("gst_rate") is not None:
            data["gst_pct"] = data.pop("gst_rate")
        elif data.get("gst_rate_pct") is not None:
            data["gst_pct"] = data.pop("gst_rate_pct")
    data.pop("gst_rate", None)
    data.pop("gst_rate_pct", None)

    # Calculate item amounts and auto-calculate totals if not supplied
    calc_net = 0.0
    for it in items_data:
        q = float(it.get("quantity") or 0)
        p = float(it.get("unit_price") or 0)
        tot = float(it.get("total_amount") or (q * p if q and p else 0))
        calc_net += tot

    if data.get("total_net_amount") is None and calc_net > 0:
        data["total_net_amount"] = calc_net

    gst_p = float(data.get("gst_pct") or 0)
    net_val = float(data.get("total_net_amount") or 0)
    if data.get("gst_amount") is None and net_val > 0 and gst_p > 0:
        data["gst_amount"] = round(net_val * gst_p / 100.0, 2)

    gst_val = float(data.get("gst_amount") or 0)
    if data.get("total_gross_amount") is None and net_val > 0:
        data["total_gross_amount"] = round(net_val + gst_val, 2)

    if data.get("total_amount") is None:
        data["total_amount"] = data.get("total_gross_amount") or net_val

    rec = BidDocumentIcb(**{k: v for k, v in data.items() if hasattr(BidDocumentIcb, k)})
    rec.status = status_val
    rec.form_code = form_code_val

    if not rec.remark and remarks_data:
        if isinstance(remarks_data, list) and remarks_data:
            first_rem = remarks_data[0]
            rec.remark = first_rem.get("remark") if isinstance(first_rem, dict) else str(first_rem)
        elif isinstance(remarks_data, str):
            rec.remark = remarks_data

    for it in items_data:
        q = it.get("quantity")
        p = it.get("unit_price")
        tot = it.get("total_amount")
        if tot is None and p is not None and q is not None:
            tot = float(p) * float(q)
        rec.items.append(BidDocumentIcbItem(
            sr_no=it.get("sr_no"),
            description=it.get("description", "") or it.get("material_name", ""),
            material_name=it.get("material_name") or it.get("description", ""),
            item_code=it.get("item_code"),
            hsn_sac=it.get("hsn_sac") or it.get("hsn_code"),
            quantity=q,
            unit_price=p,
            total_amount=tot,
        ))

    db.session.add(rec)
    db.session.flush()

    _save_attachments(files, "bid_document_icb", rec.id, user_id)
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_36_BID_DOC_ICB", "FORM_36_BID_DOCUMENT_ICB"],
        default=36,
    )
    _save_remarks(rec.project_id, step_num, rec.id, remarks_data, user_id)
    if step_num != 36:
        _save_remarks(rec.project_id, 36, rec.id, remarks_data, user_id)
    db.session.commit()

    serialized = _serialize_bid_doc_icb(rec)
    _sync_step(rec.project_id, form_code_val, status_val, serialized)
    return jsonify(serialized), 201


def handle_get_bid_doc_icb(rec_id=None):
    if rec_id is not None:
        rec = db.session.get(BidDocumentIcb, rec_id)
        if not rec:
            return _error("NOT_FOUND", f"BidDocumentIcb {rec_id} not found.", 404)
        return jsonify(_serialize_bid_doc_icb(rec)), 200

    project_id = request.args.get("project_id", type=int)
    q = BidDocumentIcb.query
    if project_id:
        q = q.filter_by(project_id=project_id)







    records = q.order_by(BidDocumentIcb.id.desc()).all()
    return jsonify([_serialize_bid_doc_icb(r) for r in records]), 200


def handle_update_bid_doc_icb(rec_id: int):
    user_id = _get_user_id()
    rec = db.session.get(BidDocumentIcb, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"BidDocumentIcb {rec_id} not found.", 404)

    try:
        raw_payload, files = _extract_payload_and_files()
        data = BidDocumentIcbUpdateSchema().load(raw_payload)
    except ValidationError as err:
        return _error("VALIDATION_ERROR", err.messages, 422)

    items_data = data.pop("items", None) if "items" in data else (data.pop("requirements", None) if "requirements" in data else None)
    data.pop("requirements", None)
    remarks_data = raw_payload.get("remarks") if "remarks" in raw_payload else (data.pop("remarks", None) if "remarks" in data else data.get("remark"))
    data.pop("remarks", None)
    data.pop("remark", None)
    status_val = data.pop("status", None) or raw_payload.get("status")
    form_code_val = raw_payload.get("form_code") or data.pop("form_code", None)
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

    if "delivery_term" in data and not data.get("delivery_terms"):
        data["delivery_terms"] = data.pop("delivery_term")
    else:
        data.pop("delivery_term", None)

    if "payment_term" in data and not data.get("payment_terms"):
        data["payment_terms"] = data.pop("payment_term")
    else:
        data.pop("payment_term", None)

    if data.get("gst_pct") is None:
        if data.get("gst_rate") is not None:
            data["gst_pct"] = data.pop("gst_rate")
        elif data.get("gst_rate_pct") is not None:
            data["gst_pct"] = data.pop("gst_rate_pct")
    data.pop("gst_rate", None)
    data.pop("gst_rate_pct", None)

    for k, v in data.items():
        if hasattr(rec, k):
            setattr(rec, k, v)
    if status_val:
        rec.status = status_val
    if form_code_val:
        rec.form_code = form_code_val

    if remarks_data:
        if isinstance(remarks_data, list) and remarks_data:
            first_rem = remarks_data[0]
            rec.remark = first_rem.get("remark") if isinstance(first_rem, dict) else str(first_rem)
        elif isinstance(remarks_data, str):
            rec.remark = remarks_data

    if items_data is not None:
        rec.items.clear()
        for it in items_data:
            q = it.get("quantity")
            p = it.get("unit_price")
            tot = it.get("total_amount")
            if tot is None and p is not None and q is not None:
                tot = float(p) * float(q)
            rec.items.append(BidDocumentIcbItem(
                sr_no=it.get("sr_no"),
                description=it.get("description", "") or it.get("material_name", ""),
                material_name=it.get("material_name") or it.get("description", ""),
                item_code=it.get("item_code"),
                hsn_sac=it.get("hsn_sac") or it.get("hsn_code"),
                quantity=q,
                unit_price=p,
                total_amount=tot,
            ))

    _save_attachments(files, "bid_document_icb", rec.id, user_id)
    step_num = _get_step_num_for_form(
        rec.project_id,
        ["FORM_36_BID_DOC_ICB", "FORM_36_BID_DOCUMENT_ICB"],
        default=36,
    )
    _save_remarks(rec.project_id, step_num, rec.id, remarks_data, user_id)
    if step_num != 36:
        _save_remarks(rec.project_id, 36, rec.id, remarks_data, user_id)
    db.session.commit()

    serialized = _serialize_bid_doc_icb(rec)
    _sync_step(rec.project_id, rec.form_code or "FORM_36_BID_DOC_ICB", rec.status, serialized)
    return jsonify(serialized), 200


def handle_delete_bid_doc_icb(rec_id: int):
    rec = db.session.get(BidDocumentIcb, rec_id)
    if not rec:
        return _error("NOT_FOUND", f"BidDocumentIcb {rec_id} not found.", 404)
    project_id = rec.project_id
    atts = list_attachments(entity_type="bid_document_icb", entity_id=rec_id)
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
    return jsonify({"success": True, "message": "Bid Document ICB deleted successfully."}), 200


# Wire routes to Bid Document ICB blueprints
for bp in (bid_document_icb_bp, bid_document_icbs_bp, bid_document_for_icb_bp):
    bp.route("", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_get_bid_doc_icb)))
    bp.route("/<int:rec_id>", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_get_bid_doc_icb)))
    bp.route("", methods=["POST"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_create_bid_doc_icb)))
    bp.route("/<int:rec_id>", methods=["PATCH", "PUT"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_update_bid_doc_icb)))
    bp.route("/<int:rec_id>", methods=["DELETE"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(handle_delete_bid_doc_icb)))

