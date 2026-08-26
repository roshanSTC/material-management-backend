from marshmallow import Schema, fields, validate


class RegisterRequestSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(
        required=True,
        load_only=True,
        validate=validate.Length(min=8, max=128),
    )
    first_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
    )
    last_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
    )


class LoginRequestSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(
        required=True,
        load_only=True,
    )


class UserResponseSchema(Schema):
    id = fields.Integer(required=True)
    email = fields.Email(required=True)
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    is_active = fields.Boolean(required=True)


class LoginDataSchema(Schema):
    id = fields.Integer(required=True)
    email = fields.Email(required=True)
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    is_active = fields.Boolean(required=True)
    access_token = fields.String(required=True)


class LoginResponseSchema(Schema):
    success = fields.Boolean(required=True)
    data = fields.Nested(LoginDataSchema, required=True)
    message = fields.String(required=True)


class RegisterResponseSchema(Schema):
    success = fields.Boolean(required=True)
    data = fields.Nested(UserResponseSchema, required=True)
    message = fields.String(required=True)


class ErrorResponseSchema(Schema):
    success = fields.Boolean(required=True)
    error = fields.Dict(required=True)