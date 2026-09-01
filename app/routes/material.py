from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.schemas.material import (
    MaterialCreateSchema,
    MaterialUpdateSchema,
    MaterialResponseSchema,
)

from app.services.material_service import (
    InvalidMaterialError,
    MaterialAlreadyExistsError,
    MaterialNotFoundError,
    create_material_transaction,
    get_material_record,
    list_material_records,
    serialize_material,
    toggle_material,
    update_material_transaction,
)


material_bp = Blueprint(
    "materials",
    __name__,
    url_prefix="/api/v1/materials",
    description="Material APIs",
)


@material_bp.post("")
@material_bp.doc(
    security=[{"BearerAuth": []}]
)
@material_bp.arguments(
    MaterialCreateSchema
)
@material_bp.response(
    201,
    MaterialResponseSchema,
)
@jwt_required()
def create(data):

    try:
        material = create_material_transaction(
            material_code=data["material_code"],
            material_name=data["material_name"],
            hsn_code=data.get("hsn_code"),
            description=data.get("description"),
        )

        return serialize_material(material), 201

    except MaterialAlreadyExistsError as exc:

        return {
            "success": False,
            "error": {
                "code": "MATERIAL_ALREADY_EXISTS",
                "message": str(exc),
            },
        }, 409

    except InvalidMaterialError as exc:

        return {
            "success": False,
            "error": {
                "code": "INVALID_MATERIAL",
                "message": str(exc),
            },
        }, 422


@material_bp.get("")
@material_bp.doc(
    security=[{"BearerAuth": []}]
)
@material_bp.response(
    200,
    MaterialResponseSchema(many=True),
)
@jwt_required()
def list_all():

    is_active_raw = None

    # Optional query parameter
    # ?is_active=true
    from flask import request

    if "is_active" in request.args:

        value = request.args.get(
            "is_active"
        )

        if value not in {"true", "false"}:
            return {
                "success": False,
                "error": {
                    "code": "INVALID_IS_ACTIVE",
                    "message": (
                        "is_active must be true or false."
                    ),
                },
            }, 422

        is_active_raw = value == "true"

    materials = list_material_records(
        is_active=is_active_raw,
    )

    return [
        serialize_material(material)
        for material in materials
    ], 200


@material_bp.get(
    "/<int:material_id>"
)
@material_bp.doc(
    security=[{"BearerAuth": []}]
)
@material_bp.response(
    200,
    MaterialResponseSchema,
)
@jwt_required()
def get_one(material_id):

    try:
        material = get_material_record(
            material_id
        )

        return serialize_material(
            material
        ), 200

    except MaterialNotFoundError as exc:

        return {
            "success": False,
            "error": {
                "code": "MATERIAL_NOT_FOUND",
                "message": str(exc),
            },
        }, 404


@material_bp.put(
    "/<int:material_id>"
)
@material_bp.doc(
    security=[{"BearerAuth": []}]
)
@material_bp.arguments(
    MaterialUpdateSchema
)
@material_bp.response(
    200,
    MaterialResponseSchema,
)
@jwt_required()
def update(data, material_id):

    try:
        material = update_material_transaction(
            material_id=material_id,
            data=data,
        )

        return serialize_material(
            material
        ), 200

    except MaterialNotFoundError as exc:

        return {
            "success": False,
            "error": {
                "code": "MATERIAL_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except MaterialAlreadyExistsError as exc:

        return {
            "success": False,
            "error": {
                "code": "MATERIAL_ALREADY_EXISTS",
                "message": str(exc),
            },
        }, 409

    except InvalidMaterialError as exc:

        return {
            "success": False,
            "error": {
                "code": "INVALID_MATERIAL",
                "message": str(exc),
            },
        }, 422


@material_bp.patch(
    "/<int:material_id>/toggle"
)
@material_bp.doc(
    security=[{"BearerAuth": []}]
)
@material_bp.response(
    200,
    MaterialResponseSchema,
)
@jwt_required()
def toggle(material_id):

    try:
        material = toggle_material(
            material_id
        )

        return serialize_material(
            material
        ), 200

    except MaterialNotFoundError as exc:

        return {
            "success": False,
            "error": {
                "code": "MATERIAL_NOT_FOUND",
                "message": str(exc),
            },
        }, 404