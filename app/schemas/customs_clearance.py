from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class CustomsClearanceItemSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    sr_no = FlexibleInt(required=False, allow_none=True)
    description = fields.String(required=True, validate=validate.Length(min=1, max=500))
    amount = fields.Decimal(as_string=False, required=False, allow_none=True)


class CustomsClearanceCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True)
    freight_forwarder_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    cha_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    invoice_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    invoice_date = FlexibleDate(required=False, allow_none=True)
    invoice_amount = fields.Decimal(as_string=False, required=False, allow_none=True)
    payment_date = FlexibleDate(required=False, allow_none=True)
    payment_amount = fields.Decimal(as_string=False, required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(fields.Nested(CustomsClearanceItemSchema), required=False, load_default=[])


class CustomsClearanceUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False, allow_none=True)
    freight_forwarder_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    cha_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    invoice_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    invoice_date = FlexibleDate(required=False, allow_none=True)
    invoice_amount = fields.Decimal(as_string=False, required=False, allow_none=True)
    payment_date = FlexibleDate(required=False, allow_none=True)
    payment_amount = fields.Decimal(as_string=False, required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(fields.Nested(CustomsClearanceItemSchema), required=False, allow_none=True)


class CustomsClearanceQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(allow_none=True)


class CustomsClearanceResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    freight_forwarder_name = fields.String(allow_none=True)
    cha_name = fields.String(allow_none=True)
    invoice_no = fields.String(allow_none=True)
    invoice_date = fields.Date(allow_none=True)
    invoice_amount = fields.Decimal(as_string=False, allow_none=True)
    payment_date = fields.Date(allow_none=True)
    payment_amount = fields.Decimal(as_string=False, allow_none=True)
    items = fields.List(fields.Nested(CustomsClearanceItemSchema), dump_default=[])
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_default=[],
    )
