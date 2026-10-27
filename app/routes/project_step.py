from datetime import datetime

from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from app.extensions.database import db
from app.models import (
    Attachment,
    FormDefinition,
    Project,
    ProjectStep,
    StepRemark,
    User,
)
from app.schemas.project_step import (
    FormDefinitionResponseSchema,
    ProjectStepAttachSchema,
    ProjectStepAttachmentResponseSchema,
    ProjectStepRemarkCreateSchema,
    ProjectStepResponseSchema,
    ProjectStepUpdateSchema,
)
from app.services.attachment_service import (
    AttachmentValidationError,
    create_attachment,
)
from app.services.project_step_service import (
    ProjectNotFoundError,
    ProjectStepNotFoundError,
)


project_step_bp = Blueprint(
    "project_steps",
    __name__,
    url_prefix="/api/v1",
    description="Dynamic 28-Form Workflow System APIs",
)

project_step_v2_bp = Blueprint(
    "project_steps_v2",
    __name__,
    url_prefix="/api/v2",
    description="Dynamic 28-Form Workflow System APIs (v2)",
)


def _get_current_user_info():
    try:
        jwt_identity = get_jwt_identity()
        if jwt_identity and str(jwt_identity).isdigit():
            user = db.session.get(User, int(jwt_identity))
            if user:
                name = user.full_name or user.username or "User"
                return int(jwt_identity), name
        return None, "User"
    except Exception:
        return None, "User"


# =========================================================================
# 1. GET ALL 28 FORM DEFINITIONS (CATALOG)
# =========================================================================
def handle_get_forms():
    forms = (
        FormDefinition.query.filter_by(is_active=True)
        .order_by(FormDefinition.id.asc())
        .all()
    )
    return [f.to_dict() for f in forms], 200


def handle_get_form_by_code(form_code: str):
    form_def = FormDefinition.query.filter_by(
        form_code=form_code, is_active=True
    ).first()
    if not form_def:
        return {
            "success": False,
            "error": {
                "code": "FORM_NOT_FOUND",
                "message": f"Form with code '{form_code}' not found.",
            },
        }, 404
    return form_def.to_dict(), 200


# =========================================================================
# =========================================================================
# 2. FORM RELATIONSHIP MAPPING
# =========================================================================
FORM_REL_MAP = [
    ("FORM_01_PQB", "pre_qualification_bids"),
    ("FORM_02_PQB_BID_DOCUMENT", "pqb_bid_documents"),
    ("FORM_03_CORRIGENDUM", "corrigendums"),
    ("FORM_04_LTE", "limited_tender_enquiries"),
    ("FORM_05_NAC", "notification_awards"),
    ("FORM_06_CONSULTANCY_INVOICE", "consultancy_invoices"),
    ("FORM_07_EOI", "expressions_of_interest"),
    ("FORM_08_CUSTOMER_QUERY", "customer_queries"),
    ("FORM_09_RFQ", "quotation_requests"),
    ("FORM_10_COST_SHEET", "cost_sheets"),
    ("FORM_11_SUPPLIER_QUOTATION", "supplier_quotations"),
    ("FORM_12_CUSTOMER_QUOTATION", "customer_quotations"),
    ("FORM_13_PAC_TENDER", "customer_tenders"),
    ("FORM_14_PURCHASE_ORDER", "purchase_orders"),
    ("FORM_15_BID_DOCUMENT", "bid_submissions"),
    ("FORM_16_ORDER_CONFIRMATION", "supplier_order_confirmations"),
    ("FORM_17_PROFORMA_INVOICE", "supplier_proforma_invoices"),
    ("FORM_18_SUPPLIER_INVOICE", "supplier_invoices"),
    ("FORM_19_SUPPLIER_PACKING_LIST", "supplier_packing_lists"),
    ("FORM_20_PAYMENT_TO_SUPPLIER", "supplier_payments"),
    ("FORM_21_TRANSPORTATION_DETAILS", ["import_logistics", "transport_details"]),
    ("FORM_22_PAYMENT_FROM_CUSTOMER", "customer_payments"),
    ("FORM_23_WARRANTY_CERTIFICATE", "warranty_certificates"),
    ("FORM_24_DELIVERY_CHALLAN", "delivery_challans"),
    ("FORM_25_CUSTOMER_PACKING_LIST", "customer_delivery_packing_lists"),
    ("FORM_26_TAX_INVOICE_CUSTOMER", "customer_delivery_invoices"),
    ("FORM_27_SHIPPING_CLEARANCE", "bills_of_entry"),
    ("FORM_28_FREIGHT_CHA", "customs_clearances"),
]
FORM_REL_DICT = dict(FORM_REL_MAP)


