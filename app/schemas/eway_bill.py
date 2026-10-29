from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
import re

from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    pre_load,
    validate,
)

from app.schemas.attachment import AttachmentResponseSchema
from app.utils.date_utils import parse_date_input


def _parse_date_field(val):
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    if not s:
        return None
    parsed = parse_date_input(s)
    if parsed is not None:
        return parsed
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        return date.fromisoformat(s)
    except Exception:
        raise ValidationError(f"Invalid date format: {val}")


class EWayBillItemCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = fields.Integer(required=False, allow_none=True)
    material_name = fields.String(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True)
    hsn_sac = fields.String(required=False, allow_none=True)
    quantity = fields.Decimal(required=False, allow_none=True, as_string=True, places=3)
    unit = fields.String(required=False, allow_none=True)
    unit_price = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)

    @pre_load
    def normalize_item_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # material_name / description
        mat_name = (
            normalized.get("material_name")
            if normalized.get("material_name") is not None
            else normalized.get("description")
        )
        desc = (
            normalized.get("description")
            if normalized.get("description") is not None
            else normalized.get("material_name")
        )
        if mat_name is not None:
            normalized["material_name"] = str(mat_name).strip()
        if desc is not None:
            normalized["description"] = str(desc).strip()

        # hsn_sac / hsn_code
        hsn = (
            normalized.get("hsn_sac")
            if normalized.get("hsn_sac") is not None
            else normalized.get("hsn_code")
            if normalized.get("hsn_code") is not None
            else normalized.get("hsn")
        )
        if hsn is not None:
            normalized["hsn_sac"] = str(hsn).strip()

        # unit
        unit_val = (
            normalized.get("unit")
            if normalized.get("unit") is not None
            else normalized.get("uom")
        )
        if unit_val is not None:
            normalized["unit"] = str(unit_val).strip()

        # total_amount / net_amount / amount / total_price
        tot_amt = (
            normalized.get("total_amount")
            if normalized.get("total_amount") is not None
            else normalized.get("net_amount")
            if normalized.get("net_amount") is not None
            else normalized.get("amount")
            if normalized.get("amount") is not None
            else normalized.get("total_price")
        )
        if tot_amt is not None:
            normalized["total_amount"] = tot_amt

        return normalized


class EWayBillItemUpdateSchema(EWayBillItemCreateSchema):
    id = fields.Integer(required=False, allow_none=True)


class EWayBillItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    sr_no = fields.Integer(dump_only=True)
    material_name = fields.String(dump_only=True)
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

    project_id = fields.Integer(required=True)
    eway_bill_no = fields.String(required=False, allow_none=True)
    eway_bill_date = fields.Date(required=False, allow_none=True)
    valid_from = fields.Date(required=False, allow_none=True)
    valid_until = fields.Date(required=False, allow_none=True)
    document_no = fields.String(required=False, allow_none=True)
    document_date = fields.Date(required=False, allow_none=True)
    value = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    place_of_dispatch = fields.String(required=False, allow_none=True)
    place_of_delivery = fields.String(required=False, allow_none=True)
    transporter = fields.String(required=False, allow_none=True)
    mode = fields.String(required=False, allow_none=True)
    vehicle_trans_doc_no = fields.String(required=False, allow_none=True)
    status = fields.String(required=False, allow_none=True, load_default="completed")
    form_code = fields.String(required=False, allow_none=True)
    attachments_count = fields.Integer(required=False, allow_none=True)
    remark = fields.Raw(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(EWayBillItemCreateSchema),
        required=False,
        load_default=list,
    )

    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # eway_bill_no
        bill_no = (
            normalized.get("eway_bill_no")
            if normalized.get("eway_bill_no") is not None
            else normalized.get("eway_bill_number")
            if normalized.get("eway_bill_number") is not None
            else normalized.get("ewayBillNo")
            if normalized.get("ewayBillNo") is not None
            else normalized.get("ewayBillNumber")
        )
        if bill_no is not None:
            normalized["eway_bill_no"] = str(bill_no).strip()

        # eway_bill_date
        b_date = (
            normalized.get("eway_bill_date")
            if normalized.get("eway_bill_date") is not None
            else normalized.get("ewayBillDate")
        )
        if b_date is not None:
            parsed = _parse_date_field(b_date)
            if parsed is not None:
                normalized["eway_bill_date"] = parsed.isoformat()

        # valid_from
        v_from = (
            normalized.get("valid_from")
            if normalized.get("valid_from") is not None
            else normalized.get("validFrom")
        )
        if v_from is not None:
            parsed = _parse_date_field(v_from)
            if parsed is not None:
                normalized["valid_from"] = parsed.isoformat()

        # valid_until
        v_until = (
            normalized.get("valid_until")
            if normalized.get("valid_until") is not None
            else normalized.get("validUntil")
        )
        if v_until is not None:
            parsed = _parse_date_field(v_until)
            if parsed is not None:
                normalized["valid_until"] = parsed.isoformat()

        # document_no
        doc_no = (
            normalized.get("document_no")
            if normalized.get("document_no") is not None
            else normalized.get("document_number")
            if normalized.get("document_number") is not None
            else normalized.get("documentNo")
            if normalized.get("documentNo") is not None
            else normalized.get("doc_no")
        )
        if doc_no is not None:
            normalized["document_no"] = str(doc_no).strip()

        # document_date
        d_date = (
            normalized.get("document_date")
            if normalized.get("document_date") is not None
            else normalized.get("documentDate")
            if normalized.get("documentDate") is not None
            else normalized.get("doc_date")
        )
        if d_date is not None:
            parsed = _parse_date_field(d_date)
            if parsed is not None:
                normalized["document_date"] = parsed.isoformat()

        # place_of_dispatch
        pod = (
            normalized.get("place_of_dispatch")
            if normalized.get("place_of_dispatch") is not None
            else normalized.get("placeOfDispatch")
            if normalized.get("placeOfDispatch") is not None
            else normalized.get("dispatch_place")
        )
        if pod is not None:
            normalized["place_of_dispatch"] = str(pod).strip()

        # place_of_delivery
        pdel = (
            normalized.get("place_of_delivery")
            if normalized.get("place_of_delivery") is not None
            else normalized.get("placeOfDelivery")
            if normalized.get("placeOfDelivery") is not None
            else normalized.get("delivery_place")
        )
        if pdel is not None:
            normalized["place_of_delivery"] = str(pdel).strip()

        # vehicle_trans_doc_no
        veh_no = (
            normalized.get("vehicle_trans_doc_no")
            if normalized.get("vehicle_trans_doc_no") is not None
            else normalized.get("vehicleTransDocNo")
            if normalized.get("vehicleTransDocNo") is not None
            else normalized.get("vehicle_no")
            if normalized.get("vehicle_no") is not None
            else normalized.get("trans_doc_no")
        )
        if veh_no is not None:
            normalized["vehicle_trans_doc_no"] = str(veh_no).strip()

        # value / total_value / total_amount / amount
        val = (
            normalized.get("value")
            if normalized.get("value") is not None
            else normalized.get("total_value")
            if normalized.get("total_value") is not None
            else normalized.get("total_amount")
            if normalized.get("total_amount") is not None
            else normalized.get("amount")
        )
        if val is not None:
            normalized["value"] = val

        # remark / remarks
        rem = (
            normalized.get("remarks")
            if normalized.get("remarks") is not None
            else normalized.get("remark")
        )
        if rem is not None:
            normalized["remark"] = rem

        return normalized


class EWayBillUpdateSchema(EWayBillCreateSchema):
    project_id = fields.Integer(required=False, allow_none=True)
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
    eway_bill_number = fields.String(dump_only=True)
    eway_bill_date = fields.Date(dump_only=True)
    valid_from = fields.Date(dump_only=True)
    valid_until = fields.Date(dump_only=True)
    document_no = fields.String(dump_only=True)
    document_number = fields.String(dump_only=True)
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
    remark = fields.Raw(dump_only=True)
    items = fields.List(fields.Nested(EWayBillItemResponseSchema), dump_only=True)
    attachments = fields.List(fields.Nested(AttachmentResponseSchema), dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class EWayBillQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    eway_bill_no = fields.String(required=False)

