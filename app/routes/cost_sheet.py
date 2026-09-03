from flask import current_app, jsonify, make_response, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from app.extensions.database import db
from app.schemas.cost_sheet import (
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
    get_project_cost_sheet,
    list_project_cost_sheets,
    serialize_cost_sheet_metadata,
)

cost_sheet_bp = Blueprint(
    "cost_sheet",
    __name__,
    url_prefix="/api/cost-sheet",
    description="Cost Sheet Management APIs",
)


def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


# 1. POST /api/cost-sheet - Create cost sheet, calculate and store in DB
@cost_sheet_bp.post("")
@cost_sheet_bp.doc(security=[{"BearerAuth": []}])
@cost_sheet_bp.arguments(ProjectCostSheetCreateSchema)
@cost_sheet_bp.response(201, ProjectCostSheetMetadataResponseSchema)
@jwt_required()
def create_cost_sheet(data):
    project_id = data.get("project_id") or data.get("product_id")
    try:
        cost_sheet = create_project_cost_sheet(
            project_id=project_id,
            data=data,
            created_by=int(get_jwt_identity()),
        )
        db.session.commit()
        return serialize_cost_sheet_metadata(cost_sheet), 201
    except ProjectNotFoundError as exc:
        db.session.rollback()
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    except UserNotFoundError as exc:
        db.session.rollback()
        return _error("USER_NOT_FOUND", str(exc), 404)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Cost sheet creation failed")
        return _error(
            "COST_SHEET_CREATE_FAILED",
            "Unable to create cost sheet.",
            500,
        )


# 2. GET /api/cost-sheet/<int:cost_sheet_id> - Get particular cost sheet data
@cost_sheet_bp.get("/<int:cost_sheet_id>")
@cost_sheet_bp.doc(security=[{"BearerAuth": []}])
@cost_sheet_bp.response(200, ProjectCostSheetMetadataResponseSchema)
@jwt_required()
def get_cost_sheet(cost_sheet_id):
    try:
        cost_sheet = get_project_cost_sheet(cost_sheet_id)
    except CostSheetNotFoundError as exc:
        return _error("COST_SHEET_NOT_FOUND", str(exc), 404)
    return serialize_cost_sheet_metadata(cost_sheet), 200


# GET /api/cost-sheet - List cost sheets (filtered by project_id if provided)
@cost_sheet_bp.get("")
@cost_sheet_bp.doc(security=[{"BearerAuth": []}])
@cost_sheet_bp.arguments(ProjectCostSheetQuerySchema, location="query")
@cost_sheet_bp.response(200, ProjectCostSheetMetadataResponseSchema(many=True))
@jwt_required()
def list_cost_sheets(args):
    project_id = args.get("project_id")
    try:
        cost_sheets = list_project_cost_sheets(project_id)
    except ProjectNotFoundError as exc:
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    return [serialize_cost_sheet_metadata(cs) for cs in cost_sheets], 200


# 3. GET /api/cost-sheet/<int:cost_sheet_id>/export - Download cost sheet Excel
@cost_sheet_bp.get("/<int:cost_sheet_id>/export")
@cost_sheet_bp.doc(
    security=[{"BearerAuth": []}],
    responses={
        200: {
            "description": "Cost sheet Excel workbook download.",
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
            },
        }
    },
)
@jwt_required()
def export_cost_sheet(cost_sheet_id):
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
