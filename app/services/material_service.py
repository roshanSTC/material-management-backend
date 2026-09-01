from app.extensions.database import db

from app.models import Material

from app.repositories.material_repository import (
    create_material as repository_create_material,
    get_material,
    get_material_by_code,
    list_materials,
)


class MaterialError(Exception):
    """Base exception for material operations."""


class MaterialNotFoundError(MaterialError):
    pass


class MaterialAlreadyExistsError(MaterialError):
    pass


class InvalidMaterialError(MaterialError):
    pass


def _clean_string(
    value: str | None,
) -> str | None:

    if value is None:
        return None

    value = value.strip()

    return value if value else None


def create_material_transaction(
    *,
    material_code: str,
    material_name: str,
    hsn_code: str | None,
    description: str | None,
) -> Material:

    material_code = material_code.strip()
    material_name = material_name.strip()

    if not material_code:
        raise InvalidMaterialError(
            "Material code is required."
        )

    if not material_name:
        raise InvalidMaterialError(
            "Material name is required."
        )

    existing = get_material_by_code(
        material_code
    )

    if existing is not None:
        raise MaterialAlreadyExistsError(
            f"Material with code "
            f"'{material_code}' already exists."
        )

    material = repository_create_material(
        material_code=material_code,
        material_name=material_name,
        hsn_code=_clean_string(hsn_code),
        description=_clean_string(description),
    )

    try:
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return material


def get_material_record(
    material_id: int,
) -> Material:

    material = get_material(material_id)

    if material is None:
        raise MaterialNotFoundError(
            f"Material with id {material_id} "
            f"was not found."
        )

    return material


def list_material_records(
    *,
    is_active: bool | None = None,
) -> list[Material]:

    return list_materials(
        is_active=is_active,
    )


def update_material_transaction(
    *,
    material_id: int,
    data: dict,
) -> Material:

    material = get_material_record(
        material_id
    )

    if "material_code" in data:
        material_code = data["material_code"].strip()

        if not material_code:
            raise InvalidMaterialError(
                "Material code cannot be empty."
            )

        existing = get_material_by_code(
            material_code
        )

        if (
            existing is not None
            and existing.id != material.id
        ):
            raise MaterialAlreadyExistsError(
                f"Material with code "
                f"'{material_code}' already exists."
            )

        material.material_code = material_code

    if "material_name" in data:
        material_name = data["material_name"].strip()

        if not material_name:
            raise InvalidMaterialError(
                "Material name cannot be empty."
            )

        material.material_name = material_name

    if "hsn_code" in data:
        material.hsn_code = _clean_string(
            data["hsn_code"]
        )

    if "description" in data:
        material.description = _clean_string(
            data["description"]
        )

    try:
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return material


def toggle_material(
    material_id: int,
) -> Material:

    material = get_material_record(
        material_id
    )

    material.is_active = not material.is_active

    try:
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return material


def serialize_material(
    material: Material,
) -> dict:

    return {
        "id": material.id,
        "material_code": material.material_code,
        "material_name": material.material_name,
        "hsn_code": material.hsn_code,
        "description": material.description,
        "is_active": material.is_active,
        "created_at": material.created_at,
        "updated_at": material.updated_at,
    }