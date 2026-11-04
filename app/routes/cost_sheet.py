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

cost_sheet_v1_singular_bp = Blueprint(
    "cost_sheet_v1_singular",
    __name__,
    url_prefix="/api/v1/cost-sheet",
    description="Cost Sheet REST APIs (v1 Singular)",
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

        item_id = it.get("id")
        if item_id is not None and str(item_id).strip() != "":
            try:
                item_id = int(item_id)
            except (ValueError, TypeError):
                item_id = None
        else:
            item_id = None

        clean_it = {
            "id": item_id,
            "sr_no": it.get("sr_no") or idx,
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
    from datetime import datetime
    from app.models.cost_sheet_item import CostSheetItem
    from app.services.cost_sheet_service import calculate_cost_sheet

    rec = db.session.get(CostSheet, cost_sheet_id)
    if not rec:
        return _error("COST_SHEET_NOT_FOUND", f"CostSheet {cost_sheet_id} not found.", 404)

    extracted_data, files = _extract_cost_sheet_payload()
    if data is None:
        data = extracted_data

    # Normalize data
    norm_data = _normalize_cost_sheet_payload(data)

    if norm_data.get("title"):
        rec.title = norm_data["title"]
    elif data.get("title"):
        rec.title = data["title"]
    elif data.get("project_title"):
        rec.title = data["project_title"]

    if data.get("status"):
        rec.status = data["status"]
    elif norm_data.get("status"):
        rec.status = norm_data["status"]

    if "globalParams" in norm_data and isinstance(norm_data["globalParams"], dict):
        rec.global_params = norm_data["globalParams"]

    # Process items update if items field was provided
    if "items" in data:
        items_payload = norm_data.get("items") or []
        existing_items_by_id = {item.id: item for item in rec.items}
        kept_item_ids = set()

        eur_to_inr = 1.0
        if isinstance(rec.global_params, dict) and rec.global_params.get("eurToInr"):
            try:
                eur_to_inr = float(rec.global_params["eurToInr"])
            except (ValueError, TypeError):
                eur_to_inr = 1.0

        for idx, item_data in enumerate(items_payload, start=1):
            item_id = item_data.get("id")
            price_eur = (
                item_data.get("pricePerUnitEur")
                if item_data.get("pricePerUnitEur") is not None
                else (
                    float(item_data["pricePerUnitInr"]) / eur_to_inr
                    if item_data.get("pricePerUnitInr") is not None and eur_to_inr
                    else 0.0
                )
            )
            cd_rate = item_data.get("customsDutyRate")
            if cd_rate is not None:
                try:
                    cd_f = float(cd_rate)
                    cd_rate = cd_f / 100.0 if cd_f > 1.0 else cd_f
                except (ValueError, TypeError):
                    cd_rate = None

            icode = (item_data.get("itemCode") or "").strip()
            if not icode:
                icode = f"ITEM-{idx}"

            idesc = (item_data.get("itemDescription") or f"Item {idx}").strip()
            qty = float(item_data.get("quantity") or 1.0)
            q_no = item_data.get("quotationNumber")
            q_idx = item_data.get("quotationIndex")

            if item_id and item_id in existing_items_by_id:
                ex = existing_items_by_id[item_id]
                ex.quotation_number = q_no
                ex.quotation_index = q_idx
                ex.item_code = icode
                ex.item_description = idesc
                ex.price_per_unit_eur = price_eur
                ex.quantity = qty
                ex.customs_duty_rate = cd_rate
                ex.updated_at = datetime.utcnow()
                kept_item_ids.add(item_id)
            else:
                new_item = CostSheetItem(
                    cost_sheet_id=rec.id,
                    quotation_number=q_no,
                    quotation_index=q_idx,
                    item_code=icode,
                    item_description=idesc,
                    price_per_unit_eur=price_eur,
                    quantity=qty,
                    customs_duty_rate=cd_rate,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                rec.items.append(new_item)

        for old_id, old_item in list(existing_items_by_id.items()):
            if old_id not in kept_item_ids:
                rec.items.remove(old_item)

        db.session.flush()

    # Recalculate calculation output based on updated global_params and items
    items_for_calc = [
        {
            "quotationNumber": it.quotation_number or "",
            "quotationIndex": it.quotation_index or "",
            "itemDescription": it.item_description,
            "itemCode": it.item_code,
            "pricePerUnitEur": float(it.price_per_unit_eur),
            "quantity": float(it.quantity),
            "customsDutyRate": (
                float(it.customs_duty_rate)
                if it.customs_duty_rate is not None
                else None
            ),
        }
        for it in rec.items
    ]
    try:
        rec.output = calculate_cost_sheet(
            global_params=rec.global_params,
            items=items_for_calc,
        )
    except Exception as exc:
        current_app.logger.warning(f"Error recalculating cost sheet output: {exc}")

    rec.updated_at = datetime.utcnow()

    # Save file attachments if any
    if files:
        from app.services.attachment_service import create_attachment
        try:
            user_identity = get_jwt_identity()
            user_id = int(user_identity) if user_identity else 1
        except Exception:
            user_id = 1
        for file in files:
            if not file or not getattr(file, "filename", None):
                continue
            try:
                create_attachment(
                    file=file,
                    entity_type="cost_sheet",
                    entity_id=rec.id,
                    uploaded_by=user_id,
                )
            except Exception as e:
                current_app.logger.warning(f"Error saving cost sheet attachment: {e}")

    # Handle remarks
    remarks_val = data.get("remarks") if "remarks" in data else data.get("remark")
    if remarks_val is not None:
        from app.services.step_remark_service import sync_step_remarks
        try:
            user_identity = get_jwt_identity()
            user_id = int(user_identity) if user_identity else None
        except Exception:
            user_id = None
        sync_step_remarks(
            project_id=rec.project_id,
            step_number=4,
            remarks_data=remarks_val,
            default_user_id=user_id,
            entity_id=rec.id,
        )

    # Sync project steps
    from app.services.project_step_service import sync_cost_sheet_step
    sync_cost_sheet_step(rec.project_id)

    from app.routes.project_step import sync_project_steps_from_records
    from app.models.project import Project
    proj = db.session.get(Project, rec.project_id)
    if proj:
        sync_project_steps_from_records(proj)

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
for bp in [cost_sheet_bp, cost_sheet_v1_bp, cost_sheet_v1_singular_bp]:
    bp.route("", methods=["POST"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(_handle_create_cost_sheet)))
    bp.route("", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(_handle_list_cost_sheets)))
    bp.route("/latest", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(_handle_get_latest_cost_sheet)))
    bp.route("/<int:cost_sheet_id>", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(_handle_get_cost_sheet)))
    bp.route("/<int:cost_sheet_id>", methods=["PATCH", "PUT"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(_handle_update_cost_sheet)))
    bp.route("/<int:cost_sheet_id>", methods=["DELETE"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(_handle_delete_cost_sheet)))
    bp.route("/<int:cost_sheet_id>/export", methods=["GET"])(bp.doc(security=[{"BearerAuth": []}])(jwt_required()(_handle_export_cost_sheet)))
