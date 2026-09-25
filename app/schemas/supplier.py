from marshmallow import Schema, fields, validate


class SupplierPocSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
    )
    email = fields.Email(
        required=False,
        allow_none=True,
    )
    contact_number = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=30),
    )
    designation = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )


class SupplierCreateSchema(Schema):
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
    )
    nickname = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    street = fields.String(
        required=False,
        allow_none=True,
    )
    area = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    city = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    state = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    pincode = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=20),
    )
    country = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    pocs = fields.List(
        fields.Nested(SupplierPocSchema),
        required=False,
        allow_none=True,
    )
    email = fields.Email(
        required=False,
        allow_none=True,
    )
    contact_number = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=30),
    )


class SupplierUpdateSchema(Schema):
    name = fields.String(
        validate=validate.Length(min=1, max=255),
    )
    nickname = fields.String(
        allow_none=True,
        validate=validate.Length(max=100),
    )
    street = fields.String(
        allow_none=True,
    )
    area = fields.String(
        allow_none=True,
        validate=validate.Length(max=255),
    )
    city = fields.String(
        allow_none=True,
        validate=validate.Length(max=100),
    )
    state = fields.String(
        allow_none=True,
        validate=validate.Length(max=100),
    )
    pincode = fields.String(
        allow_none=True,
        validate=validate.Length(max=20),
    )
    country = fields.String(
        allow_none=True,
        validate=validate.Length(max=100),
    )
    pocs = fields.List(
        fields.Nested(SupplierPocSchema),
        allow_none=True,
    )
    email = fields.Email(
        allow_none=True,
    )
    contact_number = fields.String(
        allow_none=True,
        validate=validate.Length(max=30),
    )


class SupplierResponseSchema(Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    nickname = fields.String(allow_none=True)
    street = fields.String(allow_none=True)
    area = fields.String(allow_none=True)
    city = fields.String(allow_none=True)
    state = fields.String(allow_none=True)
    pincode = fields.String(allow_none=True)
    country = fields.String(allow_none=True)
    pocs = fields.List(fields.Nested(SupplierPocSchema))
    email = fields.Email(allow_none=True)
    contact_number = fields.String(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)


class SupplierListResponseSchema(Schema):
    success = fields.Boolean(required=True)
    data = fields.List(
        fields.Nested(SupplierResponseSchema),
        required=True,
    )
    message = fields.String(required=True)