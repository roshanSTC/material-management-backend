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
    id = fields.Integer(dump_only=True)

    customer_query_id = fields.Integer(
        dump_only=True,
    )

    file_name = fields.String(
        dump_only=True,
    )


    storage_key = fields.String(
        dump_only=True,
    )

    content_type = fields.String(
        dump_only=True,
    )

    file_size = fields.Integer(
        dump_only=True,
    )

    uploaded_by = fields.Integer(
        dump_only=True,
    )

    created_at = fields.DateTime(
        dump_only=True,
    )

    updated_at = fields.DateTime(
        dump_only=True,
    )