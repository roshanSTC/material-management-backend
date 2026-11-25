from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class WarrantyCertificateCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True)
    certificate_date = FlexibleDate(required=True)
    warranty_period = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
    )
    po_no = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    po_date = FlexibleDate(required=False, allow_none=True)
    invoice_no = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    invoice_date = FlexibleDate(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)


class WarrantyCertificateUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False)
    certificate_date = FlexibleDate(required=False)
    warranty_period = fields.String(
        required=False,
        validate=validate.Length(min=1, max=100),
    )
    po_no = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    po_date = FlexibleDate(required=False, allow_none=True)
    invoice_no = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    invoice_date = FlexibleDate(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)


class WarrantyCertificateResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    certificate_date = fields.Date(dump_only=True)
    warranty_period = fields.String(dump_only=True)
    po_no = fields.String(dump_only=True, allow_none=True)
    po_date = fields.Date(dump_only=True, allow_none=True)
    invoice_no = fields.String(dump_only=True, allow_none=True)
    invoice_date = fields.Date(dump_only=True, allow_none=True)
    remarks = fields.Raw(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_only=True,
        dump_default=[],
    )


class WarrantyCertificateQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    po_no = fields.String(required=False)
    invoice_no = fields.String(required=False)
