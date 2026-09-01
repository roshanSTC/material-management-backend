from marshmallow import Schema, fields


class QuotationRequestItemSchema(Schema):
    material_name = fields.String(required=True)
    quantity = fields.Decimal(
        required=True,
        as_string=True,
    )


class QuotationRequestCreateSchema(Schema):
    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=True)

    quotation_requested_date = fields.Date(
        required=True
    )

    supplier_contacted = fields.Boolean(
        required=True
    )

    remarks = fields.String(
        required=False,
        allow_none=True,
    )

    items = fields.List(
        fields.Nested(QuotationRequestItemSchema),
        required=True,
    )


class QuotationRequestResponseSchema(Schema):
    id = fields.Integer()
    project_id = fields.Integer()
    supplier_id = fields.Integer()

    quotation_requested_date = fields.Date()
    supplier_contacted = fields.Boolean()

    remarks = fields.String(
        allow_none=True
    )

    created_at = fields.DateTime()
    updated_at = fields.DateTime()

    items = fields.List(
        fields.Nested(
            QuotationRequestItemSchema
        )
    )

    attachments = fields.List(
        fields.Dict()
    )