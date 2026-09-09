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
        if 'T' in s:
            return datetime.fromisoformat(s.replace('Z', '+00:00')).date()
        return date.fromisoformat(s[:10])
    except ValueError:
        raise ValidationError(f'Invalid date format: {val}. Expected YYYY-MM-DD.')


def _normalize_warranty_certificate_payload(raw_data):
    if not isinstance(raw_data, Mapping):
        return raw_data
    normalized = dict(raw_data)

    # Date normalization
    for date_field in ('certificate_date', 'po_date', 'invoice_date'):
        if date_field in normalized and normalized[date_field] is not None:
            d = _parse_date(normalized[date_field])
            if d is not None:
                normalized[date_field] = d.isoformat()

    # Alias normalization
    if 'po_number' in normalized and 'po_no' not in normalized:
        normalized['po_no'] = normalized['po_number']
    if 'invoice_number' in normalized and 'invoice_no' not in normalized:
        normalized['invoice_no'] = normalized['invoice_number']
    if 'remarks' in normalized and 'remark' not in normalized:
        normalized['remark'] = normalized['remarks']

    # String trimming
    for str_field in ('warranty_period', 'po_no', 'invoice_no'):
        if str_field in normalized and isinstance(normalized[str_field], str):
            normalized[str_field] = normalized[str_field].strip()

    return normalized


class WarrantyCertificateCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True)
    certificate_date = fields.Date(required=True)
    warranty_period = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
    )
    po_no = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    po_date = fields.Date(required=False, allow_none=True)
    invoice_no = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    invoice_date = fields.Date(required=False, allow_none=True)
    remark = fields.String(required=False, allow_none=True)

    @pre_load
    def preprocess(self, data, **kwargs):
        return _normalize_warranty_certificate_payload(data)


class WarrantyCertificateUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    certificate_date = fields.Date(required=False)
    warranty_period = fields.String(
        required=False,
        validate=validate.Length(min=1, max=100),
    )
    po_no = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    po_date = fields.Date(required=False, allow_none=True)
    invoice_no = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    invoice_date = fields.Date(required=False, allow_none=True)
    remark = fields.String(required=False, allow_none=True)

    @pre_load
    def preprocess(self, data, **kwargs):
        return _normalize_warranty_certificate_payload(data)


class WarrantyCertificateResponseSchema(Schema):
    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    certificate_date = fields.Date(dump_only=True)
    warranty_period = fields.String(dump_only=True)
    po_no = fields.String(dump_only=True, allow_none=True)
    po_number = fields.String(dump_only=True, allow_none=True)
    po_date = fields.Date(dump_only=True, allow_none=True)
    invoice_no = fields.String(dump_only=True, allow_none=True)
    invoice_number = fields.String(dump_only=True, allow_none=True)
    invoice_date = fields.Date(dump_only=True, allow_none=True)
    remark = fields.String(dump_only=True, allow_none=True)
    remarks = fields.String(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_only=True,
        load_default=[],
    )


class WarrantyCertificateQuerySchema(Schema):
    project_id = fields.Integer(required=False)
    po_no = fields.String(required=False)
    invoice_no = fields.String(required=False)
