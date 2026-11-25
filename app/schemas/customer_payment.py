from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class CustomerPaymentCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True)
    payment_against_invoice_no = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    invoice_date = FlexibleDate(required=False, allow_none=True)
    payment_percentage = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    invoice_value = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    payment_received = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    pending_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    balance_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    payment_received_date = FlexibleDate(required=True)
    tds_deducted = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    ld_deducted = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    remarks = fields.Raw(required=False, allow_none=True)


class CustomerPaymentUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False)
    payment_against_invoice_no = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    invoice_date = FlexibleDate(required=False, allow_none=True)
    payment_percentage = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    invoice_value = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    payment_received = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    pending_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    balance_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    payment_received_date = FlexibleDate(required=False)
    tds_deducted = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    ld_deducted = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    remarks = fields.Raw(required=False, allow_none=True)


class CustomerPaymentResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    customer_id = fields.Integer(dump_only=True, allow_none=True)
    payment_against_invoice_no = fields.String(dump_only=True)
    invoice_date = fields.Date(dump_only=True)
    payment_percentage = fields.Decimal(dump_only=True, as_string=True, places=2)
    pending_percentage = fields.Decimal(dump_only=True, as_string=True, places=2)
    invoice_value = fields.Decimal(dump_only=True, as_string=True, places=2)
    payment_received = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_paid_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    remaining_amount_before_transaction = fields.Decimal(dump_only=True, as_string=True, places=2)
    pending_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    balance_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    payment_received_date = fields.Date(dump_only=True)
    tds_deducted = fields.Decimal(dump_only=True, as_string=True, places=2, allow_none=True)
    ld_deducted = fields.Decimal(dump_only=True, as_string=True, places=2, allow_none=True)
    is_payment_completed = fields.Boolean(dump_only=True)
    payment_status = fields.String(dump_only=True)
    payment_status_message = fields.String(dump_only=True)
    remarks = fields.Raw(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_only=True,
    )


class CustomerPaymentQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    payment_against_invoice_no = fields.String(required=False)
