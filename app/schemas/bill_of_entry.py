from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class BillOfEntryCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True)
    logistic_mode = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    shipment_date = FlexibleDate(required=False, allow_none=True)
    awb_bl_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    flight_vessel_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    flight_vessel_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    port_loading = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    port_discharge = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    bill_of_entry_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    boe_filing_date = FlexibleDate(required=False, allow_none=True)
    total_assessable_value = fields.Decimal(as_string=False, allow_none=True, load_default=None)
    basic_custom_duty_bcd = fields.Decimal(as_string=False, allow_none=True, load_default=None)
    sws = fields.Decimal(as_string=False, allow_none=True, load_default=None)
    igst = fields.Decimal(as_string=False, allow_none=True, load_default=None)
    total_duty = fields.Decimal(as_string=False, allow_none=True, load_default=None)
    duty_paid_date = FlexibleDate(required=False, allow_none=True)
    challan_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    payment_ref_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    customs_location = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    cfs_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    remarks = fields.Raw(allow_none=True, load_default=None)
    items = fields.List(fields.Raw(), required=False, allow_none=True, load_default=[])
    attachments_count = FlexibleInt(required=False, allow_none=True)
    form_code = fields.String(required=False, allow_none=True)


class BillOfEntryUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False)
    logistic_mode = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    shipment_date = FlexibleDate(required=False, allow_none=True)
    awb_bl_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    flight_vessel_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    flight_vessel_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    port_loading = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    port_discharge = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    bill_of_entry_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    boe_filing_date = FlexibleDate(required=False, allow_none=True)
    total_assessable_value = fields.Decimal(as_string=False, allow_none=True)
    basic_custom_duty_bcd = fields.Decimal(as_string=False, allow_none=True)
    sws = fields.Decimal(as_string=False, allow_none=True)
    igst = fields.Decimal(as_string=False, allow_none=True)
    total_duty = fields.Decimal(as_string=False, allow_none=True)
    duty_paid_date = FlexibleDate(required=False, allow_none=True)
    challan_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    payment_ref_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    customs_location = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    cfs_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    remarks = fields.Raw(allow_none=True)
    items = fields.List(fields.Raw(), required=False, allow_none=True)
    attachments_count = FlexibleInt(required=False, allow_none=True)
    form_code = fields.String(required=False, allow_none=True)


class BillOfEntryQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, allow_none=True)


class BillOfEntryResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    logistic_mode = fields.String(allow_none=True)
    shipment_date = fields.Date(allow_none=True)
    awb_bl_no = fields.String(allow_none=True)
    flight_vessel_name = fields.String(allow_none=True)
    flight_vessel_no = fields.String(allow_none=True)
    port_loading = fields.String(allow_none=True)
    port_discharge = fields.String(allow_none=True)
    bill_of_entry_no = fields.String(allow_none=True)
    boe_filing_date = fields.Date(allow_none=True)
    total_assessable_value = fields.Raw(allow_none=True)
    basic_custom_duty_bcd = fields.Raw(allow_none=True)
    sws = fields.Raw(allow_none=True)
    igst = fields.Raw(allow_none=True)
    total_duty = fields.Raw(allow_none=True)
    duty_paid_date = fields.Date(allow_none=True)
    challan_no = fields.String(allow_none=True)
    payment_ref_no = fields.String(allow_none=True)
    customs_location = fields.String(allow_none=True)
    cfs_name = fields.String(allow_none=True)
    items = fields.List(fields.Raw(), dump_default=[])
    form_code = fields.String(dump_default="FORM_27_SHIPPING_CLEARANCE")
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_default=[],
    )


class LatestBillOfEntryQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )


class LatestBillOfEntryResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    bill_of_entry_no = fields.String(allow_none=True)
    boe_filing_date = fields.Date(allow_none=True)
    basic_custom_duty_bcd = fields.Float(allow_none=True)
    sws = fields.Float(allow_none=True)
    igst = fields.Float(allow_none=True)
    total_duty = fields.Float(allow_none=True)
