from marshmallow import Schema, fields, validate


class QuotationRequestItemSchema(Schema):
    material_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
    )

    quantity = fields.Decimal(
        required=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=0.001),
    )


class QuotationRequestCreateSchema(Schema):
    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )

    supplier_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )

    request_date = fields.Date(
        required=True,
    )

    remarks = fields.String(
        required=False,
        allow_none=True,
    )

    items = fields.List(
        fields.Nested(QuotationRequestItemSchema),
        required=True,
        validate=validate.Length(min=1),
    )


class QuotationRequestItemResponseSchema(Schema):
    id = fields.Integer(required=True)

    material_name = fields.String(
        required=True,
    )

    quantity = fields.Decimal(
        required=True,
        as_string=True,
        places=3,
    )


class QuotationRequestResponseSchema(Schema):
    id = fields.Integer(required=True)

    project_id = fields.Integer(
        required=True,
    )

    supplier_id = fields.Integer(
        required=True,
    )

    request_date = fields.Date(
        required=True,
    )

    remarks = fields.String(
        allow_none=True,
    )

    created_at = fields.DateTime(
        required=True,
    )

    updated_at = fields.DateTime(
        required=True,
    )

    items = fields.List(
        fields.Nested(
            QuotationRequestItemResponseSchema
        ),
        required=True,
    )