from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class TransportDetailCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True)
    transportation_mode = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
    )
    lr_rr_awb_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    lr_rr_awb_date = FlexibleDate(required=True)
    from_location = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
    )
    to_location = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
    )
    total_transportation_charges = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    remarks = fields.Raw(allow_none=True, load_default=None)


class TransportDetailUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False)
    transportation_mode = fields.String(
        required=False,
        validate=validate.Length(min=1, max=100),
    )
    lr_rr_awb_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    lr_rr_awb_date = FlexibleDate(required=False)
    from_location = fields.String(
        required=False,
        validate=validate.Length(min=1, max=255),
    )
    to_location = fields.String(
        required=False,
        validate=validate.Length(min=1, max=255),
    )
    total_transportation_charges = fields.Decimal(as_string=False, allow_none=True)
    remarks = fields.Raw(allow_none=True)


class TransportDetailResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    transportation_mode = fields.String(dump_only=True)
    lr_rr_awb_no = fields.String(dump_only=True, allow_none=True)
    lr_rr_awb_date = fields.Date(dump_only=True)
    from_location = fields.String(dump_only=True)
    to_location = fields.String(dump_only=True)
    total_transportation_charges = fields.Decimal(dump_only=True, as_string=False, allow_none=True)
    remarks = fields.Raw(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_only=True,
        dump_default=[],
    )


class TransportDetailQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    transportation_mode = fields.String(required=False)
    lr_rr_awb_no = fields.String(required=False)
