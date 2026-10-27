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
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
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
                else (
                    normalized.get("description")
                    if normalized.get("description") is not None
                    else (
                        normalized.get("item_description")
                        if normalized.get("item_description") is not None
                        else normalized.get("itemDescription")
                    )
                )
            )
        if mat_name is not None and str(mat_name).strip() != "":
            normalized["material_name"] = str(mat_name).strip()
        elif mat_name is None:
            normalized["material_name"] = "Delivery Item"

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
            s_hsn = str(hsn).strip()
            normalized["hsn_code"] = s_hsn if s_hsn else None

        # Handle quantity fallback
        qty = (
            normalized.get("quantity")
            if normalized.get("quantity") is not None
            else (
                normalized.get("qty")
                if normalized.get("qty") is not None
                else (
                    normalized.get("unit")
                    if normalized.get("unit") is not None
                    else normalized.get("count")
                )
            )
        )
        if qty is None or str(qty).strip() in ("", "None", "0"):
            normalized["quantity"] = "1.000"
        else:
            try:
                q_dec = Decimal(str(qty).replace(",", "").strip())
                normalized["quantity"] = str(q_dec) if q_dec >= Decimal("0.001") else "1.000"
            except Exception:
                normalized["quantity"] = "1.000"

        # Handle unit_price / rate_per_unit fallback
        unit_price = (
            normalized.get("unit_price")
            if normalized.get("unit_price") is not None
            else (
                normalized.get("unitPrice")
                if normalized.get("unitPrice") is not None
                else (
                    normalized.get("rate_per_unit")
                    if normalized.get("rate_per_unit") is not None
                    else (
                        normalized.get("rate")
                        if normalized.get("rate") is not None
                        else normalized.get("price")
                    )
                )
            )
        )
        if unit_price is not None and str(unit_price).strip() != "":
            try:
                u_dec = Decimal(str(unit_price).replace(",", "").strip())
                normalized["unit_price"] = str(u_dec) if u_dec >= Decimal("0.00") else "0.00"
            except Exception:
                normalized["unit_price"] = "0.00"
        else:
            normalized["unit_price"] = "0.00"

        # Handle net_amount / total_amount fallback
        net_amt = (
            normalized.get("net_amount")
            if normalized.get("net_amount") is not None
            else (
                normalized.get("netAmount")
                if normalized.get("netAmount") is not None
                else (
                    normalized.get("total_amount")
                    if normalized.get("total_amount") is not None
                    else (
                        normalized.get("totalAmount")
                        if normalized.get("totalAmount") is not None
                        else (
                            normalized.get("amount")
                            if normalized.get("amount") is not None
                            else normalized.get("total_price")
                        )
                    )
                )
            )
        )
        if net_amt is not None and str(net_amt).strip() != "":
            try:
                n_dec = Decimal(str(net_amt).replace(",", "").strip())
                if n_dec <= Decimal("0.00"):
                    calc = (Decimal(normalized["quantity"]) * Decimal(normalized["unit_price"])).quantize(Decimal("0.01"))
                    normalized["net_amount"] = str(calc) if calc > Decimal("0.00") else "0.00"
                else:
                    normalized["net_amount"] = str(n_dec.quantize(Decimal("0.01")))
            except Exception:
                calc = (Decimal(normalized["quantity"]) * Decimal(normalized["unit_price"])).quantize(Decimal("0.01"))
                normalized["net_amount"] = str(calc)
        else:
            calc = (Decimal(normalized["quantity"]) * Decimal(normalized["unit_price"])).quantize(Decimal("0.01"))
            normalized["net_amount"] = str(calc)

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

    @pre_load
    def normalize_item_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        if "material_name" in normalized or "materialName" in normalized or "description" in normalized:
            mat = (
                normalized.get("material_name")
                if normalized.get("material_name") is not None
                else (
                    normalized.get("materialName")
                    if normalized.get("materialName") is not None
                    else normalized.get("description")
                )
            )
            if mat is not None and str(mat).strip() != "":
                normalized["material_name"] = str(mat).strip()

        if "hsn_code" in normalized or "hsnCode" in normalized or "hsn_sac" in normalized:
            hsn = (
                normalized.get("hsn_code")
                if normalized.get("hsn_code") is not None
                else (
                    normalized.get("hsnCode")
                    if normalized.get("hsnCode") is not None
                    else normalized.get("hsn_sac")
                )
            )
            if hsn is not None:
                s_hsn = str(hsn).strip()
                normalized["hsn_code"] = s_hsn if s_hsn else None

        if "quantity" in normalized or "qty" in normalized:
            qty = normalized.get("quantity") if normalized.get("quantity") is not None else normalized.get("qty")
            if qty is not None and str(qty).strip() not in ("", "None"):
                try:
                    q_dec = Decimal(str(qty).replace(",", "").strip())
                    normalized["quantity"] = str(q_dec) if q_dec >= Decimal("0.001") else "1.000"
                except Exception:
                    normalized["quantity"] = "1.000"
            elif qty == "":
                normalized["quantity"] = None

        if "unit_price" in normalized or "unitPrice" in normalized or "rate" in normalized or "rate_per_unit" in normalized:
            unit_price = (
                normalized.get("unit_price")
                if normalized.get("unit_price") is not None
                else (
                    normalized.get("unitPrice")
                    if normalized.get("unitPrice") is not None
                    else (
                        normalized.get("rate_per_unit")
                        if normalized.get("rate_per_unit") is not None
                        else normalized.get("rate")
                    )
                )
            )
            if unit_price is not None and str(unit_price).strip() != "":
                try:
                    u_dec = Decimal(str(unit_price).replace(",", "").strip())
                    normalized["unit_price"] = str(u_dec) if u_dec >= Decimal("0.00") else "0.00"
                except Exception:
                    normalized["unit_price"] = "0.00"

        if "net_amount" in normalized or "netAmount" in normalized or "total_amount" in normalized or "totalAmount" in normalized:
            net_amt = (
                normalized.get("net_amount")
                if normalized.get("net_amount") is not None
                else (
                    normalized.get("netAmount")
                    if normalized.get("netAmount") is not None
                    else (
                        normalized.get("total_amount")
                        if normalized.get("total_amount") is not None
                        else normalized.get("totalAmount")
                    )
                )
            )
            if net_amt is not None and str(net_amt).strip() != "":
                try:
                    n_dec = Decimal(str(net_amt).replace(",", "").strip())
                    normalized["net_amount"] = str(n_dec.quantize(Decimal("0.01")))
                except Exception:
                    pass

        return normalized


