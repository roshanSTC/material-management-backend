from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.schemas.project_step import ProjectStepResponseSchema
from app.services.project_step_service import (
    ProjectNotFoundError,
    list_project_steps,
    serialize_project_step,
)


project_step_bp = Blueprint(
    "project_steps",
    __name__,
    url_prefix="/api/v1/projects",
    description="Project Step APIs",
)


@project_step_bp.get(
    "/<int:project_id>/steps"
)
@project_step_bp.doc(
    security=[{"BearerAuth": []}]
)
@project_step_bp.response(
    200,
    ProjectStepResponseSchema(many=True),
)
@jwt_required()
def list_all_steps(project_id):
    try:
        steps = list_project_steps(project_id)

        return [
            serialize_project_step(step)
            for step in steps
        ], 200

    except ProjectNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": str(exc),
            },
        }, 404