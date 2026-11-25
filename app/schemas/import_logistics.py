from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class ImportLogisticsCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True)
    supplier_id = FlexibleInt(required=False, allow_none=True)
    transportation_mode = fields.String(required=True, validate=validate.Length(min=1, max=100))
    lr_rr_awb_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    lr_rr_awb_date = FlexibleDate(required=True)
    from_location = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    to_location = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    total_transportation_charges = fields.Decimal(
        allow_none=True,
        load_default=None,
        as_string=False,
    )
    remarks = fields.Raw(allow_none=True, load_default=None)


class ImportLogisticsUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False)
    supplier_id = FlexibleInt(required=False, allow_none=True)
    transportation_mode = fields.String(required=False, validate=validate.Length(min=1, max=100))
    lr_rr_awb_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    lr_rr_awb_date = FlexibleDate(required=False)
    from_location = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    to_location = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    total_transportation_charges = fields.Decimal(allow_none=True, as_string=False)
    remarks = fields.Raw(allow_none=True)


class ImportLogisticsQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, allow_none=True)


class ImportLogisticsResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(allow_none=True)
    transportation_mode = fields.String(required=True)
    lr_rr_awb_no = fields.String(allow_none=True)
    lr_rr_awb_date = fields.Date(required=True)
    from_location = fields.String(allow_none=True)
    to_location = fields.String(allow_none=True)
    total_transportation_charges = fields.Decimal(as_string=True, places=2, allow_none=True)
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_default=[],
    )
