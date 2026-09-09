from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal

from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    pre_load,
    validate,
)

from app.schemas.attachment import AttachmentResponseSchema


def _not_blank(value: str) -> None:
    if not value or not str(value).strip():
        raise ValidationError("Field must not be blank.")


def _parse_date(val):
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    if not s:
        return None
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        return date.fromisoformat(s)
    except Exception:
        raise ValidationError(f"Invalid date format: {val}")


class DeliveryChallanItemCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    material_name = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=255),
            _not_blank,
        ),
    )
    hsn_code = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )
    quantity = fields.Decimal(
        required=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )
    unit_price = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )
    net_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )

    @pre_load
    def normalize_item_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # Handle material_name / material_description fallback
        mat_name = (
            normalized.get("material_name")
            if normalized.get("material_name") is not None
            else normalized.get("materialName")
        )
        if mat_name is None:
            mat_name = (
                normalized.get("material_description")
                if normalized.get("material_description") is not None
                else normalized.get("description")
            )
        if mat_name is not None:
            normalized["material_name"] = str(mat_name).strip()

        # Handle hsn_code / hsn_sac fallback
        hsn = (
            normalized.get("hsn_code")
            if normalized.get("hsn_code") is not None
            else normalized.get("hsnCode")
        )
        if hsn is None:
            hsn = (
                normalized.get("hsn_sac")
                if normalized.get("hsn_sac") is not None
                else normalized.get("hsn")
            )
        if hsn is not None:
            normalized["hsn_code"] = str(hsn).strip()

        # Handle unit_price / rate_per_unit fallback
        unit_price = (
            normalized.get("unit_price")
            if normalized.get("unit_price") is not None
            else normalized.get("unitPrice")
        )
        if unit_price is None:
            unit_price = (
                normalized.get("rate_per_unit")
                if normalized.get("rate_per_unit") is not None
                else normalized.get("rate")
            )
        if unit_price is not None:
            normalized["unit_price"] = unit_price

        # Handle net_amount / amount fallback
        net_amt = (
            normalized.get("net_amount")
            if normalized.get("net_amount") is not None
            else normalized.get("netAmount")
        )
        if net_amt is None:
            net_amt = (
                normalized.get("amount")
                if normalized.get("amount") is not None
                else normalized.get("total_price")
            )
        if net_amt is not None:
            normalized["net_amount"] = net_amt

        return normalized


class DeliveryChallanItemUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=False, allow_none=True)
    material_name = fields.String(
        required=False,
        validate=validate.And(
            validate.Length(min=1, max=255),
            _not_blank,
        ),
    )
    hsn_code = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )
    quantity = fields.Decimal(
        required=False,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )
    unit_price = fields.Decimal(
        required=False,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )
    net_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )


class DeliveryChallanItemResponseSchema(Schema):
    id = fields.Integer(dump_only=True)
    delivery_challan_id = fields.Integer(dump_only=True)
    material_name = fields.String(dump_only=True)
    hsn_code = fields.String(dump_only=True)
    quantity = fields.Decimal(dump_only=True, as_string=True, places=3)
    unit_price = fields.Decimal(dump_only=True, as_string=True, places=2)
    net_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class DeliveryChallanCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True)
    delivery_challan_no = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    delivery_challan_date = fields.Date(required=True)
    remark = fields.String(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(DeliveryChallanItemCreateSchema),
        required=False,
        load_default=list,
    )

    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # Handle delivery_challan_no / delivery_challan_number
        dc_no = (
            normalized.get("delivery_challan_no")
            if normalized.get("delivery_challan_no") is not None
            else normalized.get("deliveryChallanNo")
        )
        if dc_no is None:
            dc_no = (
                normalized.get("delivery_challan_number")
                if normalized.get("delivery_challan_number") is not None
                else normalized.get("deliveryChallanNumber")
            )
        if dc_no is not None:
            normalized["delivery_challan_no"] = str(dc_no).strip()

        # Handle delivery_challan_date
        dc_date = (
            normalized.get("delivery_challan_date")
            if normalized.get("delivery_challan_date") is not None
            else normalized.get("deliveryChallanDate")
        )
        if dc_date is not None:
            parsed = _parse_date(dc_date)
            if parsed is not None:
                normalized["delivery_challan_date"] = parsed.isoformat()

        # Handle project_id
        pid = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("projectId")
        )
        if pid is not None:
            try:
                normalized["project_id"] = int(pid)
            except (ValueError, TypeError):
                pass

        # Handle remark / remarks
        rem = (
            normalized.get("remark")
            if normalized.get("remark") is not None
            else normalized.get("remarks")
        )
        if rem is not None:
            normalized["remark"] = rem

        return normalized


class DeliveryChallanUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    delivery_challan_no = fields.String(
        required=False,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    delivery_challan_date = fields.Date(required=False)
    remark = fields.String(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(DeliveryChallanItemCreateSchema),
        required=False,
    )

    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        if "delivery_challan_no" in normalized or "delivery_challan_number" in normalized or "deliveryChallanNo" in normalized:
            dc_no = (
                normalized.get("delivery_challan_no")
                or normalized.get("delivery_challan_number")
                or normalized.get("deliveryChallanNo")
            )
            if dc_no is not None:
                normalized["delivery_challan_no"] = str(dc_no).strip()

        if "delivery_challan_date" in normalized or "deliveryChallanDate" in normalized:
            dc_date = normalized.get("delivery_challan_date") or normalized.get("deliveryChallanDate")
            if dc_date is not None:
                parsed = _parse_date(dc_date)
                if parsed is not None:
                    normalized["delivery_challan_date"] = parsed.isoformat()

        if "project_id" in normalized or "projectId" in normalized:
            pid = normalized.get("project_id") or normalized.get("projectId")
            if pid is not None:
                try:
                    normalized["project_id"] = int(pid)
                except (ValueError, TypeError):
                    pass

        if "remark" in normalized or "remarks" in normalized:
            rem = normalized.get("remark") or normalized.get("remarks")
            if rem is not None:
                normalized["remark"] = rem

        return normalized


class DeliveryChallanResponseSchema(Schema):
    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    delivery_challan_no = fields.String(dump_only=True)
    delivery_challan_number = fields.String(dump_only=True)
    delivery_challan_date = fields.Date(dump_only=True)
    remark = fields.String(dump_only=True)
    remarks = fields.String(dump_only=True)
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

