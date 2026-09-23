from flask import jsonify, make_response
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.schemas.step_remark import (
    ProjectRemarksListResponseSchema,
)
from app.services.step_remark_service import (
    ProjectNotFoundError,
    get_project_remarks_grouped,
)

step_remarks_bp = Blueprint(
    "step_remarks",
    __name__,
    url_prefix="/api/v1/projects",
    description="Project Step Remarks Management APIs",
)


def _error(code: str, message: str, status: int):
    return make_response(
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status,
    )


@step_remarks_bp.get("/<int:project_id>/remarks")
@step_remarks_bp.doc(security=[{"BearerAuth": []}])
@step_remarks_bp.response(200, ProjectRemarksListResponseSchema)
@jwt_required()
def get_project_remarks(project_id):
    try:
        grouped = get_project_remarks_grouped(project_id)
        return {
            "success": True,
            "message": "Project remarks fetched successfully",
            "data": grouped,
        }, 200
    except ProjectNotFoundError as exc:
        return _error("PROJECT_NOT_FOUND", str(exc), 404)
