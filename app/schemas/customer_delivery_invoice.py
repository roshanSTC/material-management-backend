from decimal import Decimal
from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


def _not_blank(value: str) -> None:
    if not value or not str(value).strip():
        raise ValidationError("Field must not be blank.")


class CustomerDeliveryInvoiceItemCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = FlexibleInt(required=False, allow_none=True)
    description = fields.String(required=True, validate=validate.Length(min=1, max=500))
    hsn_sac = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    quantity = fields.Decimal(
        required=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )
    unit_price = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )
    total_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )


class CustomerDeliveryInvoiceItemUpdateSchema(CustomerDeliveryInvoiceItemCreateSchema):
    id = fields.Integer(required=False, allow_none=True)
    description = fields.String(required=False, validate=validate.Length(min=1, max=500))
    quantity = fields.Decimal(
        required=False,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )
    unit_price = fields.Decimal(
        required=False,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )


class CustomerDeliveryInvoiceItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    sr_no = fields.Integer(dump_only=True)
    invoice_id = fields.Integer(dump_only=True)
    description = fields.String(dump_only=True)
    hsn_sac = fields.String(dump_only=True)
    quantity = fields.Decimal(dump_only=True, as_string=True, places=3)
    unit_price = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class CustomerDeliveryInvoiceCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True)
    customer_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    invoice_no = fields.String(required=True, validate=validate.Length(min=1, max=100))
    invoice_date = FlexibleDate(required=True)
    gst_pct = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    gst_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    round_off = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_gross_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    status = fields.String(required=False, allow_none=True)
    form_code = fields.String(required=False, allow_none=True)
    attachments_count = FlexibleInt(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(CustomerDeliveryInvoiceItemCreateSchema),
        required=False,
        load_default=list,
    )


class CustomerDeliveryInvoiceUpdateSchema(CustomerDeliveryInvoiceCreateSchema):
    project_id = FlexibleInt(required=False, allow_none=True)
    invoice_no = fields.String(required=False, allow_none=True, validate=validate.Length(min=1, max=100))
    invoice_date = FlexibleDate(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(CustomerDeliveryInvoiceItemUpdateSchema),
        required=False,
        allow_none=True,
    )


class CustomerDeliveryInvoiceResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    customer_name = fields.String(dump_only=True)
    invoice_no = fields.String(dump_only=True)
    invoice_date = fields.Date(dump_only=True)
    gst_pct = fields.Decimal(dump_only=True, as_string=True, places=2)
    gst_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    round_off = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_gross_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    form_code = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    attachments_count = fields.Integer(dump_only=True)
    remarks = fields.Raw(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    items = fields.List(
        fields.Nested(CustomerDeliveryInvoiceItemResponseSchema),
        dump_only=True,
    )
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_only=True,
    )


class CustomerDeliveryInvoiceQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)


class LatestCustomerDeliveryInvoiceQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True)


class LatestCustomerDeliveryInvoiceResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    invoice_no = fields.String(dump_only=True)
    invoice_date = fields.Date(dump_only=True)
    total_net_amount = fields.Decimal(as_string=True, places=2, dump_only=True)
    total_gross_amount = fields.Decimal(as_string=True, places=2, dump_only=True)
