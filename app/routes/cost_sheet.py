from flask import current_app, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from app.extensions.database import db
from app.schemas.cost_sheet import CostSheetCalculationResponseSchema, CostSheetRequestSchema
from app.services.cost_sheet_service import build_cost_sheet_workbook, calculate_cost_sheet
from app.schemas.cost_sheet import (
    CostSheetItemRateUpdateSchema,
    ProjectCostSheetCreateSchema,
    ProjectCostSheetMetadataResponseSchema,
)
from app.services.project_cost_sheet_service import (
    CostSheetItemMismatchError,
    CostSheetItemNotFoundError,
    CostSheetNotFoundError,
    ProjectNotFoundError,
    UserNotFoundError,
    cost_sheet_export_payload,
    create_project_cost_sheet,
    get_project_cost_sheet,
    list_project_cost_sheets,
    serialize_cost_sheet_metadata,
    update_cost_sheet_item_rate,
)


# cost_sheet_bp = Blueprint(
#     "cost_sheet",
#     __name__,
#     url_prefix="/api/v1/cost-sheet",
#     description="Cost Sheet Calculation and Excel Export APIs",
# )

project_cost_sheet_bp = Blueprint(
    "project_cost_sheets",
    __name__,
    url_prefix="/api/v1",
    description="Persistent Project Cost Sheet APIs",
)


def _error(code: str, message: str, status: int):
    return {"success": False, "error": {"code": code, "message": message}}, status


@project_cost_sheet_bp.post("/projects/<int:project_id>/cost-sheets")
@project_cost_sheet_bp.doc(security=[{"BearerAuth": []}])
@project_cost_sheet_bp.arguments(ProjectCostSheetCreateSchema)
@project_cost_sheet_bp.response(201, ProjectCostSheetMetadataResponseSchema)
@jwt_required()
def create_for_project(data, project_id):
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
        current_app.logger.exception("Project cost sheet creation failed")
        return _error(
            "COST_SHEET_CREATE_FAILED",
            "Unable to create project cost sheet.",
            500,
        )


@project_cost_sheet_bp.get("/projects/<int:project_id>/cost-sheets")
@project_cost_sheet_bp.doc(security=[{"BearerAuth": []}])
@project_cost_sheet_bp.response(200, ProjectCostSheetMetadataResponseSchema(many=True))
@jwt_required()
def list_for_project(project_id):
    try:
        cost_sheets = list_project_cost_sheets(project_id)
    except ProjectNotFoundError as exc:
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
    return [serialize_cost_sheet_metadata(cost_sheet) for cost_sheet in cost_sheets], 200


# @project_cost_sheet_bp.patch("/cost-sheets/<int:cost_sheet_id>/items/<int:item_id>")
# @project_cost_sheet_bp.doc(security=[{"BearerAuth": []}])
# @project_cost_sheet_bp.arguments(CostSheetItemRateUpdateSchema)
# @project_cost_sheet_bp.response(200, ProjectCostSheetMetadataResponseSchema)
# @jwt_required()
# def update_item_rate(data, cost_sheet_id, item_id):
#     try:
#         cost_sheet, _item, _price_changed = update_cost_sheet_item_rate(
#             cost_sheet_id=cost_sheet_id,
#             cost_sheet_item_id=item_id,
#             data=data,
#             changed_by=int(get_jwt_identity()),
#         )
#         db.session.commit()
#         return serialize_cost_sheet_metadata(cost_sheet), 200
#     except CostSheetNotFoundError as exc:
#         db.session.rollback()
#         return _error("COST_SHEET_NOT_FOUND", str(exc), 404)
#     except CostSheetItemNotFoundError as exc:
#         db.session.rollback()
#         return _error("COST_SHEET_ITEM_NOT_FOUND", str(exc), 404)
#     except CostSheetItemMismatchError as exc:
#         db.session.rollback()
#         return _error("COST_SHEET_ITEM_MISMATCH", str(exc), 409)
#     except UserNotFoundError as exc:
#         db.session.rollback()
#         return _error("USER_NOT_FOUND", str(exc), 404)
#     except Exception:
#         db.session.rollback()
#         current_app.logger.exception("Cost sheet item rate update failed")
#         return _error(
#             "COST_SHEET_ITEM_RATE_UPDATE_FAILED",
#             "Unable to update the cost sheet item rate.",
#             500,
#         )


@project_cost_sheet_bp.get("/cost-sheets/<int:cost_sheet_id>/export")
@project_cost_sheet_bp.doc(
    security=[{"BearerAuth": []}],
    responses={
        200: {
            "description": "In-memory project cost sheet workbook.",
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
            },
        }
    },
)
@jwt_required()
def export_project_cost_sheet(cost_sheet_id):
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


# @cost_sheet_bp.post("/calculate")
# @cost_sheet_bp.doc(security=[{"BearerAuth": []}])
# @cost_sheet_bp.arguments(CostSheetRequestSchema)
# @cost_sheet_bp.response(200, CostSheetCalculationResponseSchema)
# @jwt_required()
# def calculate(data):
#     return calculate_cost_sheet(
#         global_params=data["globalParams"],
#         items=data["items"],
#     ), 200


# @cost_sheet_bp.post("/export-excel")
# @cost_sheet_bp.doc(
#     security=[{"BearerAuth": []}],
#     responses={
#         200: {
#             "description": "Cost sheet workbook with editable Excel formulas.",
#             "content": {
#                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
#             },
#         }
#     },
# )
# @cost_sheet_bp.arguments(CostSheetRequestSchema)
# @jwt_required()
# def export_excel(data):
#     workbook = build_cost_sheet_workbook(
#         global_params=data["globalParams"],
#         items=data["items"],
#     )
#     return send_file(
#         workbook,
#         as_attachment=True,
#         download_name="cost_sheet.xlsx",
#         mimetype=(
#             "application/vnd.openxmlformats-officedocument."
#             "spreadsheetml.sheet"
#         ),
#     )
