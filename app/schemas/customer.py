import re

from marshmallow import Schema, ValidationError, fields, validate


def validate_website_url(value):
    if value is None:
        return

    value = value.strip()

    # Accept:
    # www.amazon.com
    # amazon.com
    # https://www.amazon.com
    # http://www.amazon.com
    pattern = re.compile(
        r"^(?:(?:https?|ftp)://)?"
        r"(?:www\.)?"
        r"[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+"
        r"(?::\d+)?"
        r"(?:/[^ ]*)?$"
    )

    if not pattern.match(value):
        raise ValidationError("Not a valid website URL.")


class CustomerPocSchema(Schema):
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


class CustomerCreateSchema(Schema):
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
        fields.Nested(CustomerPocSchema),
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
    address = fields.String(
        required=False,
        allow_none=True,
    )
    website_url = fields.String(
        required=False,
        allow_none=True,
        validate=[
            validate.Length(max=2048),
            validate_website_url,
        ],
    )


class CustomerUpdateSchema(Schema):
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
        fields.Nested(CustomerPocSchema),
        allow_none=True,
    )
    email = fields.Email(
        allow_none=True,
    )
    contact_number = fields.String(
        allow_none=True,
        validate=validate.Length(max=30),
    )
    address = fields.String(
        allow_none=True,
    )
    website_url = fields.String(
        allow_none=True,
        validate=[
            validate.Length(max=2048),
            validate_website_url,
        ],
    )


class CustomerResponseSchema(Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    nickname = fields.String(allow_none=True)
    street = fields.String(allow_none=True)
    area = fields.String(allow_none=True)
    city = fields.String(allow_none=True)
    state = fields.String(allow_none=True)
    pincode = fields.String(allow_none=True)
    country = fields.String(allow_none=True)
    pocs = fields.List(fields.Nested(CustomerPocSchema))
    email = fields.Email(allow_none=True)
    contact_number = fields.String(allow_none=True)
    address = fields.String(allow_none=True)
    website_url = fields.String(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)


class CustomerListResponseSchema(Schema):
    success = fields.Boolean(required=True)
    data = fields.List(
        fields.Nested(CustomerResponseSchema),
        required=True,
    )
    message = fields.String(required=True)