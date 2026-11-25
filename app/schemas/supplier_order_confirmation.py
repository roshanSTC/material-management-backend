from decimal import Decimal
from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class SupplierOrderConfirmationItemCreateSchema(Schema):
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
    unit_price = fields.Decimal(required=True, as_string=True, places=2)
    total_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)


class SupplierOrderConfirmationItemUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=False, allow_none=True)
    sr_no = FlexibleInt(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True, validate=validate.Length(min=1, max=500))
    hsn_sac = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    quantity = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )
    unit_price = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)


class SupplierOrderConfirmationCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True, validate=validate.Range(min=1))
    supplier_id = FlexibleInt(required=False, allow_none=True)
    supplier_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    purchase_order_id = FlexibleInt(required=False, allow_none=True)
    order_confirmation_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    order_confirmation_date = FlexibleDate(required=True)
    email = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    incoterms = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    delivery_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    payment_terms = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    warranty_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    total_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    currency_unit = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(SupplierOrderConfirmationItemCreateSchema),
        required=False,
        load_default=list,
    )


class SupplierOrderConfirmationUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False, allow_none=True)
    supplier_id = FlexibleInt(required=False, allow_none=True)
    supplier_name = fields.String(required=False, allow_none=True)
    purchase_order_id = FlexibleInt(required=False, allow_none=True)
    order_confirmation_no = fields.String(required=False, allow_none=True)
    order_confirmation_date = FlexibleDate(required=False, allow_none=True)
    email = fields.String(required=False, allow_none=True)
    incoterms = fields.String(required=False, allow_none=True)
    delivery_period = fields.String(required=False, allow_none=True)
    payment_terms = fields.String(required=False, allow_none=True)
    warranty_period = fields.String(required=False, allow_none=True)
    total_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    currency_unit = fields.String(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(SupplierOrderConfirmationItemUpdateSchema),
        required=False,
        allow_none=True,
    )


class SupplierOrderConfirmationQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, validate=validate.Range(min=1))


class SupplierOrderConfirmationItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    sr_no = fields.Integer(allow_none=True)
    order_confirmation_id = fields.Integer(required=True)
    description = fields.String(required=True)
    hsn_sac = fields.String(allow_none=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, required=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    created_at = fields.DateTime(required=True)


class SupplierOrderConfirmationResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=False, allow_none=True)
    supplier_name = fields.String(allow_none=True)
    purchase_order_id = fields.Integer(allow_none=True)
    order_confirmation_no = fields.String(allow_none=True)
    order_confirmation_date = fields.Date(required=True)
    email = fields.String(allow_none=True)
    incoterms = fields.String(allow_none=True)
    delivery_period = fields.String(allow_none=True)
    payment_terms = fields.String(allow_none=True)
    warranty_period = fields.String(allow_none=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    currency_unit = fields.String(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(
        fields.Nested(SupplierOrderConfirmationItemResponseSchema),
        required=True,
    )
    attachments = fields.List(fields.Nested(AttachmentResponseSchema), required=False)


class LatestSupplierOrderConfirmationQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True, validate=validate.Range(min=1))


class LatestSupplierOrderConfirmationItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = fields.Integer(allow_none=True)
    description = fields.String(allow_none=True)
    hsn_sac = fields.String(allow_none=True)
    unit_price = fields.Decimal(as_string=True, places=2, required=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)


class LatestSupplierOrderConfirmationResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    payment_terms = fields.String(allow_none=True)
    warranty_period = fields.String(allow_none=True)
    incoterms = fields.String(allow_none=True)
    delivery_period = fields.String(allow_none=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    currency_unit = fields.String(allow_none=True)
    items = fields.List(
        fields.Nested(LatestSupplierOrderConfirmationItemResponseSchema),
        required=True,
    )
