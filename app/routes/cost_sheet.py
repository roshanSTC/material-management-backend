import json
from flask import current_app, jsonify, make_response, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from app.extensions.database import db
from app.models.cost_sheet import CostSheet
from app.schemas.cost_sheet import (
    CostSheetGlobalParamsSchema,
    LatestCostSheetQuerySchema,
    LatestCostSheetResponseSchema,
    ProjectCostSheetCreateSchema,
    ProjectCostSheetMetadataResponseSchema,
    ProjectCostSheetQuerySchema,
)
from app.services.cost_sheet_service import build_cost_sheet_workbook
from app.services.project_cost_sheet_service import (
    CostSheetNotFoundError,
    ProjectNotFoundError,
    UserNotFoundError,
    cost_sheet_export_payload,
    create_project_cost_sheet,
    get_latest_project_cost_sheet,
    get_project_cost_sheet,
    list_project_cost_sheets,
    serialize_cost_sheet_metadata,
    serialize_latest_cost_sheet,
)

cost_sheet_bp = Blueprint(
    "cost_sheet",
    __name__,
    url_prefix="/api/cost-sheet",
    description="Cost Sheet Management APIs",
)

cost_sheet_v1_bp = Blueprint(
    "cost_sheets_v1",
    __name__,
    url_prefix="/api/v1/cost-sheets",
    description="Cost Sheet REST APIs (v1)",
)



def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


def _extract_cost_sheet_payload():
    files = []
    if request.files:
        files = request.files.getlist("file")

    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        raw_data = request.form.get("data")
        if raw_data:
            try:
                data = json.loads(raw_data)
            except Exception:
                data = request.form.to_dict()
        else:
            data = request.form.to_dict()
    return data, files


