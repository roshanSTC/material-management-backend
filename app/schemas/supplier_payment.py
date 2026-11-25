from marshmallow import EXCLUDE, Schema, fields, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleInt


class SupplierPaymentCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True)
    supplier_id = FlexibleInt(required=False, allow_none=True)
    supplier_name = fields.String(required=False, allow_none=True)
    currency = fields.String(
        required=False,
        load_default="INR",
        validate=validate.Length(max=10),
    )
    payment_pct = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_contract_value = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    payment_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    payment_date = FlexibleDate(required=True)
    reference_no = fields.String(required=False, allow_none=True)
    pending_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    eur_to_inr_rate = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    payment_amount_inr = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    bank_charges_currency = fields.String(required=False, allow_none=True, validate=validate.Length(max=10))
    bank_charges = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    swift_charges = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_outflow = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    remarks = fields.Raw(required=False, allow_none=True)


class SupplierPaymentUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False)
    supplier_id = FlexibleInt(required=False, allow_none=True)
    supplier_name = fields.String(required=False, allow_none=True)
    currency = fields.String(required=False, validate=validate.Length(max=10))
    payment_pct = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_contract_value = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    payment_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    payment_date = FlexibleDate(required=False)
    reference_no = fields.String(required=False, allow_none=True)
    pending_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    eur_to_inr_rate = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    payment_amount_inr = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    bank_charges_currency = fields.String(required=False, allow_none=True, validate=validate.Length(max=10))
    bank_charges = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    swift_charges = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_outflow = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    remarks = fields.Raw(required=False, allow_none=True)


class SupplierPaymentResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    supplier_id = fields.Integer(dump_only=True)
    currency = fields.String(dump_only=True)
    payment_pct = fields.Decimal(dump_only=True, as_string=True, places=2)
    pending_percentage = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_contract_value = fields.Decimal(dump_only=True, as_string=True, places=2)
    payment_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_paid_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    remaining_amount_before_transaction = fields.Decimal(dump_only=True, as_string=True, places=2)
    payment_date = fields.Date(dump_only=True)
    reference_no = fields.String(dump_only=True)
    pending_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    eur_to_inr_rate = fields.Decimal(dump_only=True, as_string=True, places=2)
    payment_amount_inr = fields.Decimal(dump_only=True, as_string=True, places=2)
    bank_charges_currency = fields.String(dump_only=True)
    bank_charges = fields.Decimal(dump_only=True, as_string=True, places=2)
    swift_charges = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_outflow = fields.Decimal(dump_only=True, as_string=True, places=2)
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


class SupplierPaymentQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    supplier_id = fields.Integer(required=False)
    currency = fields.String(required=False)
