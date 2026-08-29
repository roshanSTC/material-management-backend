from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.schemas.project_step import (
    ProjectStepCreateUpdateSchema,
    ProjectStepResponseSchema,
)
from app.services.project_step_service import (
    InvalidStepDataError,
    InvalidStepNumberError,
    ProjectNotFoundError,
    ProjectStepAlreadyExistsError,
    ProjectStepNotFoundError,
    create_project_step,
    get_project_step,
    list_project_steps,
    serialize_project_step,
    update_project_step,
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


@project_step_bp.get(
    "/<int:project_id>/steps/<int:step_number>"
)
@project_step_bp.doc(
    security=[{"BearerAuth": []}]
)
@project_step_bp.response(
    200,
    ProjectStepResponseSchema,
)
@jwt_required()
def get_step(project_id, step_number):
    try:
        step = get_project_step(
            project_id=project_id,
            step_number=step_number,
        )

        return serialize_project_step(step), 200

    except ProjectNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except ProjectStepNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "PROJECT_STEP_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except InvalidStepNumberError as exc:
        return {
            "success": False,
            "error": {
                "code": "INVALID_STEP_NUMBER",
                "message": str(exc),
            },
        }, 422


@project_step_bp.post(
    "/<int:project_id>/steps/<int:step_number>"
)
@project_step_bp.doc(
    security=[{"BearerAuth": []}]
)
@project_step_bp.arguments(
    ProjectStepCreateUpdateSchema
)
@project_step_bp.response(
    201,
    ProjectStepResponseSchema,
)
@jwt_required()
def create_step(data, project_id, step_number):
    try:
        step = create_project_step(
            project_id=project_id,
            step_number=step_number,
            data=data.get("data"),
        )

        return serialize_project_step(step), 201

    except ProjectNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except ProjectStepAlreadyExistsError as exc:
        return {
            "success": False,
            "error": {
                "code": "PROJECT_STEP_ALREADY_EXISTS",
                "message": str(exc),
            },
        }, 409

    except InvalidStepNumberError as exc:
        return {
            "success": False,
            "error": {
                "code": "INVALID_STEP_NUMBER",
                "message": str(exc),
            },
        }, 422

    except InvalidStepDataError as exc:
        return {
            "success": False,
            "error": {
                "code": "INVALID_STEP_DATA",
                "message": str(exc),
            },
        }, 422


@project_step_bp.put(
    "/<int:project_id>/steps/<int:step_number>"
)
@project_step_bp.doc(
    security=[{"BearerAuth": []}]
)
@project_step_bp.arguments(
    ProjectStepCreateUpdateSchema
)
@project_step_bp.response(
    200,
    ProjectStepResponseSchema,
)
@jwt_required()
def update_step(data, project_id, step_number):
    try:
        step = update_project_step(
            project_id=project_id,
            step_number=step_number,
            data=data.get("data"),
        )

        return serialize_project_step(step), 200

    except ProjectNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except ProjectStepNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "PROJECT_STEP_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except InvalidStepNumberError as exc:
        return {
            "success": False,
            "error": {
                "code": "INVALID_STEP_NUMBER",
                "message": str(exc),
            },
        }, 422

    except InvalidStepDataError as exc:
        return {
            "success": False,
            "error": {
                "code": "INVALID_STEP_DATA",
                "message": str(exc),
            },
        }, 422