def _normalize_cost_sheet_payload(data: dict) -> dict:
    if not isinstance(data, dict):
        return {}
    normalized = dict(data)

    def _pct_to_rate(val, default=None):
        if val is None or val == "":
            return default
        try:
            f = float(val)
            return f / 100.0 if f > 1.0 else f
        except (ValueError, TypeError):
            return default

    # 1. Project ID resolution
    pid = normalized.get("project_id") or normalized.get("product_id") or normalized.get("projectId")
    if pid is not None:
        try:
            normalized["project_id"] = int(pid)
        except (ValueError, TypeError):
            pass

    # 2. Global Params resolution (supporting both flat and nested payloads)
    if "globalParams" in normalized and isinstance(normalized.get("globalParams"), dict):
        try:
            normalized["globalParams"] = CostSheetGlobalParamsSchema().load(normalized["globalParams"])
        except Exception:
            pass
    else:
        eur_to_inr = (
            normalized.get("eur_to_inr_rate_buffer")
            or normalized.get("eur_to_inr_rate_prep")
            or normalized.get("eurToInr")
            or 90.0
        )

        gp = {
            "eurToInr": float(eur_to_inr),
            "insuranceFreightRate": _pct_to_rate(normalized.get("freight_insurance_pct"), 0.01),
            "defaultCustomsDutyRate": _pct_to_rate(normalized.get("custom_duty_pct"), 0.075),
            "igstRate": _pct_to_rate(normalized.get("igst_pct"), 0.18),
            "transportationRate": _pct_to_rate(normalized.get("transportation_pct"), 0.01),
            "financeChargesRate": _pct_to_rate(normalized.get("finance_charges_pct"), 0.02),
            "marginRate": _pct_to_rate(normalized.get("margin_pct"), 0.10),
            "gstRate": _pct_to_rate(normalized.get("gst_pct"), 0.18),
        }
        try:
            normalized["globalParams"] = CostSheetGlobalParamsSchema().load(gp)
        except Exception:
            normalized["globalParams"] = gp

    # 3. Items normalization
    raw_items = normalized.get("items")
    if raw_items is None:
        raw_items = []

    clean_items = []
    for idx, it in enumerate(raw_items, start=1):
        if not isinstance(it, dict):
            continue
        icode = (it.get("itemCode") or it.get("item_code") or "").strip()
        if not icode:
            icode = f"ITEM-{idx}"

        idesc = (
            it.get("itemDescription")
            or it.get("item_description")
            or it.get("description")
            or it.get("material_name")
            or f"Item {idx}"
        ).strip()

        # Resolve prices (supporting pricePerUnitEur, pricePerUnitInr, unit_price, price, etc.)
        p_eur = (
            float(it["pricePerUnitEur"])
            if it.get("pricePerUnitEur") is not None and str(it.get("pricePerUnitEur")).strip() != ""
            else (
                float(it["price_per_unit_eur"])
                if it.get("price_per_unit_eur") is not None and str(it.get("price_per_unit_eur")).strip() != ""
                else None
            )
        )
        p_inr = (
            float(it["pricePerUnitInr"])
            if it.get("pricePerUnitInr") is not None and str(it.get("pricePerUnitInr")).strip() != ""
            else (
                float(it["price_per_unit_inr"])
                if it.get("price_per_unit_inr") is not None and str(it.get("price_per_unit_inr")).strip() != ""
                else None
            )
        )
        gen_price = (
            float(it["unit_price"])
            if it.get("unit_price") is not None and str(it.get("unit_price")).strip() != ""
            else (
                float(it["unitPrice"])
                if it.get("unitPrice") is not None and str(it.get("unitPrice")).strip() != ""
                else (
                    float(it["price"])
                    if it.get("price") is not None and str(it.get("price")).strip() != ""
                    else None
                )
            )
        )
        if p_eur is None and p_inr is None and gen_price is not None:
            p_eur = gen_price

        raw_cd = (
            it.get("customsDutyRate")
            if it.get("customsDutyRate") is not None and str(it.get("customsDutyRate")).strip() != ""
            else (
                it.get("customs_duty_rate")
                if it.get("customs_duty_rate") is not None and str(it.get("customs_duty_rate")).strip() != ""
                else (
                    it.get("custom_duty_rate")
                    if it.get("custom_duty_rate") is not None and str(it.get("custom_duty_rate")).strip() != ""
                    else (
                        it.get("custom_duty_pct")
                        if it.get("custom_duty_pct") is not None and str(it.get("custom_duty_pct")).strip() != ""
                        else None
                    )
                )
            )
        )
        cd_rate = _pct_to_rate(raw_cd, None)
        if cd_rate is not None and cd_rate > 1.0:
            cd_rate = cd_rate / 100.0

        clean_it = {
            "quotationNumber": it.get("quotationNumber") or it.get("quotation_number") or "",
            "quotationIndex": it.get("quotationIndex") or it.get("quotation_index") or f"{idx}",
            "itemDescription": idesc,
            "itemCode": icode,
            "quantity": float(it.get("quantity") or 1.0),
            "pricePerUnitEur": p_eur,
            "pricePerUnitInr": p_inr,
            "customsDutyRate": cd_rate,
        }
        clean_items.append(clean_it)
    normalized["items"] = clean_items

    # 4. Title normalization
    if not normalized.get("title"):
        normalized["title"] = normalized.get("project_title") or f"Cost Sheet for Project {normalized.get('project_id', 1)}"

    return normalized


def _handle_create_cost_sheet(data=None):
    extracted_data, files = _extract_cost_sheet_payload()
    if data is None:
        data = extracted_data

    data = _normalize_cost_sheet_payload(data)
    project_id = data.get("project_id") or data.get("product_id")
    if not project_id:
        return _error("PROJECT_ID_REQUIRED", "project_id is required.", 400)

    try:
        user_identity = get_jwt_identity()
        created_by = int(user_identity) if user_identity else 1
    except (TypeError, ValueError):
        created_by = 1

    try:
        cost_sheet = create_project_cost_sheet(
            project_id=project_id,
            data=data,
            created_by=created_by,
        )

        if files:
            from app.services.attachment_service import create_attachment
            for file in files:
                if not file or not getattr(file, "filename", None):
                    continue
                try:
                    create_attachment(
                        file=file,
                        entity_type="cost_sheet",
                        entity_id=cost_sheet.id,
                        uploaded_by=created_by,
                    )
                except Exception as e:
                    current_app.logger.warning(f"Error saving cost sheet attachment: {e}")

        db.session.commit()
        return serialize_cost_sheet_metadata(cost_sheet), 201
    except ProjectNotFoundError as exc:
        db.session.rollback()
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except UserNotFoundError as exc:
        db.session.rollback()
        return _error("USER_NOT_FOUND", str(exc), 404)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Cost sheet creation failed: %s", exc)
        return _error(
            "COST_SHEET_CREATE_FAILED",
            str(exc) or "Unable to create cost sheet.",
            500,
        )


