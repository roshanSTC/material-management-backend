from datetime import date
from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class SupplierQuotationItemSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = FlexibleInt(required=False, allow_none=True)
    description = fields.String(required=True, validate=validate.Length(min=1, max=500))
    hsn_sac = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
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


class SupplierQuotationCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True, validate=validate.Range(min=1))
    supplier_id = FlexibleInt(required=False, allow_none=True)
    supplier_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    quotation_no = fields.String(required=True, validate=validate.Length(min=1, max=100))
    quotation_value = fields.Raw(required=False, allow_none=True)
    total_net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_gross_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    quotation_date = FlexibleDate(required=False, allow_none=True, load_default=date.today)
    currency_unit = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    currency_symbol = fields.String(required=False, allow_none=True, validate=validate.Length(max=20))
    quotation_validity = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    incoterms = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    payment_terms = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    delivery_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    warranty_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    form_code = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    attachments_count = FlexibleInt(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(SupplierQuotationItemSchema),
        required=True,
        validate=validate.Length(min=1),
    )


class SupplierQuotationUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False, validate=validate.Range(min=1))
    supplier_id = FlexibleInt(required=False, allow_none=True)
    supplier_name = fields.String(required=False, allow_none=True)
    quotation_no = fields.String(required=False, validate=validate.Length(min=1, max=100))
    quotation_value = fields.Raw(required=False, allow_none=True)
    total_net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_gross_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    quotation_date = FlexibleDate(required=False, allow_none=True)
    currency_unit = fields.String(required=False, allow_none=True)
    currency_symbol = fields.String(required=False, allow_none=True)
    quotation_validity = fields.String(required=False, allow_none=True)
    incoterms = fields.String(required=False, allow_none=True)
    payment_terms = fields.String(required=False, allow_none=True)
    delivery_period = fields.String(required=False, allow_none=True)
    warranty_period = fields.String(required=False, allow_none=True)
    form_code = fields.String(required=False, allow_none=True)
    attachments_count = FlexibleInt(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(SupplierQuotationItemSchema),
        required=False,
        validate=validate.Length(min=1),
    )


class SupplierQuotationItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    sr_no = fields.Integer(allow_none=True)
    supplier_quotation_id = fields.Integer(required=True)
    description = fields.String(required=True)
    hsn_sac = fields.String(allow_none=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    created_at = fields.DateTime(required=True)


class SupplierQuotationResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=True)
    supplier_name = fields.String(allow_none=True)
    quotation_no = fields.String(required=True)
    quotation_value = fields.Decimal(as_string=True, places=2, required=True)
    total_net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_gross_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    quotation_date = fields.Date(required=True)
    currency_unit = fields.String(allow_none=True)
    currency_symbol = fields.String(allow_none=True)
    quotation_validity = fields.String(allow_none=True)
    incoterms = fields.String(allow_none=True)
    payment_terms = fields.String(allow_none=True)
    delivery_period = fields.String(allow_none=True)
    warranty_period = fields.String(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(fields.Nested(SupplierQuotationItemResponseSchema), required=True)
    attachments = fields.List(fields.Nested(AttachmentResponseSchema), required=True)


class SupplierQuotationQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, validate=validate.Range(min=1))
    supplier_id = fields.Integer(required=False, validate=validate.Range(min=1))


class LatestSupplierQuotationQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True, validate=validate.Range(min=1))


class LatestSupplierQuotationItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = fields.Integer(allow_none=True)
    description = fields.String(required=True)
    hsn_sac = fields.String(required=False, allow_none=True)
    unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)


class LatestSupplierQuotationResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    quotation_no = fields.String(allow_none=True)
    quotation_date = fields.Raw(allow_none=True)
    quotation_value = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_gross_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    currency_unit = fields.String(allow_none=True)
    currency_symbol = fields.String(allow_none=True)
    quotation_validity = fields.String(allow_none=True)
    incoterms = fields.String(allow_none=True)
    payment_terms = fields.String(allow_none=True)
    delivery_period = fields.String(allow_none=True)
    warranty_period = fields.String(allow_none=True)
    items = fields.List(fields.Nested(LatestSupplierQuotationItemResponseSchema), required=True)
