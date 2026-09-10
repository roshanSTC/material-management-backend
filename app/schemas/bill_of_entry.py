from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal

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
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        raise ValidationError(f"Invalid date format: {val}. Expected YYYY-MM-DD.")


def _normalize_bill_of_entry_payload(raw_data):
    if not isinstance(raw_data, Mapping):
        return raw_data
    normalized = dict(raw_data)

    # Date normalization
    if "date" in normalized:
        d = _parse_date(normalized["date"])
        if d is not None:
            normalized["date"] = d.isoformat()
    elif "entry_date" in normalized:
        d = _parse_date(normalized["entry_date"])
        if d is not None:
            normalized["date"] = d.isoformat()

    # Alias normalization
    if "bill_of_entry_number" in normalized and "bill_of_entry_no" not in normalized:
        normalized["bill_of_entry_no"] = normalized["bill_of_entry_number"]

    # String stripping
    if "bill_of_entry_no" in normalized and isinstance(normalized["bill_of_entry_no"], str):
        normalized["bill_of_entry_no"] = normalized["bill_of_entry_no"].strip()
    if "remark" in normalized and isinstance(normalized["remark"], str):
        normalized["remark"] = normalized["remark"].strip()

    # Calculate total_duty if omitted
    if "total_duty" not in normalized or normalized.get("total_duty") is None:
        parts = [
            normalized.get("bcd"),
            normalized.get("sws"),
            normalized.get("igst"),
        ]
        if any(p is not None for p in parts):
            total = Decimal(0)
            for p in parts:
                if p is not None:
                    try:
                        total += Decimal(str(p))
                    except Exception:
                        pass
            normalized["total_duty"] = float(total)

    return normalized


class BillOfEntryCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True)
    bill_of_entry_no = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
    )
    date = fields.Date(required=True)
    total_assessable_value = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    bcd = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    sws = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    igst = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    total_duty = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    remark = fields.String(allow_none=True, load_default=None)

    @pre_load
    def prepare_data(self, data, **kwargs):
        return _normalize_bill_of_entry_payload(data)


class BillOfEntryUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    bill_of_entry_no = fields.String(
        required=False,
        validate=validate.Length(min=1, max=100),
    )
    date = fields.Date(required=False)
    total_assessable_value = fields.Decimal(
        as_string=False,
        allow_none=True,
    )
    bcd = fields.Decimal(
        as_string=False,
        allow_none=True,
    )
    sws = fields.Decimal(
        as_string=False,
        allow_none=True,
    )
    igst = fields.Decimal(
        as_string=False,
        allow_none=True,
    )
    total_duty = fields.Decimal(
        as_string=False,
        allow_none=True,
    )
    remark = fields.String(allow_none=True)

    @pre_load
    def prepare_data(self, data, **kwargs):
        return _normalize_bill_of_entry_payload(data)


class BillOfEntryQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, allow_none=True)


class BillOfEntryResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    bill_of_entry_no = fields.String(required=True)
    bill_of_entry_number = fields.String(allow_none=True)
    date = fields.Date(required=True)
    entry_date = fields.Date(allow_none=True)
    total_assessable_value = fields.Raw(allow_none=True)
    bcd = fields.Raw(allow_none=True)
    sws = fields.Raw(allow_none=True)
    igst = fields.Raw(allow_none=True)
    total_duty = fields.Raw(allow_none=True)
    remark = fields.String(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)

    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_default=[],
    )


class LatestBillOfEntryQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        resolved_id = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("projectId")
        )
        if resolved_id is not None and str(resolved_id).strip() != "":
            normalized["project_id"] = str(resolved_id).strip()
        return normalized


class LatestBillOfEntryResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    bcd = fields.Float(allow_none=True)
    sws = fields.Float(allow_none=True)
    igst = fields.Float(allow_none=True)
    duty = fields.Float(allow_none=True)

