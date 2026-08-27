
from marshmallow import Schema, fields, validate


class ProjectCreateSchema(Schema):
    project_title = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
    )

    customer_id = fields.Integer(
        required=True,
        strict=True,
    )

    supplier_id = fields.Integer(
        required=True,
        strict=True,
    )


class ProjectUpdateSchema(Schema):
    project_title = fields.String(
        validate=validate.Length(min=1, max=255),
    )

    customer_id = fields.Integer(
        strict=True,
    )

    supplier_id = fields.Integer(
        strict=True,
    )


class ProjectResponseSchema(Schema):
    id = fields.Integer(required=True)
    project_title = fields.String(required=True)
    customer_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
