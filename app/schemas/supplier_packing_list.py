from decimal import Decimal
from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class SupplierPackingListItemCreateSchema(Schema):
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
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )
    unit_weight = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.000")),
    )
    total_weight = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.000")),
    )


class SupplierPackingListItemUpdateSchema(Schema):
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
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )
    unit_weight = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.000")),
    )
    total_weight = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.000")),
    )


class SupplierPackingListItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    sr_no = fields.Integer(allow_none=True)
    packing_list_id = fields.Integer(required=True)
    description = fields.String(required=True)
    hsn_sac = fields.String(allow_none=True)
    quantity = fields.Decimal(as_string=True, places=3, allow_none=True)
    unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    unit_weight = fields.Decimal(as_string=True, places=3, allow_none=True)
    total_weight = fields.Decimal(as_string=True, places=3, allow_none=True)
    created_at = fields.DateTime(required=True)


class SupplierPackingListCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True, validate=validate.Range(min=1))
    supplier_id = FlexibleInt(required=False, allow_none=True)
    packing_list_no = fields.String(required=True, validate=validate.Length(min=1, max=100))
    packing_list_date = FlexibleDate(required=True)
    packing_condition = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    net_weight = fields.Decimal(required=False, allow_none=True, as_string=True, places=3)
    gross_weight = fields.Decimal(required=False, allow_none=True, as_string=True, places=3)
    total_no_packages = FlexibleInt(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(SupplierPackingListItemCreateSchema),
        required=False,
        load_default=list,
    )


class SupplierPackingListUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False, validate=validate.Range(min=1))
    supplier_id = FlexibleInt(required=False, allow_none=True)
    packing_list_no = fields.String(required=False, validate=validate.Length(min=1, max=100))
    packing_list_date = FlexibleDate(required=False)
    packing_condition = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    net_weight = fields.Decimal(required=False, allow_none=True, as_string=True, places=3)
    gross_weight = fields.Decimal(required=False, allow_none=True, as_string=True, places=3)
    total_no_packages = FlexibleInt(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(SupplierPackingListItemUpdateSchema),
        required=False,
        allow_none=True,
    )


class SupplierPackingListQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, validate=validate.Range(min=1))
    supplier_id = fields.Integer(required=False, validate=validate.Range(min=1))
    packing_list_no = fields.String(required=False)


class SupplierPackingListResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=False, allow_none=True)
    packing_list_no = fields.String(required=True)
    packing_list_date = fields.Date(required=True)
    packing_condition = fields.String(allow_none=True)
    net_weight = fields.Decimal(as_string=True, places=3, allow_none=True)
    gross_weight = fields.Decimal(as_string=True, places=3, allow_none=True)
    total_no_packages = fields.Integer(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(
        fields.Nested(SupplierPackingListItemResponseSchema),
        required=True,
    )
    attachments = fields.List(fields.Nested(AttachmentResponseSchema), required=False)


class LatestSupplierPackingListQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True, validate=validate.Range(min=1))


class LatestSupplierPackingListResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    gross_weight = fields.Decimal(as_string=True, places=3, allow_none=True)
    net_weight = fields.Decimal(as_string=True, places=3, allow_none=True)
    total_no_packages = fields.Integer(allow_none=True)