# =========================================================================
# 2. GET CURRENT STEPS FOR A PROJECT (TIMELINE OVERVIEW)
# =========================================================================
def sync_project_steps_from_records(project):
    """
    Ensures that any forms created directly via their dedicated REST endpoints
    are reflected as completed steps in the project_steps table for this project.
    """
    form_rel_map = FORM_REL_MAP

    existing_steps = {s.form_code: s for s in project.steps if s.form_code}
    max_order = max([s.step_order or s.step_number or 0 for s in project.steps], default=0)
    max_step_num = max([s.step_number or 0 for s in project.steps], default=0)
    changed = False
    deleted_any = False

    try:
        form_defs = {f.form_code: f for f in FormDefinition.query.filter_by(is_active=True).all()}
    except Exception:
        form_defs = {}

    for form_code, attrs in form_rel_map:
        has_record = False
        if isinstance(attrs, list):
            has_record = any(bool(getattr(project, a, None)) for a in attrs)
        else:
            has_record = bool(getattr(project, attrs, None))

        if has_record:
            if form_code in existing_steps:
                step = existing_steps[form_code]
                step_data = dict(step.data or {}) if isinstance(step.data, dict) else {}
                step_data["_synced_from_record"] = True
                step.data = step_data
                if step.status != "completed" or step.progress_percentage != 100:
                    step.status = "completed"
                    step.progress_percentage = 100
                    if not step.completed_at:
                        step.completed_at = datetime.utcnow()
                    changed = True
            else:
                fdef = form_defs.get(form_code)
                max_order += 1
                max_step_num = max(max_order, max_step_num) + 1
                new_step = ProjectStep(
                    project_id=project.id,
                    step_order=max_order,
                    step_number=max_step_num,
                    form_code=form_code,
                    step_name=fdef.name if fdef else form_code,
                    description=fdef.description if fdef else "",
                    status="completed",
                    progress_percentage=100,
                    completed_at=datetime.utcnow(),
                    data={"_auto_created": True, "_synced_from_record": True},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.session.add(new_step)
                existing_steps[form_code] = new_step
                changed = True
        else:
            if form_code in existing_steps:
                step = existing_steps[form_code]
                step_data = dict(step.data or {}) if isinstance(step.data, dict) else {}
                # Do not revert if the step was explicitly completed by user via Step API
                if step_data.get("_manually_completed"):
                    continue

                if step_data.get("_auto_created"):
                    db.session.delete(step)
                    del existing_steps[form_code]
                    changed = True
                    deleted_any = True
                else:
                    if step.status == "completed" or (step.progress_percentage or 0) > 0:
                        step.progress_percentage = 0
                        step.completed_at = None
                        step_data.pop("_synced_from_record", None)
                        if step_data.get("_is_attached"):
                            step.status = "in_progress"
                            step.data = step_data
                        else:
                            step.status = "pending"
                            step.data = {}
                        changed = True

    if deleted_any:
        db.session.flush()
        remaining_steps = (
            ProjectStep.query.filter_by(project_id=project.id)
            .order_by(ProjectStep.step_order.asc(), ProjectStep.id.asc())
            .all()
        )
        for idx, s in enumerate(remaining_steps, start=1):
            if s.step_order != idx:
                s.step_order = idx
        project.updated_at = datetime.utcnow()
        db.session.commit()
    elif changed:
        project.updated_at = datetime.utcnow()
        db.session.commit()


def handle_get_project_steps(project_id: int):
    project = db.session.get(Project, project_id)
    if not project:
        return {
            "success": False,
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project with id {project_id} was not found.",
            },
        }, 404

    # Synchronize any filled records into project_steps
    sync_project_steps_from_records(project)

    steps = (
        ProjectStep.query.filter_by(project_id=project_id)
        .order_by(ProjectStep.step_order.asc(), ProjectStep.id.asc())
        .all()
    )
    return [s.to_dict() for s in steps], 200


