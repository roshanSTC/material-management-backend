import json
from marshmallow import fields


def normalize_remark_for_db(remark):
    """
    Prepares a remark value for storage in a SQL column (e.g. TEXT).
    If it's a list or dict, dump to JSON string.
    If it's a string, strip it.
    If empty or None, return None.
    """
    if remark is None:
        return None
    if isinstance(remark, (list, dict)):
        return json.dumps(remark)
    if isinstance(remark, str):
        s = remark.strip()
        return s if s else None
    return str(remark)


def normalize_remark_for_response(remark):
    """
    Prepares a remark value for JSON API response (returning a list of remark dicts).
    Supports:
    - Lists of remark dicts: returned directly.
    - JSON strings encoding lists or dicts: parsed to list.
    - Plain strings: wrapped into [{'remark': s, 'created_at': None, 'user': None}].
    - None or empty: returns [].
    """
    if remark is None:
        return []
    if isinstance(remark, list):
        return remark
    if isinstance(remark, dict):
        return [remark]
    if isinstance(remark, str):
        s = remark.strip()
        if not s:
            return []
        if (s.startswith("[") and s.endswith("]")) or (s.startswith("{") and s.endswith("}")):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return parsed
                if isinstance(parsed, dict):
                    return [parsed]
            except Exception:
                pass
        return [{"remark": s, "created_at": None, "user": None}]
    return []


def deserialize_remark_for_entity(remark):
    """
    If remark is a JSON string of a list or dict, parse and return the list/dict.
    Otherwise return remark as is (e.g. string, list, dict, or None).
    """
    if isinstance(remark, str):
        s = remark.strip()
        if (s.startswith("[") and s.endswith("]")) or (s.startswith("{") and s.endswith("}")):
            try:
                return json.loads(s)
            except Exception:
                pass
        return s
    return remark


class RemarkField(fields.Field):
    """
    Marshmallow field that accepts strings, lists, dicts, or None,
    and upon serialization converts JSON-stringified remark lists/dicts back
    to Python objects.
    """
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return deserialize_remark_for_entity(value)

    def _deserialize(self, value, attr, data, **kwargs):
        return value


def get_step_remarks_for_response(
    project_id: int | None,
    step_number: int,
    fallback_raw=None,
    entity_id: int | None = None,
) -> list[dict]:
    """
    Returns remark objects from the step_remarks table for (project_id, step_number, entity_id).
    Falls back to deserializing and normalizing fallback_raw if no database remarks exist.
    """
    if not project_id or not step_number:
        return []
    from app.repositories.step_remark_repository import list_remarks_for_step
    from app.services.step_remark_service import serialize_remark

    db_remarks = [
        serialize_remark(r)
        for r in list_remarks_for_step(project_id, step_number, entity_id=entity_id)
    ]
    if db_remarks:
        return db_remarks

    # If entity_id was provided but no entity-scoped remarks exist, check for legacy un-scoped remarks
    if entity_id is not None:
        legacy_remarks = [
            serialize_remark(r)
            for r in list_remarks_for_step(project_id, step_number)
            if r.entity_id is None
        ]
        if legacy_remarks:
            return legacy_remarks

    return normalize_remark_for_response(deserialize_remark_for_entity(fallback_raw))

