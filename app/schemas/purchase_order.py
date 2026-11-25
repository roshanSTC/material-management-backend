from decimal import Decimal
from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class PurchaseOrderItemCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = FlexibleInt(required=False, allow_none=True)
    description = fields.String(required=True, validate=validate.Length(min=1, max=500))
    hsn_sac = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    unit = fields.String(required=False, allow_none=True, load_default="NOS")
    quantity = fields.Decimal(
        required=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )
    unit_price = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_price = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    delivery_date = FlexibleDate(required=False, allow_none=True)


class PurchaseOrderItemUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=False, allow_none=True)
    sr_no = FlexibleInt(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True, validate=validate.Length(min=1, max=500))
    hsn_sac = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    unit = fields.String(required=False, allow_none=True)
    quantity = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )
    unit_price = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_price = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    delivery_date = FlexibleDate(required=False, allow_none=True)


class PurchaseOrderCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True, validate=validate.Range(min=1))
    customer_id = FlexibleInt(required=False, allow_none=True)
    customer_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    tender_id = FlexibleInt(required=False, allow_none=True)
    poc_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    email = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    contact = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    po_no = fields.String(required=True, validate=validate.Length(min=1, max=100))
    po_title = fields.String(required=True, validate=validate.Length(min=1, max=255))
    po_date = FlexibleDate(required=True)
    delivery_date = FlexibleDate(required=False, allow_none=True)
    delivery_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    delivery_terms = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    payment_terms = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    warranty_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    gst_rate_pct = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    gst_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_gross_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(PurchaseOrderItemCreateSchema),
        required=False,
        load_default=list,
    )


class PurchaseOrderUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False, allow_none=True)
    customer_id = FlexibleInt(required=False, allow_none=True)
    customer_name = fields.String(required=False, allow_none=True)
    tender_id = FlexibleInt(required=False, allow_none=True)
    poc_name = fields.String(required=False, allow_none=True)
    email = fields.String(required=False, allow_none=True)
    contact = fields.String(required=False, allow_none=True)
    po_no = fields.String(required=False, allow_none=True)
    po_title = fields.String(required=False, allow_none=True)
    po_date = FlexibleDate(required=False, allow_none=True)
    delivery_date = FlexibleDate(required=False, allow_none=True)
    delivery_period = fields.String(required=False, allow_none=True)
    delivery_terms = fields.String(required=False, allow_none=True)
    payment_terms = fields.String(required=False, allow_none=True)
    warranty_period = fields.String(required=False, allow_none=True)
    gst_rate_pct = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    gst_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_gross_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(PurchaseOrderItemUpdateSchema),
        required=False,
        allow_none=True,
    )


class PurchaseOrderQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, validate=validate.Range(min=1))


class LatestPurchaseOrderQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=1))
    po_no = fields.String(required=False, allow_none=True)


class PurchaseOrderItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    sr_no = fields.Integer(allow_none=True)
    purchase_order_id = fields.Integer(required=True)
    description = fields.String(required=True)
    hsn_sac = fields.String(allow_none=True)
    unit = fields.String(allow_none=True, dump_default="NOS")
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    delivery_date = fields.Date(allow_none=True)
    created_at = fields.DateTime(required=True)


class PurchaseOrderResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    customer_id = fields.Integer(required=True)
    customer_name = fields.String(allow_none=True)
    tender_id = fields.Integer(allow_none=True)
    poc_name = fields.String(allow_none=True)
    email = fields.String(allow_none=True)
    contact = fields.String(allow_none=True)
    po_no = fields.String(required=True)
    po_title = fields.String(required=True)
    po_date = fields.Date(required=True)
    delivery_date = fields.Date(allow_none=True)
    delivery_terms = fields.String(allow_none=True)
    payment_terms = fields.String(allow_none=True)
    warranty_period = fields.String(allow_none=True)
    gst_rate_pct = fields.Decimal(as_string=True, places=2, allow_none=True)
    gst_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_gross_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(fields.Nested(PurchaseOrderItemResponseSchema), required=True)
    attachments = fields.List(fields.Nested(AttachmentResponseSchema), required=False)


class LatestPurchaseOrderItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = fields.Integer(allow_none=True)
    description = fields.String(allow_none=True)
    hsn_sac = fields.String(allow_none=True)
    unit = fields.String(allow_none=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    delivery_date = fields.Date(allow_none=True)


class LatestPurchaseOrderResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    po_no = fields.String(allow_none=True)
    po_date = fields.Date(allow_none=True)
    gst_rate_pct = fields.Decimal(as_string=True, places=2, allow_none=True)
    gst_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_gross_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    items = fields.List(fields.Nested(LatestPurchaseOrderItemResponseSchema), required=True)
