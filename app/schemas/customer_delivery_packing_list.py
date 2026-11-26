from decimal import Decimal
from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt, FlexibleString


class CustomerDeliveryPackingListItemCreateSchema(Schema):
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
    unit_weight = fields.Decimal(required=False, allow_none=True, as_string=True, places=3)
    total_weight = fields.Decimal(required=False, allow_none=True, as_string=True, places=3)


class CustomerDeliveryPackingListItemUpdateSchema(Schema):
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
    unit_weight = fields.Decimal(required=False, allow_none=True, as_string=True, places=3)
    total_weight = fields.Decimal(required=False, allow_none=True, as_string=True, places=3)


class CustomerDeliveryPackingListItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    sr_no = fields.Integer(dump_only=True)
    packing_list_id = fields.Integer(dump_only=True)
    description = fields.String(dump_only=True)
    hsn_sac = fields.String(dump_only=True)
    quantity = fields.Decimal(dump_only=True, as_string=True, places=3, allow_none=True)
    unit_weight = fields.Decimal(dump_only=True, as_string=True, places=3, allow_none=True)
    total_weight = fields.Decimal(dump_only=True, as_string=True, places=3, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class CustomerDeliveryPackingListCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True)
    packing_list_no = fields.String(required=True, validate=validate.Length(min=1, max=100))
    packing_list_date = FlexibleDate(required=True)
    total_no_packages = FlexibleInt(required=False, allow_none=True)
    packing_condition = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    net_weight = FlexibleString(required=False, allow_none=True, validate=validate.Length(max=255))
    gross_weight = FlexibleString(required=False, allow_none=True, validate=validate.Length(max=255))
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(CustomerDeliveryPackingListItemCreateSchema),
        required=False,
        load_default=list,
    )
    attachments_count = FlexibleInt(required=False, allow_none=True)
    form_code = fields.String(required=False, allow_none=True)


class CustomerDeliveryPackingListUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False)
    packing_list_no = fields.String(required=False, validate=validate.Length(min=1, max=100))
    packing_list_date = FlexibleDate(required=False)
    total_no_packages = FlexibleInt(required=False, allow_none=True)
    packing_condition = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    net_weight = FlexibleString(required=False, allow_none=True, validate=validate.Length(max=255))
    gross_weight = FlexibleString(required=False, allow_none=True, validate=validate.Length(max=255))
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(CustomerDeliveryPackingListItemUpdateSchema),
        required=False,
        allow_none=True,
    )
    attachments_count = FlexibleInt(required=False, allow_none=True)
    form_code = fields.String(required=False, allow_none=True)


class CustomerDeliveryPackingListResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    packing_list_no = fields.String(dump_only=True)
    packing_list_date = fields.Date(dump_only=True)
    total_no_packages = fields.Integer(dump_only=True)
    packing_condition = fields.String(dump_only=True)
    net_weight = fields.String(dump_only=True)
    gross_weight = fields.String(dump_only=True)
    remarks = fields.Raw(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    items = fields.List(
        fields.Nested(CustomerDeliveryPackingListItemResponseSchema),
        dump_only=True,
    )
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_only=True,
    )


class CustomerDeliveryPackingListQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    packing_list_no = fields.String(required=False)
