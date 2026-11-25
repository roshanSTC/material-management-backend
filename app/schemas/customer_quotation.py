from datetime import date
from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class CustomerQuotationItemSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = FlexibleInt(required=False, allow_none=True)
    cost_sheet_item_id = fields.Integer(required=False, allow_none=True)
    item_code = fields.String(required=False, allow_none=True)
    description = fields.String(required=True, validate=validate.Length(min=1, max=500))
    hsn_sac = fields.String(required=False, allow_none=True)
    quantity = fields.Decimal(
        required=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=0.001),
    )
    unit_price = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0),
    )
    total_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0),
    )
    customs_duty_rate = fields.Float(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0),
    )


class CustomerQuotationCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(
        required=True,
        validate=validate.Range(min=1),
    )
    customer_id = FlexibleInt(required=False, allow_none=True)
    customer_name = fields.String(required=False, allow_none=True)
    quotation_no = fields.String(required=True, validate=validate.Length(min=1, max=100))
    quotation_date = FlexibleDate(required=False, allow_none=True, load_default=date.today)
    quotation_value = fields.Raw(required=False, allow_none=True)
    currency_unit = fields.String(required=False, allow_none=True)
    currency_symbol = fields.String(required=False, allow_none=True)
    total_net_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    quotation_validity = fields.String(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(CustomerQuotationItemSchema),
        required=True,
        validate=validate.Length(min=1),
    )


class CustomerQuotationUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(
        required=False,
        validate=validate.Range(min=1),
    )
    customer_id = FlexibleInt(required=False, allow_none=True)
    customer_name = fields.String(required=False, allow_none=True)
    quotation_no = fields.String(required=False, validate=validate.Length(min=1, max=100))
    quotation_date = FlexibleDate(required=False, allow_none=True)
    quotation_value = fields.Raw(required=False, allow_none=True)
    currency_unit = fields.String(required=False, allow_none=True)
    currency_symbol = fields.String(required=False, allow_none=True)
    total_net_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    quotation_validity = fields.String(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(CustomerQuotationItemSchema),
        required=False,
    )


class CustomerQuotationQuerySchema(Schema):
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
    quotation_no = fields.String(required=False)


class CustomerQuotationItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    sr_no = fields.Integer(allow_none=True)
    customer_quotation_id = fields.Integer(required=True)
    cost_sheet_item_id = fields.Integer(allow_none=True)
    item_code = fields.String(allow_none=True)
    description = fields.String(required=True)
    hsn_sac = fields.String(allow_none=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    customs_duty_rate = fields.Float(allow_none=True)
    created_at = fields.DateTime(required=True)


class CustomerQuotationResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    customer_id = fields.Integer(required=True)
    customer_name = fields.String(allow_none=True)
    quotation_no = fields.String(required=True)
    quotation_date = fields.Date(required=True)
    quotation_value = fields.Decimal(as_string=True, places=2, required=True)
    currency_unit = fields.String(allow_none=True)
    currency_symbol = fields.String(allow_none=True)
    total_net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    quotation_validity = fields.String(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(
        fields.Nested(CustomerQuotationItemResponseSchema),
        required=True,
    )
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        required=True,
    )


class LatestCustomerQuotationQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )


class LatestCustomerQuotationResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    items = fields.List(
        fields.Nested(CustomerQuotationItemResponseSchema),
        required=True,
    )
