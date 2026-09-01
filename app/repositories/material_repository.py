from app.extensions.database import db
from app.models import Material


def create_material(
    *,
    material_code: str,
    material_name: str,
    hsn_code: str | None,
    description: str | None,
) -> Material:

    material = Material(
        material_code=material_code,
        material_name=material_name,
        hsn_code=hsn_code,
        description=description,
        is_active=True,
    )

    db.session.add(material)

    return material


def get_material(
    material_id: int,
) -> Material | None:

    return db.session.get(
        Material,
        material_id,
    )


def get_material_by_code(
    material_code: str,
) -> Material | None:

    return db.session.execute(
        db.select(Material)
        .where(
            Material.material_code == material_code
        )
    ).scalar_one_or_none()


def list_materials(
    *,
    is_active: bool | None = None,
) -> list[Material]:

    query = db.select(Material)

    if is_active is not None:
        query = query.where(
            Material.is_active == is_active
        )

    query = query.order_by(
        Material.material_name.asc()
    )

    return db.session.execute(
        query
    ).scalars().all()