from decimal import Decimal
from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class SupplierProformaInvoiceItemCreateSchema(Schema):
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
        validate=validate.Range(min=Decimal("0.00")),
    )


class SupplierProformaInvoiceItemUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=False, allow_none=True)
    sr_no = FlexibleInt(required=False, allow_none=True)
    description = fields.String(required=False, validate=validate.Length(min=1, max=500))
    hsn_sac = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
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
    total_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )


class SupplierProformaInvoiceCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True, validate=validate.Range(min=1))
    supplier_id = FlexibleInt(required=False, allow_none=True)
    supplier_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    order_confirmation_id = FlexibleInt(required=False, allow_none=True)
    proforma_invoice_no = fields.String(required=True, validate=validate.Length(min=1, max=100))
    proforma_invoice_date = FlexibleDate(required=True)
    incoterms = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    delivery_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    delivery_date = FlexibleDate(required=False, allow_none=True)
    payment_terms = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    warranty_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    total_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(SupplierProformaInvoiceItemCreateSchema),
        required=False,
        load_default=list,
    )


class SupplierProformaInvoiceUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False, validate=validate.Range(min=1))
    supplier_id = FlexibleInt(required=False, allow_none=True)
    supplier_name = fields.String(required=False, allow_none=True)
    order_confirmation_id = FlexibleInt(required=False, allow_none=True)
    proforma_invoice_no = fields.String(required=False, validate=validate.Length(min=1, max=100))
    proforma_invoice_date = FlexibleDate(required=False)
    incoterms = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    delivery_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    delivery_date = FlexibleDate(required=False, allow_none=True)
    payment_terms = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    warranty_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    total_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(SupplierProformaInvoiceItemUpdateSchema),
        required=False,
        allow_none=True,
    )


class SupplierProformaInvoiceQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, validate=validate.Range(min=1))
    supplier_id = fields.Integer(required=False, validate=validate.Range(min=1))
    proforma_invoice_no = fields.String(required=False)


class SupplierProformaInvoiceItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    sr_no = fields.Integer(allow_none=True)
    proforma_invoice_id = fields.Integer(required=True)
    description = fields.String(required=True)
    hsn_sac = fields.String(allow_none=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, required=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    created_at = fields.DateTime(required=True)


class SupplierProformaInvoiceResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=True)
    supplier_name = fields.String(allow_none=True)
    order_confirmation_id = fields.Integer(allow_none=True)
    proforma_invoice_no = fields.String(required=True)
    proforma_invoice_date = fields.Date(required=True)
    incoterms = fields.String(allow_none=True)
    delivery_period = fields.String(allow_none=True)
    delivery_date = fields.Date(allow_none=True)
    payment_terms = fields.String(allow_none=True)
    warranty_period = fields.String(allow_none=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(
        fields.Nested(SupplierProformaInvoiceItemResponseSchema),
        required=True,
    )
    attachments = fields.List(fields.Nested(AttachmentResponseSchema), required=False)


class LatestSupplierProformaInvoiceQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True, validate=validate.Range(min=1))


class LatestSupplierProformaInvoiceItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = fields.Integer(allow_none=True)
    description = fields.String(allow_none=True)
    hsn_sac = fields.String(allow_none=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)


class LatestSupplierProformaInvoiceResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    delivery_period = fields.String(allow_none=True)
    incoterms = fields.String(allow_none=True)
    payment_terms = fields.String(allow_none=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    warranty_period = fields.String(allow_none=True)
    items = fields.List(
        fields.Nested(LatestSupplierProformaInvoiceItemResponseSchema),
        required=True,
    )
