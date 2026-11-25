from marshmallow import EXCLUDE, Schema, fields

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class EWayBillItemCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = FlexibleInt(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True)
    hsn_sac = fields.String(required=False, allow_none=True)
    quantity = fields.Decimal(required=False, allow_none=True, as_string=True, places=3)
    unit = fields.String(required=False, allow_none=True)
    unit_price = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)


class EWayBillItemUpdateSchema(EWayBillItemCreateSchema):
    id = fields.Integer(required=False, allow_none=True)


class EWayBillItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    sr_no = fields.Integer(dump_only=True)
    description = fields.String(dump_only=True)
    hsn_sac = fields.String(dump_only=True)
    quantity = fields.Decimal(dump_only=True, as_string=True, places=3)
    unit = fields.String(dump_only=True)
    unit_price = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    created_at = fields.DateTime(dump_only=True)


class EWayBillCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True)
    eway_bill_no = fields.String(required=False, allow_none=True)
    eway_bill_date = FlexibleDate(required=False, allow_none=True)
    valid_from = FlexibleDate(required=False, allow_none=True)
    valid_until = FlexibleDate(required=False, allow_none=True)
    document_no = fields.String(required=False, allow_none=True)
    document_date = FlexibleDate(required=False, allow_none=True)
    value = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    place_of_dispatch = fields.String(required=False, allow_none=True)
    place_of_delivery = fields.String(required=False, allow_none=True)
    transporter = fields.String(required=False, allow_none=True)
    mode = fields.String(required=False, allow_none=True)
    vehicle_trans_doc_no = fields.String(required=False, allow_none=True)
    status = fields.String(required=False, allow_none=True, load_default="completed")
    form_code = fields.String(required=False, allow_none=True)
    attachments_count = FlexibleInt(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(EWayBillItemCreateSchema),
        required=False,
        load_default=list,
    )


class EWayBillUpdateSchema(EWayBillCreateSchema):
    project_id = FlexibleInt(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(EWayBillItemUpdateSchema),
        required=False,
        allow_none=True,
    )


class EWayBillResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    eway_bill_no = fields.String(dump_only=True)
    eway_bill_date = fields.Date(dump_only=True)
    valid_from = fields.Date(dump_only=True)
    valid_until = fields.Date(dump_only=True)
    document_no = fields.String(dump_only=True)
    document_date = fields.Date(dump_only=True)
    value = fields.Decimal(dump_only=True, as_string=True, places=2)
    place_of_dispatch = fields.String(dump_only=True)
    place_of_delivery = fields.String(dump_only=True)
    transporter = fields.String(dump_only=True)
    mode = fields.String(dump_only=True)
    vehicle_trans_doc_no = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    form_code = fields.String(dump_only=True)
    attachments_count = fields.Integer(dump_only=True)
    remarks = fields.Raw(dump_only=True)
    items = fields.List(fields.Nested(EWayBillItemResponseSchema), dump_only=True)
    attachments = fields.List(fields.Nested(AttachmentResponseSchema), dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class EWayBillQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    eway_bill_no = fields.String(required=False)