# =========================================================================
# 3. ATTACH A NEW FORM AS A STEP (ON DEMAND)
# =========================================================================
def handle_add_project_step(*args, **kwargs):
    project_id = kwargs.get("project_id")
    payload = args[0] if (args and isinstance(args[0], dict)) else (kwargs.get("data") or request.get_json(silent=True) or {})

    project = db.session.get(Project, project_id)
    if not project:
        return {
            "success": False,
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project with id {project_id} was not found.",
            },
        }, 404

    form_code = payload.get("form_code")
    if not form_code:
        return {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "form_code is required.",
            },
        }, 400

    form_def = FormDefinition.query.filter_by(form_code=form_code).first()
    if not form_def:
        return {
            "success": False,
            "error": {
                "code": "INVALID_FORM_CODE",
                "message": f"Form definition '{form_code}' does not exist.",
            },
        }, 400

    step_name = payload.get("step_name") or form_def.name
    description = (
        payload.get("description")
        if payload.get("description") is not None
        else (form_def.description or "")
    )
    initial_data = payload.get("data") or {}
    if isinstance(initial_data, dict):
        initial_data["_is_attached"] = True

    # Compute next step_order and safe step_number
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
    next_order = max_order + 1
    next_step_num = max(next_order, max_step_num + 1)

    status = payload.get("status") or "in_progress"
    progress_percentage = (
        payload.get("progress_percentage")
        if payload.get("progress_percentage") is not None
        else (100 if status == "completed" else 0)
    )
    completed_at = datetime.utcnow() if status == "completed" else None
    if status == "completed":
        initial_data["_manually_completed"] = True

    new_step = ProjectStep(
        project_id=project_id,
        step_order=next_order,
        step_number=next_step_num,
        form_code=form_code,
        step_name=step_name,
        description=description,
        status=status,
        progress_percentage=progress_percentage,
        completed_at=completed_at,
        data=initial_data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(new_step)
    db.session.flush()

    if payload.get("remark"):
        user_id, default_user_name = _get_current_user_info()
        r_author = payload.get("user_name") or default_user_name
        r_obj = StepRemark(
            project_id=project_id,
            step_id=new_step.id,
            step_number=next_order,
            user_id=user_id,
            user_name=r_author,
            remark=str(payload["remark"]).strip(),
            created_at=datetime.utcnow(),
        )
        db.session.add(r_obj)

    # Recalculate project overall progress
    total_steps = ProjectStep.query.filter_by(project_id=project_id).count()
    completed = ProjectStep.query.filter_by(
        project_id=project_id, status="completed"
    ).count()
    project.updated_at = datetime.utcnow()

    db.session.commit()
    return new_step.to_dict(), 201


# =========================================================================
# 4. GET A SINGLE STEP BY ID
# =========================================================================
def handle_get_single_step(project_id: int, step_id: int):
    step = ProjectStep.query.filter_by(
        project_id=project_id, id=step_id
    ).first()
    if not step:
        return {
            "success": False,
            "error": {
                "code": "STEP_NOT_FOUND",
                "message": f"Step with id {step_id} was not found for project {project_id}.",
            },
        }, 404

    return step.to_dict(), 200


# =========================================================================
# 5. UPDATE STEP (SAVE DRAFT OR COMPLETE STEP)
# =========================================================================
def handle_update_step(*args, **kwargs):
    project_id = kwargs.get("project_id")
    step_id = kwargs.get("step_id")
    payload = args[0] if (args and isinstance(args[0], dict)) else (kwargs.get("data") or request.get_json(silent=True) or {})

    step = ProjectStep.query.filter_by(
        project_id=project_id, id=step_id
    ).first()
    if not step:
        return {
            "success": False,
            "error": {
                "code": "STEP_NOT_FOUND",
                "message": f"Step with id {step_id} was not found for project {project_id}.",
            },
        }, 404

    user_id, user_name = _get_current_user_info()

    current_data = dict(step.data or {}) if isinstance(step.data, dict) else {}
    if "data" in payload and payload["data"] is not None:
        if isinstance(payload["data"], dict):
            current_data.update(payload["data"])

    if "status" in payload and payload["status"] is not None:
        step.status = payload["status"]
        if step.status == "completed":
            if not step.completed_at:
                step.completed_at = datetime.utcnow()
            if "progress_percentage" not in payload:
                step.progress_percentage = 100
            current_data["_manually_completed"] = True
        elif step.status != "completed":
            step.completed_at = None
            current_data.pop("_manually_completed", None)

    step.data = current_data

    if (
        "progress_percentage" in payload
        and payload["progress_percentage"] is not None
    ):
        step.progress_percentage = payload["progress_percentage"]

    if "step_name" in payload and payload["step_name"]:
        step.step_name = payload["step_name"]

    if "description" in payload and payload["description"] is not None:
        step.description = payload["description"]

    if "remark" in payload and payload["remark"]:
        r_author = payload.get("user_name") or user_name
        r_obj = StepRemark(
            project_id=project_id,
            step_id=step.id,
            step_number=step.step_order or step.step_number or 1,
            user_id=user_id,
            user_name=r_author,
            remark=str(payload["remark"]).strip(),
            created_at=datetime.utcnow(),
        )
        db.session.add(r_obj)

    step.updated_at = datetime.utcnow()

    # Recalculate project progress
    project = db.session.get(Project, project_id)
    if project:
        project.updated_at = datetime.utcnow()

    db.session.commit()
    return step.to_dict(), 200


# =========================================================================
# 6. DELETE / REMOVE A STEP FROM PROJECT
# =========================================================================
def handle_delete_step(project_id: int, step_id: int):
    step = ProjectStep.query.filter_by(
        project_id=project_id, id=step_id
    ).first()
    if not step:
        return {
            "success": False,
            "error": {
                "code": "STEP_NOT_FOUND",
                "message": f"Step with id {step_id} was not found for project {project_id}.",
            },
        }, 404

    project = db.session.get(Project, project_id)
    form_code = step.form_code

    # 1. If this step corresponds to a form, delete all underlying form records for this project
    if form_code and project and form_code in FORM_REL_DICT:
        attrs = FORM_REL_DICT[form_code]
        attr_list = attrs if isinstance(attrs, list) else [attrs]
        for attr in attr_list:
            records = getattr(project, attr, [])
            if records:
                for rec in list(records):
                    # Clear any nullable foreign keys pointing to this record
                    try:
                        if hasattr(rec, "__tablename__"):
                            if rec.__tablename__ == "customer_tenders":
                                from app.models.bid_submission import BidSubmission
                                from app.models.purchase_order import PurchaseOrder
                                BidSubmission.query.filter_by(tender_id=rec.id).update({"tender_id": None})
                                PurchaseOrder.query.filter_by(tender_id=rec.id).update({"tender_id": None})
                            elif rec.__tablename__ == "purchase_orders":
                                from app.models.supplier_order_confirmation import SupplierOrderConfirmation
                                SupplierOrderConfirmation.query.filter_by(purchase_order_id=rec.id).update({"purchase_order_id": None})
                            elif rec.__tablename__ == "bills_of_entry":
                                from app.models.customs_clearance import CustomsClearance
                                CustomsClearance.query.filter_by(bill_of_entry_id=rec.id).update({"bill_of_entry_id": None})
                    except Exception:
                        pass

                    # Delete attachments and files for this record
                    try:
                        from app.models.attachment import Attachment
                        from app.services.storage import get_storage
                        storage = get_storage()
                        atts = Attachment.query.filter_by(entity_id=rec.id).all()
                        for att in atts:
                            try:
                                if storage.exists(att.storage_key):
                                    storage.delete(att.storage_key)
                            except Exception:
                                pass
                            db.session.delete(att)
                    except Exception:
                        pass

                    # Delete remarks for this entity
                    try:
                        from app.models.step_remark import StepRemark
                        StepRemark.query.filter_by(
                            project_id=project_id,
                            entity_id=rec.id,
                        ).delete(synchronize_session=False)
                    except Exception:
                        pass

                    db.session.delete(rec)

    # 2. Delete the step itself
    db.session.delete(step)
    db.session.flush()

    # 3. Reorder remaining steps
    remaining = (
        ProjectStep.query.filter_by(project_id=project_id)
        .order_by(ProjectStep.step_order.asc(), ProjectStep.id.asc())
        .all()
    )
    for idx, s in enumerate(remaining, start=1):
        if s.step_order != idx:
            s.step_order = idx

    if project:
        project.updated_at = datetime.utcnow()

    db.session.commit()
    return {"success": True, "message": "Step removed successfully"}, 200


# =========================================================================
# 7. UPLOAD ATTACHMENT FOR A STEP
# =========================================================================
def handle_upload_step_attachment(project_id: int, step_id: int):
    step = ProjectStep.query.filter_by(
        project_id=project_id, id=step_id
    ).first()
    if not step:
        return {
            "success": False,
            "error": {
                "code": "STEP_NOT_FOUND",
                "message": f"Step with id {step_id} was not found for project {project_id}.",
            },
        }, 404

    file = request.files.get("file")
    if not file:
        return {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "File is required.",
            },
        }, 400

    upload_key = request.form.get("upload_key")
    if not upload_key:
        return {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "upload_key is required.",
            },
        }, 400

    user_id, _ = _get_current_user_info()

    try:
        attachment, storage_key = create_attachment(
            file=file,
            entity_type="project_step",
            entity_id=step.id,
            uploaded_by=user_id or 1,
        )
        attachment.upload_key = upload_key.strip()
        db.session.commit()

        return attachment.to_dict(), 201

    except AttachmentValidationError as exc:
        return {
            "success": False,
            "error": {
                "code": "ATTACHMENT_VALIDATION_ERROR",
                "message": str(exc),
            },
        }, 400


