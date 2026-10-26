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
    except Exception:
        pass
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValidationError(f"Invalid date format: {val}. Expected YYYY-MM-DD.")


def _normalize_transport_detail_payload(raw_data):
    if not isinstance(raw_data, Mapping):
        return raw_data
    normalized = dict(raw_data)

    # Date normalization
    raw_date = (
        normalized.get("date")
        or normalized.get("lr_rr_awb_date")
        or normalized.get("lr_rr_date")
        or normalized.get("transport_date")
    )
    if raw_date is not None:
        d = _parse_date(raw_date)
        if d is not None:
            normalized["date"] = d.isoformat()
            normalized["lr_rr_awb_date"] = d.isoformat()
            normalized["transport_date"] = d.isoformat()

    # Mode normalization
    raw_mode = (
        normalized.get("transportation_mode")
        or normalized.get("transport_mode")
        or normalized.get("mode")
    )
    if raw_mode:
        m_str = str(raw_mode).strip().lower()
        if "air" in m_str:
            norm_mode = "air"
        elif "train" in m_str or "rail" in m_str:
            norm_mode = "train"
        elif "road" in m_str or "truck" in m_str:
            norm_mode = "road"
        else:
            norm_mode = m_str
        normalized["transport_mode"] = norm_mode
        normalized["transportation_mode"] = raw_mode
    elif "transport_mode" not in normalized:
        normalized["transport_mode"] = "road"
        normalized["transportation_mode"] = "Road"

    # Number aliases
    raw_no = (
        normalized.get("lr_rr_awb_no")
        or normalized.get("lr_no")
        or normalized.get("lr_number")
        or normalized.get("rr_no")
        or normalized.get("awb_no")
    )
    if raw_no:
        clean_no = str(raw_no).strip()
        normalized["lr_rr_awb_no"] = clean_no
        t_mode = normalized.get("transport_mode", "road")
        if t_mode == "air":
            if "awb_no" not in normalized:
                normalized["awb_no"] = clean_no
            if "lr_no" not in normalized:
                normalized["lr_no"] = clean_no
        elif t_mode == "train":
            if "rr_no" not in normalized:
                normalized["rr_no"] = clean_no
            if "lr_no" not in normalized:
                normalized["lr_no"] = clean_no
        else:
            if "lr_no" not in normalized:
                normalized["lr_no"] = clean_no

    # Charges normalization
    charges = (
        normalized.get("total_transportation_charges")
        or normalized.get("totalTransportationCharges")
        or normalized.get("transport_charges")
        or normalized.get("transportCharges")
    )
    if charges is not None and str(charges).strip() != "":
        normalized["transport_charges"] = charges
        normalized["total_transportation_charges"] = charges

    if "remarks" in normalized and not normalized.get("remark"):
        normalized["remark"] = normalized["remarks"]
    elif "remark" in normalized and not normalized.get("remarks"):
        normalized["remarks"] = normalized["remark"]

    # String trimming
    for field_name in (
        "lr_no",
        "rr_no",
        "awb_no",
        "lr_rr_awb_no",
        "from_location",
        "to_location",
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
    remark = fields.Raw(allow_none=True, load_default=None)
    remarks = fields.Raw(allow_none=True, load_default=None)

    # Aliases
    transportation_mode = fields.Raw(allow_none=True, load_default=None)
    lr_rr_awb_no = fields.String(allow_none=True, load_default=None)
    lr_rr_awb_date = fields.Date(allow_none=True, load_default=None)
    transport_date = fields.Date(allow_none=True, load_default=None)
    total_transportation_charges = fields.Decimal(allow_none=True, load_default=None)
    items = fields.Raw(allow_none=True, load_default=None)
    attachments_count = fields.Raw(allow_none=True, load_default=None)
    form_code = fields.Raw(allow_none=True, load_default=None)

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
    remark = fields.Raw(allow_none=True)
    remarks = fields.Raw(allow_none=True)

    # Aliases
    transportation_mode = fields.Raw(allow_none=True)
    lr_rr_awb_no = fields.String(allow_none=True)
    lr_rr_awb_date = fields.Date(allow_none=True)
    transport_date = fields.Date(allow_none=True)
    total_transportation_charges = fields.Decimal(allow_none=True)
    items = fields.Raw(allow_none=True)
    attachments_count = fields.Raw(allow_none=True)
    form_code = fields.Raw(allow_none=True)

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
    lr_rr_awb_date = fields.Date(dump_only=True)
    from_location = fields.String(dump_only=True)
    to_location = fields.String(dump_only=True)
    lr_no = fields.String(dump_only=True, allow_none=True)
    lr_number = fields.String(dump_only=True, allow_none=True)
    rr_no = fields.String(dump_only=True, allow_none=True)
    awb_no = fields.String(dump_only=True, allow_none=True)
    lr_rr_awb_no = fields.String(dump_only=True, allow_none=True)
    transport_charges = fields.Decimal(dump_only=True, as_string=False, allow_none=True)
    total_transportation_charges = fields.Decimal(dump_only=True, as_string=False, allow_none=True)
    remarks = fields.Raw(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_only=True,
        dump_default=[],
    )


class TransportDetailQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    transport_mode = fields.String(required=False)
    lr_no = fields.String(required=False)
