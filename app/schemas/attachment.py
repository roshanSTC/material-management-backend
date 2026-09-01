from marshmallow import Schema, fields


class AttachmentUploadSchema(Schema):
    file = fields.Raw(
        required=True,
        metadata={
            "type": "string",
            "format": "binary",
        },
    )


class AttachmentResponseSchema(Schema):
    id = fields.Integer(required=True)

    entity_type = fields.String(
        required=True,
    )

    entity_id = fields.Integer(
        required=True,
    )

    file_name = fields.String(
        required=True,
    )

    storage_key = fields.String(
        required=True,
    )

    content_type = fields.String(
        required=True,
    )

    file_size = fields.Integer(
        required=True,
    )

    uploaded_by = fields.Integer(
        required=True,
    )

    created_at = fields.DateTime(
        required=True,
    )

    updated_at = fields.DateTime(
        required=True,
    )