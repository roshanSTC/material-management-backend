from marshmallow import Schema, fields


class ProjectStepCreateUpdateSchema(Schema):
    data = fields.Dict(
        required=False,
        allow_none=True,
    )


class ProjectStepResponseSchema(Schema):
    id = fields.Integer(
        allow_none=True,
    )

    project_id = fields.Integer(
        required=True,
    )

    step_number = fields.Integer(
        required=True,
    )

    step_name = fields.String(
        required=True,
    )

    description = fields.String(
        required=True,
    )

    status = fields.String(
        required=True,
    )

    progress_percentage = fields.Float(
        required=True,
    )

    completed_at = fields.DateTime(
        allow_none=True,
    )

    data = fields.Dict(
        allow_none=True,
    )