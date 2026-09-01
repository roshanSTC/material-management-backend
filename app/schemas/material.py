from marshmallow import Schema, fields, validate


class MaterialCreateSchema(Schema):
    material_code = fields.String(
        required=True,
        validate=validate.Length(
            min=1,
            max=100,
        ),
    )

    material_name = fields.String(
        required=True,
        validate=validate.Length(
            min=1,
            max=255,
        ),
    )

    hsn_code = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(
            max=20,
        ),
    )

    description = fields.String(
        required=False,
        allow_none=True,
    )


class MaterialUpdateSchema(Schema):
    material_code = fields.String(
        required=False,
        validate=validate.Length(
            min=1,
            max=100,
        ),
    )

    material_name = fields.String(
        required=False,
        validate=validate.Length(
            min=1,
            max=255,
        ),
    )

    hsn_code = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(
            max=20,
        ),
    )

    description = fields.String(
        required=False,
        allow_none=True,
    )


class MaterialResponseSchema(Schema):
    id = fields.Integer(
        required=True,
    )

    material_code = fields.String(
        required=True,
    )

    material_name = fields.String(
        required=True,
    )

    hsn_code = fields.String(
        allow_none=True,
    )

    description = fields.String(
        allow_none=True,
    )

    is_active = fields.Boolean(
        required=True,
    )

    created_at = fields.DateTime(
        required=True,
    )

    updated_at = fields.DateTime(
        required=True,
    )