# =========================================================================
# 8. ADD REMARK TO A STEP
# =========================================================================
def handle_add_step_remark(*args, **kwargs):
    project_id = kwargs.get("project_id")
    step_id = kwargs.get("step_id")
    payload = args[0] if (args and isinstance(args[0], dict)) else (kwargs.get("data") or request.get_json(silent=True) or {})

    step = ProjectStep.query.filter_by(
        project_id=project_id, id=step_id
    ).first()
    if not step:
        return {
            "success": False,
            "error": {
                "code": "STEP_NOT_FOUND",
                "message": f"Step with id {step_id} was not found for project {project_id}.",
            },
        }, 404

    remark_text = payload.get("remark")
    if not remark_text or not str(remark_text).strip():
        return {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "remark is required.",
            },
        }, 400

    user_id, default_user_name = _get_current_user_info()
    user_name = payload.get("user_name") or default_user_name

    new_remark = StepRemark(
        project_id=project_id,
        step_id=step.id,
        step_number=step.step_order or step.step_number or 1,
        user_id=user_id,
        user_name=user_name,
        remark=str(remark_text).strip(),
        created_at=datetime.utcnow(),
    )
    db.session.add(new_remark)
    db.session.commit()

    return new_remark.to_dict(), 201


# =========================================================================
# REGISTER ROUTES ON BOTH /api/v1 AND /api/v2 BLUEPRINTS
# =========================================================================
for bp in [project_step_bp, project_step_v2_bp]:
    bp.route("/forms", methods=["GET"])(
        bp.doc(
            summary="List 28 Form Definitions",
            description="Returns catalog metadata for all 28 forms available for attachment.",
            security=[{"BearerAuth": []}],
        )(
            bp.response(200, FormDefinitionResponseSchema(many=True))(
                jwt_required()(handle_get_forms)
            )
        )
    )

    bp.route("/forms/<string:form_code>", methods=["GET"])(
        bp.doc(
            summary="Get Form Definition by Code",
            description="Returns metadata for a specific form by form_code.",
            security=[{"BearerAuth": []}],
        )(
            bp.response(200, FormDefinitionResponseSchema)(
                jwt_required()(handle_get_form_by_code)
            )
        )
    )

    bp.route("/projects/<int:project_id>/steps", methods=["GET"])(
        bp.doc(
            summary="List Project Steps",
            description="Returns all active steps attached to this project, ordered by step_order ASC.",
            security=[{"BearerAuth": []}],
        )(
            bp.response(200, ProjectStepResponseSchema(many=True))(
                jwt_required()(handle_get_project_steps)
            )
        )
    )

    bp.route("/projects/<int:project_id>/steps", methods=["POST"])(
        bp.doc(
            summary="Attach Form as Step",
            description="Attaches a new form from the 28-catalog as a step to the project.",
            security=[{"BearerAuth": []}],
        )(
            bp.arguments(ProjectStepAttachSchema)(
                bp.response(201, ProjectStepResponseSchema)(
                    jwt_required()(handle_add_project_step)
                )
            )
        )
    )

    bp.route("/projects/<int:project_id>/steps/<int:step_id>", methods=["GET"])(
        bp.doc(
            summary="Get Project Step",
            description="Returns single step details with data, remarks, and attachments.",
            security=[{"BearerAuth": []}],
        )(
            bp.response(200, ProjectStepResponseSchema)(
                jwt_required()(handle_get_single_step)
            )
        )
    )

    bp.route("/projects/<int:project_id>/steps/<int:step_id>", methods=["PUT"])(
        bp.doc(
            summary="Update Step (Save Draft or Complete)",
            description="Saves draft form fields, items, remarks, or marks step completed.",
            security=[{"BearerAuth": []}],
        )(
            bp.arguments(ProjectStepUpdateSchema)(
                bp.response(200, ProjectStepResponseSchema)(
                    jwt_required()(handle_update_step)
                )
            )
        )
    )

    bp.route("/projects/<int:project_id>/steps/<int:step_id>", methods=["PATCH"])(
        bp.doc(
            summary="Patch Step",
            description="Partially updates step fields, items, or status.",
            security=[{"BearerAuth": []}],
        )(
            bp.arguments(ProjectStepUpdateSchema)(
                bp.response(200, ProjectStepResponseSchema)(
                    jwt_required()(handle_update_step)
                )
            )
        )
    )

    bp.route("/projects/<int:project_id>/steps/<int:step_id>", methods=["DELETE"])(
        bp.doc(
            summary="Delete Step",
            description="Removes an attached step and cascades to its remarks and attachments.",
            security=[{"BearerAuth": []}],
        )(
            jwt_required()(handle_delete_step)
        )
    )

    bp.route(
        "/projects/<int:project_id>/steps/<int:step_id>/attachments",
        methods=["POST"],
    )(
        bp.doc(
            summary="Upload Step Attachment",
            description="Uploads a file for a specific upload slot (e.g. upload_pqb, upload_boe).",
            security=[{"BearerAuth": []}],
        )(
            jwt_required()(handle_upload_step_attachment)
        )
    )

    bp.route(
        "/projects/<int:project_id>/steps/<int:step_id>/remarks",
        methods=["POST"],
    )(
        bp.doc(
            summary="Add Step Remark",
            description="Adds a remark to the step audit trail.",
            security=[{"BearerAuth": []}],
        )(
            bp.arguments(ProjectStepRemarkCreateSchema)(
                jwt_required()(handle_add_step_remark)
            )
        )
    )