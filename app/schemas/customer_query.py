from datetime import date
from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class CustomerQueryItemSchema(Schema):
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


class CustomerQueryCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(
        required=True,
        validate=validate.Range(min=1),
    )
    customer_id = FlexibleInt(required=False, allow_none=True)
    customer_name = fields.String(required=False, allow_none=True)
    query_date = FlexibleDate(required=False, allow_none=True, load_default=date.today)
    form_code = fields.String(required=False, allow_none=True)
    attachments_count = FlexibleInt(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(CustomerQueryItemSchema),
        required=False,
        allow_none=True,
    )


class CustomerQueryItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    sr_no = fields.Integer(allow_none=True)
    description = fields.String(required=True)
    quantity = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
    )


class CustomerQueryResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    customer_id = fields.Integer(required=True)
    customer_name = fields.String(allow_none=True)
    query_date = fields.Date(required=True)
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(
        fields.Nested(CustomerQueryItemResponseSchema),
        required=True,
    )
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        required=True,
    )


class CustomerQueryUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False, allow_none=True)
    customer_id = FlexibleInt(required=False, allow_none=True)
    customer_name = fields.String(required=False, allow_none=True)
    query_date = FlexibleDate(required=False, allow_none=True)
    form_code = fields.String(required=False, allow_none=True)
    attachments_count = FlexibleInt(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(CustomerQueryItemSchema),
        required=False,
        allow_none=True,
    )


class CustomerQueryQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=False,
        validate=validate.Range(min=1),
    )
    customer_id = fields.Integer(
        required=False,
        validate=validate.Range(min=1),
    )


class LatestCustomerQueryQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )


class LatestCustomerQueryItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = fields.Integer(allow_none=True)
    description = fields.String(required=True)
    quantity = fields.Decimal(as_string=True, places=3, allow_none=True)


class LatestCustomerQueryResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    items = fields.List(
        fields.Nested(LatestCustomerQueryItemResponseSchema),
        required=True,
    )
