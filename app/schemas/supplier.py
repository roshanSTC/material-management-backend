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
    website_url = fields.String(
        required=False,
        allow_none=True,
        validate=[
            validate.Length(max=2048),
            validate_website_url,
        ],
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
    website_url = fields.String(
        required=False,
        allow_none=True,
        validate=[
            validate.Length(max=2048),
            validate_website_url,
        ],
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