def _handle_get_latest_cost_sheet(args=None):
    if args is None:
        args = {}
    project_id = (
        args.get("project_id")
        or request.args.get("project_id")
        or request.args.get("product_id")
    )
    if not project_id:
        return _error("PROJECT_ID_REQUIRED", "project_id query parameter is required.", 400)
    try:
        project_id = int(project_id)
        if project_id <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return _error("INVALID_PROJECT_ID", "project_id must be a positive integer.", 400)

    try:
        cost_sheet = get_latest_project_cost_sheet(project_id)
        return serialize_latest_cost_sheet(cost_sheet), 200
    except ProjectNotFoundError as exc:
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except CostSheetNotFoundError as exc:
        return _error("COST_SHEET_NOT_FOUND", str(exc), 404)


def _handle_get_cost_sheet(cost_sheet_id):
    try:
        cost_sheet = get_project_cost_sheet(cost_sheet_id)
    except CostSheetNotFoundError as exc:
        return _error("COST_SHEET_NOT_FOUND", str(exc), 404)
    return serialize_cost_sheet_metadata(cost_sheet), 200


def _handle_list_cost_sheets(args=None):
    if args is None:
        args = request.args
    project_id = args.get("project_id") if args else None
    if project_id:
        try:
            project_id = int(project_id)
        except (ValueError, TypeError):
            project_id = None
    try:
        cost_sheets = list_project_cost_sheets(project_id)
    except ProjectNotFoundError as exc:
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    return [serialize_cost_sheet_metadata(cs) for cs in cost_sheets], 200


def _handle_update_cost_sheet(cost_sheet_id, data=None):
    rec = db.session.get(CostSheet, cost_sheet_id)
    if not rec:
        return _error("COST_SHEET_NOT_FOUND", f"CostSheet {cost_sheet_id} not found.", 404)

    extracted_data, files = _extract_cost_sheet_payload()
    if data is None:
        data = extracted_data
    if "title" in data:
        rec.title = data["title"]
    if "status" in data:
        rec.status = data["status"]

    remarks_val = data.get("remarks") if "remarks" in data else data.get("remark")
    if remarks_val is not None:
        from app.services.step_remark_service import sync_step_remarks
        user_identity = get_jwt_identity()
        user_id = int(user_identity) if user_identity else None
        sync_step_remarks(
            project_id=rec.project_id,
            step_number=4,
            remarks_data=remarks_val,
            default_user_id=user_id,
            entity_id=rec.id,
        )

    db.session.commit()
    return serialize_cost_sheet_metadata(rec), 200


def _handle_delete_cost_sheet(cost_sheet_id):
    rec = db.session.get(CostSheet, cost_sheet_id)
    if not rec:
        return _error("COST_SHEET_NOT_FOUND", f"CostSheet {cost_sheet_id} not found.", 404)
    db.session.delete(rec)
    db.session.commit()
    return jsonify({"success": True, "message": "Cost sheet deleted successfully."}), 200


def _handle_export_cost_sheet(cost_sheet_id):
    try:
        cost_sheet = get_project_cost_sheet(cost_sheet_id)
    except CostSheetNotFoundError as exc:
        return _error("COST_SHEET_NOT_FOUND", str(exc), 404)

    global_params, items = cost_sheet_export_payload(cost_sheet)
    workbook = build_cost_sheet_workbook(global_params=global_params, items=items)
    return send_file(
        workbook,
        as_attachment=True,
        download_name=(
            f"CostSheet_Project_{cost_sheet.project_id}_"
            f"v{cost_sheet.version_number}.xlsx"
        ),
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )


# Register routes on all cost sheet blueprints (legacy and v1 plural/singular)
for bp in [cost_sheet_bp, cost_sheet_v1_bp,]:
    bp.route("", methods=["POST"])(jwt_required()(_handle_create_cost_sheet))
    bp.route("", methods=["GET"])(jwt_required()(_handle_list_cost_sheets))
    bp.route("/latest", methods=["GET"])(jwt_required()(_handle_get_latest_cost_sheet))
    bp.route("/<int:cost_sheet_id>", methods=["GET"])(jwt_required()(_handle_get_cost_sheet))
    bp.route("/<int:cost_sheet_id>", methods=["PATCH"])(jwt_required()(_handle_update_cost_sheet))
    bp.route("/<int:cost_sheet_id>", methods=["DELETE"])(jwt_required()(_handle_delete_cost_sheet))
    bp.route("/<int:cost_sheet_id>/export", methods=["GET"])(jwt_required()(_handle_export_cost_sheet))