class DeliveryChallanItemResponseSchema(Schema):
    id = fields.Integer(dump_only=True)
    delivery_challan_id = fields.Integer(dump_only=True)
    material_name = fields.String(dump_only=True)
    material_description = fields.String(dump_only=True, attribute="material_name")
    description = fields.String(dump_only=True, attribute="material_name")
    hsn_code = fields.String(dump_only=True)
    hsn_sac = fields.String(dump_only=True, attribute="hsn_code")
    quantity = fields.Decimal(dump_only=True, as_string=True, places=3)
    unit_price = fields.Decimal(dump_only=True, as_string=True, places=2)
    rate_per_unit = fields.Decimal(dump_only=True, attribute="unit_price", as_string=True, places=2)
    net_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    amount = fields.Decimal(dump_only=True, attribute="net_amount", as_string=True, places=2)
    total_amount = fields.Decimal(dump_only=True, attribute="net_amount", as_string=True, places=2)
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
    gst_rate = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    gst_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    round_off = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    net_total = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    remark = fields.Raw(
        required=False,
        allow_none=True,
    )
    remarks = fields.Raw(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(DeliveryChallanItemCreateSchema),
        required=False,
        load_default=list,
    )
    attachments_count = fields.Integer(
        required=False,
        allow_none=True,
    )
    form_code = fields.String(
        required=False,
        allow_none=True,
    )

    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # Handle delivery_challan_no / delivery_challan_number / challan_no
        dc_no = (
            normalized.get("delivery_challan_no")
            if normalized.get("delivery_challan_no") is not None
            else (
                normalized.get("deliveryChallanNo")
                if normalized.get("deliveryChallanNo") is not None
                else (
                    normalized.get("delivery_challan_number")
                    if normalized.get("delivery_challan_number") is not None
                    else (
                        normalized.get("deliveryChallanNumber")
                        if normalized.get("deliveryChallanNumber") is not None
                        else (
                            normalized.get("challan_no")
                            if normalized.get("challan_no") is not None
                            else (
                                normalized.get("challanNo")
                                if normalized.get("challanNo") is not None
                                else (
                                    normalized.get("challan_number")
                                    if normalized.get("challan_number") is not None
                                    else normalized.get("challanNumber")
                                )
                            )
                        )
                    )
                )
            )
        )
        if dc_no is not None:
            normalized["delivery_challan_no"] = str(dc_no).strip()

        # Handle delivery_challan_date / challan_date
        dc_date = (
            normalized.get("delivery_challan_date")
            if normalized.get("delivery_challan_date") is not None
            else (
                normalized.get("deliveryChallanDate")
                if normalized.get("deliveryChallanDate") is not None
                else (
                    normalized.get("challan_date")
                    if normalized.get("challan_date") is not None
                    else (
                        normalized.get("challanDate")
                        if normalized.get("challanDate") is not None
                        else normalized.get("date")
                    )
                )
            )
        )
        if dc_date is not None and str(dc_date).strip() != "":
            parsed = _parse_date(dc_date)
            if parsed is not None:
                normalized["delivery_challan_date"] = parsed.isoformat()
        elif dc_date == "":
            normalized["delivery_challan_date"] = None

        # Handle project_id
        pid = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("projectId")
        )
        if pid is not None and str(pid).strip() != "":
            try:
                normalized["project_id"] = int(pid)
            except (ValueError, TypeError):
                pass
        elif pid == "":
            normalized.pop("project_id", None)

        # Handle gst_rate
        if "gst_rate" in normalized or "gstRate" in normalized or "gst" in normalized:
            gst_r = normalized.get("gst_rate") or normalized.get("gstRate") or normalized.get("gst")
            if gst_r is not None and str(gst_r).strip() != "":
                normalized["gst_rate"] = gst_r
            elif gst_r == "":
                normalized["gst_rate"] = None

        # Handle gst_amount
        if "gst_amount" in normalized or "gstAmount" in normalized:
            gst_a = normalized.get("gst_amount") or normalized.get("gstAmount")
            if gst_a is not None and str(gst_a).strip() != "":
                normalized["gst_amount"] = gst_a
            elif gst_a == "":
                normalized["gst_amount"] = None

        # Handle round_off
        if "round_off" in normalized or "roundOff" in normalized:
            ro = normalized.get("round_off") or normalized.get("roundOff")
            if ro is not None and str(ro).strip() != "":
                normalized["round_off"] = ro
            elif ro == "":
                normalized["round_off"] = None

        # Handle net_total
        if "net_total" in normalized or "netTotal" in normalized:
            nt = normalized.get("net_total") or normalized.get("netTotal")
            if nt is not None and str(nt).strip() != "":
                normalized["net_total"] = nt
            elif nt == "":
                normalized["net_total"] = None

        # Handle remark / remarks
        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]

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
    gst_rate = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    gst_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    round_off = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    net_total = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    remark = fields.Raw(
        required=False,
        allow_none=True,
    )
    remarks = fields.Raw(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(DeliveryChallanItemCreateSchema),
        required=False,
    )
    attachments_count = fields.Integer(
        required=False,
        allow_none=True,
    )
    form_code = fields.String(
        required=False,
        allow_none=True,
    )

    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        if "delivery_challan_no" in normalized or "delivery_challan_number" in normalized or "deliveryChallanNo" in normalized or "challan_no" in normalized:
            dc_no = (
                normalized.get("delivery_challan_no")
                or normalized.get("delivery_challan_number")
                or normalized.get("deliveryChallanNo")
                or normalized.get("challan_no")
            )
            if dc_no is not None:
                normalized["delivery_challan_no"] = str(dc_no).strip()

        if "delivery_challan_date" in normalized or "deliveryChallanDate" in normalized or "challan_date" in normalized:
            dc_date = (
                normalized.get("delivery_challan_date")
                or normalized.get("deliveryChallanDate")
                or normalized.get("challan_date")
            )
            if dc_date is not None and str(dc_date).strip() != "":
                parsed = _parse_date(dc_date)
                if parsed is not None:
                    normalized["delivery_challan_date"] = parsed.isoformat()
            elif dc_date == "":
                normalized["delivery_challan_date"] = None

        if "project_id" in normalized or "projectId" in normalized:
            pid = normalized.get("project_id") or normalized.get("projectId")
            if pid is not None and str(pid).strip() != "":
                try:
                    normalized["project_id"] = int(pid)
                except (ValueError, TypeError):
                    pass
            elif pid == "":
                normalized["project_id"] = None

        if "gst_rate" in normalized or "gstRate" in normalized or "gst" in normalized:
            gst_r = normalized.get("gst_rate") or normalized.get("gstRate") or normalized.get("gst")
            if gst_r is not None and str(gst_r).strip() != "":
                normalized["gst_rate"] = gst_r
            elif gst_r == "":
                normalized["gst_rate"] = None

        if "gst_amount" in normalized or "gstAmount" in normalized:
            gst_a = normalized.get("gst_amount") or normalized.get("gstAmount")
            if gst_a is not None and str(gst_a).strip() != "":
                normalized["gst_amount"] = gst_a
            elif gst_a == "":
                normalized["gst_amount"] = None

        if "round_off" in normalized or "roundOff" in normalized:
            ro = normalized.get("round_off") or normalized.get("roundOff")
            if ro is not None and str(ro).strip() != "":
                normalized["round_off"] = ro
            elif ro == "":
                normalized["round_off"] = None

        if "net_total" in normalized or "netTotal" in normalized:
            nt = normalized.get("net_total") or normalized.get("netTotal")
            if nt is not None and str(nt).strip() != "":
                normalized["net_total"] = nt
            elif nt == "":
                normalized["net_total"] = None

        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]

        return normalized


class DeliveryChallanResponseSchema(Schema):
    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    delivery_challan_no = fields.String(dump_only=True)
    delivery_challan_number = fields.String(dump_only=True)
    challan_no = fields.String(dump_only=True, attribute="delivery_challan_no")
    delivery_challan_date = fields.Date(dump_only=True)
    gst_rate = fields.Decimal(dump_only=True, as_string=True, places=2)
    gst_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    round_off = fields.Decimal(dump_only=True, as_string=True, places=2)
    net_total = fields.Decimal(dump_only=True, as_string=True, places=2)
    remark = fields.Raw(dump_only=True)
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
