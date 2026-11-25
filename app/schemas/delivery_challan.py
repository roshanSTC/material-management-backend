from decimal import Decimal
from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class DeliveryChallanItemCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = FlexibleInt(required=False, allow_none=True)
    description = fields.String(required=True, validate=validate.Length(min=1, max=500))
    hsn_sac = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    quantity = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.000")),
    )
    unit_price = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )
    total_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )


class DeliveryChallanItemUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=False, allow_none=True)
    sr_no = FlexibleInt(required=False, allow_none=True)
    description = fields.String(required=False, validate=validate.Length(min=1, max=500))
    hsn_sac = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    quantity = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.000")),
    )
    unit_price = fields.Decimal(
        required=False,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )
    total_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )


class DeliveryChallanItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    sr_no = fields.Integer(dump_only=True)
    delivery_challan_id = fields.Integer(dump_only=True)
    description = fields.String(dump_only=True)
    hsn_sac = fields.String(dump_only=True)
    quantity = fields.Decimal(dump_only=True, as_string=True, places=3, allow_none=True)
    unit_price = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class DeliveryChallanCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True)
    delivery_challan_no = fields.String(required=True, validate=validate.Length(min=1, max=100))
    delivery_challan_date = FlexibleDate(required=True)
    gst_pct = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    gst_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    round_off = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_gross_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(DeliveryChallanItemCreateSchema),
        required=False,
        load_default=list,
    )
    attachments_count = FlexibleInt(required=False, allow_none=True)
    form_code = fields.String(required=False, allow_none=True)


class DeliveryChallanUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False)
    delivery_challan_no = fields.String(required=False, validate=validate.Length(min=1, max=100))
    delivery_challan_date = FlexibleDate(required=False)
    gst_pct = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    gst_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    round_off = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_gross_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(DeliveryChallanItemUpdateSchema),
        required=False,
        allow_none=True,
    )
    attachments_count = FlexibleInt(required=False, allow_none=True)
    form_code = fields.String(required=False, allow_none=True)


class DeliveryChallanResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    delivery_challan_no = fields.String(dump_only=True)
    delivery_challan_date = fields.Date(dump_only=True)
    gst_pct = fields.Decimal(dump_only=True, as_string=True, places=2)
    gst_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    round_off = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_gross_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    remarks = fields.Raw(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    items = fields.List(
        fields.Nested(DeliveryChallanItemResponseSchema),
        dump_only=True,
    )
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_only=True,
    )


class DeliveryChallanQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    delivery_challan_no = fields.String(required=False)
