from marshmallow import Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema


class CustomerQueryItemSchema(Schema):
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
    
    


class CustomerQueryCreateSchema(Schema):
    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )

    customer_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )

    qo_date = fields.Date(
        required=True,
    )

    remark = fields.String(
        required=False,
        allow_none=True,
    )

    items = fields.List(
        fields.Nested(CustomerQueryItemSchema),
        required=True,
        validate=validate.Length(min=1),
    )


class CustomerQueryItemResponseSchema(Schema):
    id = fields.Integer(required=True)
    material_name = fields.String(required=True)
    quantity = fields.Decimal(
        required=True,
        as_string=True,
        places=3,
    )


class CustomerQueryResponseSchema(Schema):
    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    customer_id = fields.Integer(required=True)
    qo_date = fields.Date(required=True)
    remark = fields.String(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)

    items = fields.List(
        fields.Nested(CustomerQueryItemResponseSchema),
        required=True,
    )
    
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        required=True,
    )
    
class CustomerQueryUpdateSchema(Schema):
    project_id = fields.Integer(required=False)
    customer_id = fields.Integer(required=False)
    qo_date = fields.Date(required=False)
    remark = fields.String(required=False, allow_none=True)

    items = fields.List(
        fields.Nested(CustomerQueryItemSchema),
        required=False,
    )