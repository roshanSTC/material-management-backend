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


def _normalize_customs_clearance_payload(raw_data):
    if not isinstance(raw_data, Mapping):
        return raw_data
    normalized = dict(raw_data)

    # Date parsing
    if "boe_date" in normalized:
        d = _parse_date(normalized["boe_date"])
        if d is not None:
            normalized["boe_date"] = d.isoformat()
    if "duty_paid_date" in normalized:
        d = _parse_date(normalized["duty_paid_date"])
        if d is not None:
            normalized["duty_paid_date"] = d.isoformat()

    # Aliases
    if "customs_location_port" in normalized and "customs_location" not in normalized:
        normalized["customs_location"] = normalized["customs_location_port"]
    if "challan_number" in normalized and "challan_no" not in normalized:
        normalized["challan_no"] = normalized["challan_number"]
    if "transaction_payment_reference" in normalized and "transaction_ref_no" not in normalized:
        normalized["transaction_ref_no"] = normalized["transaction_payment_reference"]
    if "bill_of_entry_number" in normalized and "bill_of_entry_no" not in normalized:
        normalized["bill_of_entry_no"] = normalized["bill_of_entry_number"]

    # Trimming strings
    for k in (
        "cha_name",
        "bill_of_entry_no",
        "customs_location",
        "challan_no",
        "cfs_name",
        "transaction_ref_no",
        "remark",
    ):
        if k in normalized and isinstance(normalized[k], str):
            normalized[k] = normalized[k].strip()

    # Calculate total_customs_amount if omitted
    if "total_customs_amount" not in normalized or normalized.get("total_customs_amount") is None:
        parts = [
            normalized.get("duty_amount"),
            normalized.get("igst_amount"),
            normalized.get("other_customs_charges"),
        ]
        if any(p is not None for p in parts):
            total = Decimal(0)
            for p in parts:
                if p is not None:
                    try:
                        total += Decimal(str(p))
                    except Exception:
                        pass
            normalized["total_customs_amount"] = float(total)

    return normalized


class CustomsClearanceCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True)
    cha_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
    )
    bill_of_entry_no = fields.String(
        allow_none=True,
        load_default=None,
        validate=validate.Length(max=100),
    )
    boe_date = fields.Date(allow_none=True, load_default=None)
    customs_location = fields.String(
        allow_none=True,
        load_default=None,
        validate=validate.Length(max=255),
    )
    duty_paid_date = fields.Date(allow_none=True, load_default=None)
    challan_no = fields.String(
        allow_none=True,
        load_default=None,
        validate=validate.Length(max=100),
    )
    cfs_name = fields.String(
        allow_none=True,
        load_default=None,
        validate=validate.Length(max=255),
    )
    transaction_ref_no = fields.String(
        allow_none=True,
        load_default=None,
        validate=validate.Length(max=255),
    )
    duty_amount = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    igst_amount = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    other_customs_charges = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    total_customs_amount = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    remark = fields.String(allow_none=True, load_default=None)

    @pre_load
    def normalize_input(self, data, **kwargs):
        return _normalize_customs_clearance_payload(data)


class CustomsClearanceUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(allow_none=True)
    cha_name = fields.String(
        allow_none=True,
        validate=validate.Length(min=1, max=255),
    )
    bill_of_entry_no = fields.String(
        allow_none=True,
        validate=validate.Length(max=100),
    )
    boe_date = fields.Date(allow_none=True)
    customs_location = fields.String(
        allow_none=True,
        validate=validate.Length(max=255),
    )
    duty_paid_date = fields.Date(allow_none=True)
    challan_no = fields.String(
        allow_none=True,
        validate=validate.Length(max=100),
    )
    cfs_name = fields.String(
        allow_none=True,
        validate=validate.Length(max=255),
    )
    transaction_ref_no = fields.String(
        allow_none=True,
        validate=validate.Length(max=255),
    )
    duty_amount = fields.Decimal(as_string=False, allow_none=True)
    igst_amount = fields.Decimal(as_string=False, allow_none=True)
    other_customs_charges = fields.Decimal(as_string=False, allow_none=True)
    total_customs_amount = fields.Decimal(as_string=False, allow_none=True)
    remark = fields.String(allow_none=True)

    @pre_load
    def normalize_input(self, data, **kwargs):
        return _normalize_customs_clearance_payload(data)


class CustomsClearanceQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(allow_none=True)
    bill_of_entry_no = fields.String(allow_none=True)
    challan_no = fields.String(allow_none=True)


class CustomsClearanceResponseSchema(Schema):
    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    bill_of_entry_id = fields.Integer(allow_none=True)
    cha_name = fields.String(required=True)
    bill_of_entry_no = fields.String(allow_none=True)
    bill_of_entry_number = fields.String(allow_none=True)
    boe_date = fields.Date(allow_none=True)
    customs_location = fields.String(allow_none=True)
    customs_location_port = fields.String(allow_none=True)
    duty_paid_date = fields.Date(allow_none=True)
    challan_no = fields.String(allow_none=True)
    challan_number = fields.String(allow_none=True)
    cfs_name = fields.String(allow_none=True)
    transaction_ref_no = fields.String(allow_none=True)
    transaction_payment_reference = fields.String(allow_none=True)
    duty_amount = fields.Decimal(as_string=False, allow_none=True)
    igst_amount = fields.Decimal(as_string=False, allow_none=True)
    other_customs_charges = fields.Decimal(as_string=False, allow_none=True)
    total_customs_amount = fields.Decimal(as_string=False, allow_none=True)
    remark = fields.String(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_default=[],
    )
