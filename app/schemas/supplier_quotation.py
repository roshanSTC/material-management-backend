from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from app.schemas.attachment import AttachmentResponseSchema


def _not_blank(value: str) -> None:
    if not value.strip():
        raise ValidationError("Field must not be blank.")


class SupplierQuotationItemSchema(Schema):
    material_name = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=255),
            _not_blank,
        ),
    )
    quantity = fields.Decimal(
        required=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=0.001),
    )


class SupplierQuotationCreateSchema(Schema):
    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    supplier_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    quotation_number = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    quotation_date = fields.Date(required=True)
    quotation_value = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0.01),
    )
    validity = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    incoterms = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )
    payment_terms = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    delivery_period = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    remark = fields.String(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(SupplierQuotationItemSchema),
        required=True,
        validate=validate.Length(min=1),
    )


class SupplierQuotationUpdateSchema(Schema):
    project_id = fields.Integer(validate=validate.Range(min=1))
    supplier_id = fields.Integer(validate=validate.Range(min=1))
    quotation_number = fields.String(
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    quotation_date = fields.Date()
    quotation_value = fields.Decimal(
        as_string=True,
        places=2,
        validate=validate.Range(min=0.01),
    )
    validity = fields.String(allow_none=True, validate=validate.Length(max=100))
    incoterms = fields.String(allow_none=True, validate=validate.Length(max=50))
    payment_terms = fields.String(allow_none=True, validate=validate.Length(max=255))
    delivery_period = fields.String(
        allow_none=True,
        validate=validate.Length(max=100),
    )
    remark = fields.String(allow_none=True)
    items = fields.List(
        fields.Nested(SupplierQuotationItemSchema),
        validate=validate.Length(min=1),
    )

    @validates_schema
    def validate_non_empty_payload(self, data, **kwargs):
        if not data:
            raise ValidationError(
                "At least one supplier quotation field is required."
            )


class SupplierQuotationItemResponseSchema(Schema):
    id = fields.Integer(required=True)
    material_name = fields.String(required=True)
    quantity = fields.Decimal(required=True, as_string=True, places=3)


class SupplierQuotationResponseSchema(Schema):
    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=True)
    quotation_number = fields.String(required=True)
    quotation_date = fields.Date(required=True)
    quotation_value = fields.Decimal(required=True, as_string=True, places=2)
    validity = fields.String(allow_none=True)
    incoterms = fields.String(allow_none=True)
    payment_terms = fields.String(allow_none=True)
    delivery_period = fields.String(allow_none=True)
    remark = fields.String(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(fields.Nested(SupplierQuotationItemResponseSchema), required=True)
    attachments = fields.List(fields.Nested(AttachmentResponseSchema), required=True)
