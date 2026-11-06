from marshmallow import EXCLUDE, Schema, fields, validate, post_dump


class FormDefinitionResponseSchema(Schema):
    id = fields.Integer(required=True)
    form_code = fields.String(required=True)
    name = fields.String(required=True)
    category = fields.String(required=True)
    phase_id = fields.String(required=True)
    icon = fields.String(required=False)
    description = fields.String(required=False, allow_none=True)
    has_table = fields.Boolean(required=True)


class ProjectStepAttachSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    form_code = fields.String(required=True)
    step_name = fields.String(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True)
    status = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["pending", "in_progress", "completed", "skipped"]),
    )
    progress_percentage = fields.Integer(required=False, allow_none=True)
    remark = fields.String(required=False, allow_none=True)
    user_name = fields.String(required=False, allow_none=True)
    data = fields.Dict(required=False, allow_none=True)


class ProjectStepUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    data = fields.Dict(required=False, allow_none=True)
    status = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["pending", "in_progress", "completed", "skipped"]),
    )
    progress_percentage = fields.Integer(required=False, allow_none=True)
    step_name = fields.String(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True)
    remark = fields.String(required=False, allow_none=True)
    user_name = fields.String(required=False, allow_none=True)


class ProjectStepRemarkCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    remark = fields.String(required=True)
    user_name = fields.String(required=False, allow_none=True)


class ProjectStepAttachmentResponseSchema(Schema):
    id = fields.Integer(required=True)
    upload_key = fields.String(required=True)
    file_name = fields.String(required=True)
    file_size = fields.String(required=False)
    file_size_bytes = fields.Integer(required=False, allow_none=True)
    file_path = fields.String(required=True)
    download_url = fields.String(required=False, allow_none=True)
    created_at = fields.DateTime(required=False, allow_none=True)


class ProjectStepResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(allow_none=True)
    project_id = fields.Integer(required=True)
    step_order = fields.Integer(required=True)
    step_number = fields.Integer(required=True)
    form_code = fields.String(required=False, allow_none=True)
    step_name = fields.String(required=True)
    description = fields.String(required=False, allow_none=True)
    phase_id = fields.String(required=False, allow_none=True)
    category = fields.String(required=False, allow_none=True)
    icon = fields.String(required=False, allow_none=True)
    status = fields.String(required=True)
    progress_percentage = fields.Integer(required=True)
    completed_at = fields.DateTime(allow_none=True)
    data = fields.Dict(allow_none=True)
    remarks = fields.List(fields.Raw(), dump_only=True, allow_none=True)
    attachments = fields.List(fields.Raw(), dump_only=True, allow_none=True)

    @post_dump(pass_original=True)
    def include_dynamic_fields(self, data, original, **kwargs):
        if isinstance(original, dict):
            if "data" not in original:
                data.pop("data", None)
            for k, v in original.items():
                if k not in data:
                    data[k] = v
        return data