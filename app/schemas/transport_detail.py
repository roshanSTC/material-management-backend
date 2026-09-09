from collections.abc import Mapping
from datetime import date, datetime

from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    pre_load,
    validate,
)

from app.schemas.attachment import AttachmentResponseSchema


def _parse_date(val):
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    if not s:
        return None
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        return date.fromisoformat(s[:10])
    except ValueError:
        raise ValidationError(f"Invalid date format: {val}. Expected YYYY-MM-DD.")


def _normalize_transport_detail_payload(raw_data):
    if not isinstance(raw_data, Mapping):
        return raw_data
    normalized = dict(raw_data)

    # Date normalization
    if "date" in normalized and normalized["date"] is not None:
        d = _parse_date(normalized["date"])
        if d is not None:
            normalized["date"] = d.isoformat()
    elif "transport_date" in normalized and normalized["transport_date"] is not None:
        d = _parse_date(normalized["transport_date"])
        if d is not None:
            normalized["date"] = d.isoformat()

    # Mode normalization
    if "transportation_mode" in normalized and "transport_mode" not in normalized:
        normalized["transport_mode"] = normalized["transportation_mode"]
    if "transport_mode" in normalized and isinstance(normalized["transport_mode"], str):
        normalized["transport_mode"] = normalized["transport_mode"].strip().lower()

    # Aliases
    if "lr_number" in normalized and "lr_no" not in normalized:
        normalized["lr_no"] = normalized["lr_number"]
    if "remarks" in normalized and "remark" not in normalized:
        normalized["remark"] = normalized["remarks"]

    # String trimming
    for field_name in (
        "lr_no",
        "rr_no",
        "awb_no",
        "from_location",
        "to_location",
        "remark",
    ):
        if field_name in normalized and isinstance(normalized[field_name], str):
            normalized[field_name] = normalized[field_name].strip()

    return normalized


class TransportDetailCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True)
    transport_mode = fields.String(
        required=True,
        validate=validate.OneOf(
            ["road", "train", "air"],
            error="transport_mode must be one of: road, train, air.",
        ),
    )
    date = fields.Date(required=True)
    from_location = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
    )
    to_location = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
    )
    lr_no = fields.String(allow_none=True, load_default=None)
    rr_no = fields.String(allow_none=True, load_default=None)
    awb_no = fields.String(allow_none=True, load_default=None)
    transport_charges = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    remark = fields.String(allow_none=True, load_default=None)

    @pre_load
    def preprocess(self, data, **kwargs):
        return _normalize_transport_detail_payload(data)


class TransportDetailUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    transport_mode = fields.String(
        required=False,
        validate=validate.OneOf(
            ["road", "train", "air"],
            error="transport_mode must be one of: road, train, air.",
        ),
    )
    date = fields.Date(required=False)
    from_location = fields.String(
        required=False,
        validate=validate.Length(min=1, max=255),
    )
    to_location = fields.String(
        required=False,
        validate=validate.Length(min=1, max=255),
    )
    lr_no = fields.String(allow_none=True)
    rr_no = fields.String(allow_none=True)
    awb_no = fields.String(allow_none=True)
    transport_charges = fields.Decimal(as_string=False, allow_none=True)
    remark = fields.String(allow_none=True)

    @pre_load
    def preprocess(self, data, **kwargs):
        return _normalize_transport_detail_payload(data)


class TransportDetailResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    transport_mode = fields.String(dump_only=True)
    transportation_mode = fields.String(dump_only=True)
    date = fields.Date(dump_only=True)
    transport_date = fields.Date(dump_only=True)
    from_location = fields.String(dump_only=True)
    to_location = fields.String(dump_only=True)
    lr_no = fields.String(dump_only=True, allow_none=True)
    lr_number = fields.String(dump_only=True, allow_none=True)
    rr_no = fields.String(dump_only=True, allow_none=True)
    awb_no = fields.String(dump_only=True, allow_none=True)
    transport_charges = fields.Decimal(dump_only=True, as_string=False, allow_none=True)
    remark = fields.String(dump_only=True, allow_none=True)
    remarks = fields.String(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_only=True,
        dump_default=[],
    )


class TransportDetailQuerySchema(Schema):
    project_id = fields.Integer(required=False)
    transport_mode = fields.String(required=False)
    lr_no = fields.String(required=False)
