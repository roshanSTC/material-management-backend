
from app.models import (
    Customer,
    Project,
    Supplier,
)
from app.extensions.database import db


SUPPORTED_ENTITIES = {
    "project": Project,
    "customer": Customer,
    "supplier": Supplier,
}


class AttachmentEntityError(Exception):
    """Base exception for attachment entity errors."""


class AttachmentEntityNotFoundError(
    AttachmentEntityError
):
    """Raised when the target entity does not exist."""


def get_entity_model(entity_type: str):
    """
    Return the SQLAlchemy model associated with an
    attachment entity type.
    """

    normalized_entity_type = (
        entity_type.strip().lower()
    )

    model = SUPPORTED_ENTITIES.get(
        normalized_entity_type
    )

    if model is None:
        raise AttachmentEntityError(
            f"Unsupported entity type: "
            f"{entity_type}"
        )

    return model


def get_entity(
    *,
    entity_type: str,
    entity_id: int,
):
    """
    Resolve and validate the target business entity.
    """

    model = get_entity_model(entity_type)

    entity = db.session.get(
            model,
            entity_id,
        )

    if entity is None:
        raise AttachmentEntityNotFoundError(
            f"{entity_type} with id {entity_id} "
            "was not found."
        )

    return entity
