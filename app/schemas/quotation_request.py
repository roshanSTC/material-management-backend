from datetime import date
from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.common import FlexibleDate, FlexibleInt


class QuotationRequestItemSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    sr_no = FlexibleInt(required=False, allow_none=True)
    description = fields.String(required=True, validate=validate.Length(min=1, max=500))
    quantity = fields.Decimal(
        required=False,
        as_string=True,
        places=3,
        allow_none=True,
    )


class QuotationRequestCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True)
    supplier_id = FlexibleInt(required=False, allow_none=True)
    supplier_name = fields.String(required=False, allow_none=True)
    request_date = FlexibleDate(required=False, allow_none=True, load_default=date.today)
    supplier_contacted = fields.Boolean(required=False, allow_none=True, load_default=True)
    form_code = fields.String(required=False, allow_none=True)
    attachments_count = FlexibleInt(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(QuotationRequestItemSchema),
        required=False,
        allow_none=True,
    )


class QuotationRequestResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    project_id = fields.Integer()
    supplier_id = fields.Integer()
    supplier_name = fields.String(allow_none=True)
    request_date = fields.Date()
    supplier_contacted = fields.Boolean()
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    items = fields.List(fields.Nested(QuotationRequestItemSchema))
    attachments = fields.List(fields.Dict())


class QuotationRequestQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=False,
        validate=validate.Range(min=1),
    )
    supplier_id = fields.Integer(
        required=False,
        validate=validate.Range(min=1),
    )


class LatestQuotationRequestQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=False,
        validate=validate.Range(min=1),
    )
