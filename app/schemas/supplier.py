from marshmallow import Schema, fields, validate


class SupplierCreateSchema(Schema):
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
    )
    email = fields.Email(required=True)
    contact_number = fields.String(
        required=True,
        validate=validate.Length(min=1, max=30),
    )
    address = fields.String(
        required=True,
        validate=validate.Length(min=1),
    )
    website_url = fields.Url(
        required=False,
        allow_none=True,
        validate=validate.Length(max=2048),
    )


class SupplierUpdateSchema(Schema):
    name = fields.String(
        validate=validate.Length(min=1, max=255),
    )
    email = fields.Email()
    contact_number = fields.String(
        validate=validate.Length(min=1, max=30),
    )
    address = fields.String(
        validate=validate.Length(min=1),
    )
    website_url = fields.Url(
        allow_none=True,
        validate=validate.Length(max=2048),
    )


class SupplierResponseSchema(Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    email = fields.Email(required=True)
    contact_number = fields.String(required=True)
    address = fields.String(required=True)
    website_url = fields.String(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)