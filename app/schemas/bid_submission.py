from decimal import Decimal
from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class BidSubmissionItemCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = FlexibleInt(required=False, allow_none=True)
    description = fields.String(required=True, validate=validate.Length(min=1, max=500))
    hsn_sac = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    unit_price = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    quantity = fields.Decimal(
        required=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )
    total_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)


class BidSubmissionItemUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=False, allow_none=True)
    sr_no = FlexibleInt(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True, validate=validate.Length(min=1, max=500))
    hsn_sac = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    unit_price = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    quantity = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )
    total_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)


class BidSubmissionCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True, validate=validate.Range(min=1))
    tender_id = FlexibleInt(required=False, allow_none=True)
    customer_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    tender_title = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    tender_no = fields.String(required=True, validate=validate.Length(min=1, max=100))
    tender_issue_date = FlexibleDate(required=False, allow_none=True)
    total_no_corrigendum_issued = FlexibleInt(required=False, allow_none=True)
    bid_submission_date = FlexibleDate(required=False, allow_none=True)
    delivery_terms = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    delivery_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    payment_terms = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    bid_validity = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    warranty_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    gst_pct = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    gst_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_gross_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(BidSubmissionItemCreateSchema),
        required=False,
        load_default=list,
    )


class BidSubmissionUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False, allow_none=True)
    tender_id = FlexibleInt(required=False, allow_none=True)
    customer_name = fields.String(required=False, allow_none=True)
    tender_title = fields.String(required=False, allow_none=True)
    tender_no = fields.String(required=False, allow_none=True)
    tender_issue_date = FlexibleDate(required=False, allow_none=True)
    total_no_corrigendum_issued = FlexibleInt(required=False, allow_none=True)
    bid_submission_date = FlexibleDate(required=False, allow_none=True)
    delivery_terms = fields.String(required=False, allow_none=True)
    delivery_period = fields.String(required=False, allow_none=True)
    payment_terms = fields.String(required=False, allow_none=True)
    bid_validity = fields.String(required=False, allow_none=True)
    warranty_period = fields.String(required=False, allow_none=True)
    gst_pct = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    gst_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_gross_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(BidSubmissionItemUpdateSchema),
        required=False,
        allow_none=True,
    )


class BidSubmissionQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, validate=validate.Range(min=1))


class BidSubmissionItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    sr_no = fields.Integer(allow_none=True)
    bid_submission_id = fields.Integer(required=True)
    description = fields.String(required=True)
    hsn_sac = fields.String(allow_none=True)
    unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    created_at = fields.DateTime(required=True)


class BidSubmissionResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    customer_name = fields.String(allow_none=True)
    tender_id = fields.Integer(allow_none=True)
    tender_title = fields.String(allow_none=True)
    tender_no = fields.String(required=True)
    tender_issue_date = fields.Date(allow_none=True)
    total_no_corrigendum_issued = fields.Integer(allow_none=True)
    bid_submission_date = fields.Date(allow_none=True)
    delivery_terms = fields.String(allow_none=True)
    delivery_period = fields.String(allow_none=True)
    payment_terms = fields.String(allow_none=True)
    bid_validity = fields.String(allow_none=True)
    warranty_period = fields.String(allow_none=True)
    gst_pct = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    gst_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_gross_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(fields.Nested(BidSubmissionItemResponseSchema), required=True)
    attachments = fields.List(fields.Nested(AttachmentResponseSchema), required=False)


class LatestBidSubmissionQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True, validate=validate.Range(min=1))


class LatestBidSubmissionItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = fields.Integer(allow_none=True)
    description = fields.String(required=True)
    hsn_sac = fields.String(allow_none=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)


class LatestBidSubmissionResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    gst_pct = fields.Decimal(as_string=True, places=2, allow_none=True)
    delivery_terms = fields.String(allow_none=True)
    payment_terms = fields.String(allow_none=True)
    warranty_period = fields.String(allow_none=True)
    items = fields.List(
        fields.Nested(LatestBidSubmissionItemResponseSchema),
        required=True,
    )
