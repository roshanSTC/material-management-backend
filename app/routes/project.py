
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.schemas.project import (
    ProjectCreateSchema,
    ProjectResponseSchema,
    ProjectUpdateSchema,
)
from app.services.project_service import (
    CustomerNotFoundError,
    ProjectNotFoundError,
    SupplierNotFoundError,
    create_project,
    get_project,
    list_projects,
    update_project,
)


project_bp = Blueprint(
    "projects",
    __name__,
    url_prefix="/api/v1/projects",
    description="Project Management APIs",
)


def _project_response(project):
    return {
        "id": project.id,
        "project_title": project.project_title,
        "customer_id": project.customer_id,
        "supplier_id": project.supplier_id,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


@project_bp.post("")
@project_bp.doc(security=[{"BearerAuth": []}])
@project_bp.arguments(ProjectCreateSchema)
@project_bp.response(201, ProjectResponseSchema)
@jwt_required()
def create(data):
    try:
        project = create_project(
            project_title=data["project_title"],
            customer_id=data["customer_id"],
            supplier_id=data["supplier_id"],
        )

    except CustomerNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "CUSTOMER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except SupplierNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "SUPPLIER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    return _project_response(project), 201


@project_bp.get("")
@project_bp.doc(security=[{"BearerAuth": []}])
@project_bp.response(200, ProjectResponseSchema(many=True))
@jwt_required()
def list_all():
    projects = list_projects()

    return [
        _project_response(project)
        for project in projects
    ], 200


@project_bp.get("/<int:project_id>")
@project_bp.doc(security=[{"BearerAuth": []}])
@project_bp.response(200, ProjectResponseSchema)
@jwt_required()
def get(project_id):
    try:
        project = get_project(project_id)

    except ProjectNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    return _project_response(project), 200


@project_bp.put("/<int:project_id>")
@project_bp.doc(security=[{"BearerAuth": []}])
@project_bp.arguments(ProjectUpdateSchema)
@project_bp.response(200, ProjectResponseSchema)
@jwt_required()
def update(data, project_id):
    try:
        project = update_project(
            project_id,
            project_title=data.get("project_title"),
            customer_id=data.get("customer_id"),
            supplier_id=data.get("supplier_id"),
        )

    except ProjectNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except CustomerNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "CUSTOMER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except SupplierNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "SUPPLIER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    return _project_response(project), 200
