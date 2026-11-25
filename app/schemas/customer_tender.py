from decimal import Decimal
from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleDateTime, FlexibleInt


class CustomerTenderItemCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = FlexibleInt(required=False, allow_none=True)
    item_code = fields.String(required=False, allow_none=True)
    description = fields.String(required=True, validate=validate.Length(min=1, max=500))
    unit = fields.String(required=False, allow_none=True)
    quantity = fields.Decimal(
        required=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )


class CustomerTenderItemUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=False, allow_none=True)
    sr_no = FlexibleInt(required=False, allow_none=True)
    item_code = fields.String(required=False, allow_none=True)
    description = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1, max=500),
    )
    unit = fields.String(required=False, allow_none=True)
    quantity = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )


class CustomerTenderCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(
        required=True,
        validate=validate.Range(min=1),
    )
    customer_id = FlexibleInt(required=False, allow_none=True)
    customer_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    officer_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    email = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    address = fields.String(required=False, allow_none=True)
    website = fields.String(required=False, allow_none=True, validate=validate.Length(max=2048))
    contact_number = fields.String(required=False, allow_none=True, validate=validate.Length(max=30))
    tender_title = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    tender_no = fields.String(required=True, validate=validate.Length(min=1, max=100))
    tender_issue_date = FlexibleDate(required=False, allow_none=True)
    opening_date_time = FlexibleDateTime(required=False, allow_none=True)
    closing_date_time = FlexibleDateTime(required=False, allow_none=True)
    tender_fee = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    validity = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    delivery_terms = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    delivery_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    payment_terms = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    warranty_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(CustomerTenderItemCreateSchema),
        required=False,
        load_default=list,
    )


class CustomerTenderUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False, allow_none=True)
    customer_id = FlexibleInt(required=False, allow_none=True)
    customer_name = fields.String(required=False, allow_none=True)
    officer_name = fields.String(required=False, allow_none=True)
    email = fields.String(required=False, allow_none=True)
    address = fields.String(required=False, allow_none=True)
    website = fields.String(required=False, allow_none=True)
    contact_number = fields.String(required=False, allow_none=True)
    tender_title = fields.String(required=False, allow_none=True)
    tender_no = fields.String(required=False, allow_none=True)
    tender_issue_date = FlexibleDate(required=False, allow_none=True)
    opening_date_time = FlexibleDateTime(required=False, allow_none=True)
    closing_date_time = FlexibleDateTime(required=False, allow_none=True)
    tender_fee = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    validity = fields.String(required=False, allow_none=True)
    delivery_terms = fields.String(required=False, allow_none=True)
    delivery_period = fields.String(required=False, allow_none=True)
    payment_terms = fields.String(required=False, allow_none=True)
    warranty_period = fields.String(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(CustomerTenderItemUpdateSchema),
        required=False,
        allow_none=True,
    )


class CustomerTenderQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, validate=validate.Range(min=1))
    latest = fields.Raw(required=False, allow_none=True)
    enquiry_only = fields.Raw(required=False, allow_none=True)
    tender_only = fields.Raw(required=False, allow_none=True)


class LatestCustomerTenderQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True, validate=validate.Range(min=1))


class CustomerTenderItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    sr_no = fields.Integer(allow_none=True)
    customer_tender_id = fields.Integer(required=True)
    item_code = fields.String(allow_none=True)
    description = fields.String(required=True)
    unit = fields.String(allow_none=True, dump_default="NOS")
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    created_at = fields.DateTime(required=True)


class CustomerTenderResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    customer_id = fields.Integer(allow_none=True)
    customer_name = fields.String(allow_none=True)
    officer_name = fields.String(allow_none=True)
    email = fields.String(allow_none=True)
    address = fields.String(allow_none=True)
    website = fields.String(allow_none=True)
    contact_number = fields.String(allow_none=True)
    tender_title = fields.String(allow_none=True)
    tender_no = fields.String(required=True)
    tender_issue_date = fields.Date(allow_none=True)
    opening_date_time = fields.DateTime(allow_none=True)
    closing_date_time = fields.DateTime(allow_none=True)
    tender_fee = fields.Decimal(as_string=True, places=2, allow_none=True)
    validity = fields.String(allow_none=True)
    delivery_terms = fields.String(allow_none=True)
    delivery_period = fields.String(allow_none=True)
    payment_terms = fields.String(allow_none=True)
    warranty_period = fields.String(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(
        fields.Nested(CustomerTenderItemResponseSchema),
        required=True,
    )
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        required=False,
    )


class LatestCustomerTenderItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = fields.Integer(allow_none=True)
    description = fields.String(required=True)
    unit = fields.String(allow_none=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)


class LatestCustomerTenderResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    customer_id = fields.Integer(allow_none=True)
    customer_name = fields.String(allow_none=True)
    tender_title = fields.String(allow_none=True)
    tender_no = fields.String(required=True)
    tender_issue_date = fields.Date(allow_none=True)
    delivery_terms = fields.String(allow_none=True)
    delivery_period = fields.String(allow_none=True)
    payment_terms = fields.String(allow_none=True)
    validity = fields.String(allow_none=True)
    warranty_period = fields.String(allow_none=True)
    items = fields.List(
        fields.Nested(LatestCustomerTenderItemResponseSchema),
        required=True,
    )


class LatestPacTenderResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(allow_none=True)
    project_id = fields.Integer(allow_none=True)
    customer_name = fields.String(allow_none=True)
    tender_title = fields.String(allow_none=True)
    tender_no = fields.String(allow_none=True)
    tender_issue_date = fields.Date(allow_none=True)
    closing_date_time = fields.DateTime(allow_none=True)


class LatestPacTenderQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, allow_none=True)
