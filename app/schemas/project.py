from marshmallow import EXCLUDE, Schema, fields, validate


class ProjectCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

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
    class Meta:
        unknown = EXCLUDE

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
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_title = fields.String(required=True)
    customer_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)


class ProjectSummaryItemSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_title = fields.String(required=True)
    customer_id = fields.Integer(required=True)
    customer_name = fields.String(allow_none=True)
    supplier_id = fields.Integer(required=True)
    supplier_name = fields.String(allow_none=True)
    current_step_number = fields.Integer(required=True)
    total_steps = fields.Integer(required=True)
    current_step_name = fields.String(required=True)
    progress_percentage = fields.Integer(required=True)
    status = fields.String(required=True)
    health_status = fields.String(required=True)
    next_action = fields.String(allow_none=True)
    target_delivery_date = fields.String(allow_none=True)
    total_value = fields.Raw(allow_none=True)
    currency = fields.String(required=True)
    customer_payment_status = fields.String(required=True)
    supplier_payment_status = fields.String(required=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)


class ProjectListResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    success = fields.Boolean(required=True)
    message = fields.String(required=True)
    data = fields.List(fields.Nested(ProjectSummaryItemSchema), required=True)
