from marshmallow import EXCLUDE, INCLUDE, Schema, fields, validate


class StepRemarkCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    remark = fields.String(
        required=True,
        validate=validate.Length(min=1),
    )


class StepRemarkItemSchema(Schema):
    class Meta:
        unknown = INCLUDE

    id = fields.Raw(allow_none=True, dump_default=None)
    project_id = fields.Raw(allow_none=True, dump_default=None)
    step_number = fields.Raw(allow_none=True, dump_default=None)
    remark = fields.Raw(allow_none=True)
    user = fields.Raw(allow_none=True, dump_default=None)
    user_id = fields.Raw(allow_none=True, dump_default=None)
    created_at = fields.Raw(allow_none=True, dump_default=None)
    updated_at = fields.Raw(allow_none=True, dump_default=None)


class StepRemarksByStepSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    step_number = fields.Integer(required=True)
    step_name = fields.String(required=True)
    remarks = fields.List(fields.Raw(), required=True)


class ProjectRemarksListResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    success = fields.Boolean(required=True)
    message = fields.String(required=True)
    data = fields.List(fields.Nested(StepRemarksByStepSchema), required=True)


class StepRemarkSingleResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    success = fields.Boolean(required=True)
    message = fields.String(required=True)
    data = fields.Nested(StepRemarkItemSchema, required=True)

