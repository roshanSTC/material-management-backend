import re
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


class SupplierPackingListItemCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    material_name = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    description = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=500),
            _not_blank,
        ),
    )
    hsn_code = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )
    hsn_sac = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )
    quantity = fields.Decimal(
        required=False,
        load_default=Decimal("1.000"),
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )
    unit_price = fields.Decimal(
        required=False,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
        load_default=Decimal("0.00"),
    )
    net_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )
    weight = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.000")),
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

    @pre_load
    def normalize_item_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # Material name / description fallback
        mat_name = (
            normalized.get("material_name")
            if normalized.get("material_name") is not None
            else normalized.get("materialName")
        )
        desc = (
            normalized.get("description")
            if normalized.get("description") is not None
            else normalized.get("item_description")
            if normalized.get("item_description") is not None
            else normalized.get("material_description")
        )
        if desc is None or not str(desc).strip():
            if mat_name and str(mat_name).strip():
                desc = str(mat_name).strip()
            else:
                sr_no = normalized.get("sr_no") or 1
                desc = f"Packing Item {sr_no}"
        normalized["description"] = str(desc).strip()
        if not mat_name or not str(mat_name).strip():
            normalized["material_name"] = normalized["description"]
        else:
            normalized["material_name"] = str(mat_name).strip()

        # HSN aliases
        hsn = (
            normalized.get("hsn_code")
            if normalized.get("hsn_code") is not None
            else normalized.get("hsn_sac")
            if normalized.get("hsn_sac") is not None
            else normalized.get("hsn")
        )
        if hsn is not None and str(hsn).strip():
            cleaned_hsn = str(hsn).strip()
            normalized["hsn_code"] = cleaned_hsn
            normalized["hsn_sac"] = cleaned_hsn
        else:
            normalized["hsn_code"] = None
            normalized["hsn_sac"] = None

        # Unit weight
        uweight_val = (
            normalized.get("unit_weight")
            if normalized.get("unit_weight") is not None
            else normalized.get("unitWeight")
            if normalized.get("unitWeight") is not None
            else normalized.get("unit_weight_kg")
            if normalized.get("unit_weight_kg") is not None
            else normalized.get("weight")
        )
        if uweight_val is not None and str(uweight_val).strip() != "":
            try:
                normalized["unit_weight"] = str(Decimal(str(uweight_val).strip()))
            except Exception:
                normalized["unit_weight"] = None
        else:
            normalized["unit_weight"] = None

        # Total weight
        tot_weight_val = (
            normalized.get("total_weight")
            if normalized.get("total_weight") is not None
            else normalized.get("totalWeight")
        )
        if tot_weight_val is not None and str(tot_weight_val).strip() != "":
            try:
                normalized["total_weight"] = str(Decimal(str(tot_weight_val).strip()))
            except Exception:
                normalized["total_weight"] = None
        elif normalized.get("unit_weight") and (normalized.get("quantity") or normalized.get("qty")):
            try:
                q_temp = Decimal(str(normalized.get("quantity") or normalized.get("qty") or 1))
                normalized["total_weight"] = str(
                    (Decimal(normalized["unit_weight"]) * q_temp).quantize(Decimal("0.001"))
                )
            except Exception:
                normalized["total_weight"] = None
        else:
            normalized["total_weight"] = None

        normalized["weight"] = normalized.get("unit_weight")

        # Quantity
        qty_val = (
            normalized.get("quantity")
            if normalized.get("quantity") is not None
            else normalized.get("qty")
        )
        if qty_val is None or str(qty_val).strip() == "":
            try:
                uw = Decimal(str(normalized.get("unit_weight") or 0))
                tw = Decimal(str(normalized.get("total_weight") or 0))
                if uw > 0 and tw > 0:
                    qty_val = (tw / uw).quantize(Decimal("0.001"))
                else:
                    qty_val = "1.000"
            except Exception:
                qty_val = "1.000"
        else:
            try:
                clean_q = re.sub(r"[^\d.]", "", str(qty_val))
                d_q = Decimal(clean_q) if clean_q else Decimal("1.000")
                if d_q <= 0:
                    d_q = Decimal("1.000")
                qty_val = str(d_q)
            except Exception:
                qty_val = "1.000"
        normalized["quantity"] = str(qty_val).strip()

        # Unit price
        price_val = (
            normalized.get("unit_price")
            if normalized.get("unit_price") is not None
            else normalized.get("unitPrice")
            if normalized.get("unitPrice") is not None
            else normalized.get("rate")
        )
        if price_val is not None and str(price_val).strip() != "":
            try:
                clean_p = re.sub(r"[^\d.]", "", str(price_val))
                normalized["unit_price"] = str(Decimal(clean_p)) if clean_p else "0.00"
            except Exception:
                normalized["unit_price"] = "0.00"
        else:
            normalized["unit_price"] = "0.00"

        # Net amount / total_amount
        net_val = (
            normalized.get("net_amount")
            if normalized.get("net_amount") is not None
            else normalized.get("netAmount")
            if normalized.get("netAmount") is not None
            else normalized.get("total_amount")
            if normalized.get("total_amount") is not None
            else normalized.get("totalAmount")
        )
        if net_val is not None and str(net_val).strip() != "":
            try:
                clean_n = re.sub(r"[^\d.]", "", str(net_val))
                normalized["net_amount"] = str(Decimal(clean_n)) if clean_n else None
            except Exception:
                normalized["net_amount"] = None
        else:
            try:
                d_q = Decimal(normalized["quantity"])
                d_p = Decimal(normalized["unit_price"])
                normalized["net_amount"] = str((d_q * d_p).quantize(Decimal("0.01")))
            except Exception:
                normalized["net_amount"] = None

        return normalized


class SupplierPackingListItemUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=False)
    material_name = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    description = fields.String(
        required=False,
        validate=validate.And(
            validate.Length(min=1, max=500),
            _not_blank,
        ),
    )
    hsn_code = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )
    hsn_sac = fields.String(
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
        validate=validate.Range(min=Decimal("0.00")),
    )
    weight = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.000")),
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

    @pre_load
    def normalize_item_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        if "description" in normalized or "material_name" in normalized:
            desc = normalized.get("description") or normalized.get("material_name")
            if desc is not None and str(desc).strip():
                normalized["description"] = str(desc).strip()
                normalized["material_name"] = str(desc).strip()
        if "quantity" in normalized:
            qty = normalized.get("quantity")
            if qty is not None and str(qty).strip() != "":
                try:
                    clean_q = re.sub(r"[^\d.]", "", str(qty))
                    normalized["quantity"] = str(Decimal(clean_q)) if clean_q else "1.000"
                except Exception:
                    normalized["quantity"] = "1.000"
            else:
                normalized["quantity"] = None
        return normalized


class SupplierPackingListItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    sr_no = fields.Integer(required=False, allow_none=True)
    packing_list_id = fields.Integer(required=True)
    supplier_packing_list_id = fields.Integer(dump_only=True)
    material_name = fields.String(allow_none=True)
    description = fields.String(required=True)
    material_description = fields.String(dump_only=True)
    hsn_code = fields.String(allow_none=True)
    hsn = fields.String(dump_only=True)
    hsn_sac = fields.String(dump_only=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, required=True)
    net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    weight = fields.Decimal(as_string=True, places=3, allow_none=True)
    unit_weight = fields.Decimal(as_string=True, places=3, allow_none=True)
    unit_weight_kg = fields.Decimal(dump_only=True, as_string=True, places=3, allow_none=True)
    total_weight = fields.Decimal(as_string=True, places=3, allow_none=True)
    created_at = fields.DateTime(required=True)


class SupplierPackingListCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    supplier_id = fields.Integer(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1),
    )
    packing_list_no = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    packing_list_date = fields.Date(
        required=True,
    )
    packing_condition = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    weight = fields.Decimal(
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
    remark = fields.Raw(
        required=False,
        allow_none=True,
    )
    remarks = fields.Raw(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(SupplierPackingListItemCreateSchema),
        required=True,
        validate=validate.Length(min=1),
    )

    @pre_load
    def normalize_packing_list_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # Project ID
        resolved_pid = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("projectId")
        )
        if resolved_pid is not None and str(resolved_pid).strip() != "":
            normalized["project_id"] = str(resolved_pid).strip()

        # Supplier ID
        resolved_sid = (
            normalized.get("supplier_id")
            if normalized.get("supplier_id") is not None
            else normalized.get("supplierId")
        )
        if resolved_sid is not None and str(resolved_sid).strip() != "":
            normalized["supplier_id"] = str(resolved_sid).strip()

        # Packing list no / packing_list_number
        resolved_no = (
            normalized.get("packing_list_no")
            if normalized.get("packing_list_no") is not None
            else normalized.get("packing_list_number")
            if normalized.get("packing_list_number") is not None
            else normalized.get("packingListNo")
            if normalized.get("packingListNo") is not None
            else normalized.get("packingListNumber")
        )
        if resolved_no is not None:
            normalized["packing_list_no"] = str(resolved_no).strip()

        # Packing list date
        resolved_date = (
            normalized.get("packing_list_date")
            if normalized.get("packing_list_date") is not None
            else normalized.get("packingListDate")
        )
        if resolved_date is not None:
            pdate = _parse_date(resolved_date)
            if pdate:
                normalized["packing_list_date"] = pdate.isoformat()

        # Packing condition
        resolved_cond = (
            normalized.get("packing_condition")
            if normalized.get("packing_condition") is not None
            else normalized.get("packingCondition")
        )
        if resolved_cond is not None:
            normalized["packing_condition"] = str(resolved_cond).strip()

        # Weight / Total weight / gross_weight / net_weight
        resolved_tot_weight = (
            normalized.get("total_weight")
            if normalized.get("total_weight") is not None
            else normalized.get("totalWeight")
            if normalized.get("totalWeight") is not None
            else normalized.get("total_gross_weight_kg")
            if normalized.get("total_gross_weight_kg") is not None
            else normalized.get("gross_weight")
            if normalized.get("gross_weight") is not None
            else normalized.get("grossWeight")
            if normalized.get("grossWeight") is not None
            else normalized.get("weight")
        )
        if resolved_tot_weight is not None and str(resolved_tot_weight).strip() != "":
            try:
                normalized["total_weight"] = str(Decimal(str(resolved_tot_weight).strip()))
            except Exception:
                normalized["total_weight"] = str(resolved_tot_weight).strip()

        resolved_weight = (
            normalized.get("net_weight")
            if normalized.get("net_weight") is not None
            else normalized.get("netWeight")
            if normalized.get("netWeight") is not None
            else normalized.get("weight")
            if normalized.get("weight") is not None
            else resolved_tot_weight
        )
        if resolved_weight is not None and str(resolved_weight).strip() != "":
            try:
                normalized["weight"] = str(Decimal(str(resolved_weight).strip()))
            except Exception:
                normalized["weight"] = str(resolved_weight).strip()

        # Fallback total_weight from items if root is missing
        if not normalized.get("total_weight") and normalized.get("items"):
            try:
                sum_tw = sum(
                    Decimal(str(it.get("total_weight") or it.get("unit_weight") or 0))
                    for it in normalized["items"]
                    if isinstance(it, (dict, Mapping))
                )
                if sum_tw > 0:
                    normalized["total_weight"] = str(sum_tw)
                    if not normalized.get("weight"):
                        normalized["weight"] = str(sum_tw)
            except Exception:
                pass

        # Remark / remarks
        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]

        # clean items
        if "items" in normalized and isinstance(normalized["items"], list):
            normalized["items"] = [
                item for item in normalized["items"] if isinstance(item, (dict, Mapping))
            ]

        return normalized


class SupplierPackingListUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=False,
        validate=validate.Range(min=1),
    )
    supplier_id = fields.Integer(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1),
    )
    packing_list_no = fields.String(
        required=False,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    packing_list_date = fields.Date(
        required=False,
    )
    packing_condition = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    weight = fields.Decimal(
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
    remark = fields.Raw(
        required=False,
        allow_none=True,
    )
    remarks = fields.Raw(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(SupplierPackingListItemCreateSchema),
        required=False,
    )

    @pre_load
    def normalize_update_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        if "projectId" in normalized and "project_id" not in normalized:
            normalized["project_id"] = normalized["projectId"]
        if "supplierId" in normalized and "supplier_id" not in normalized:
            normalized["supplier_id"] = normalized["supplierId"]
        if "packing_list_number" in normalized and "packing_list_no" not in normalized:
            normalized["packing_list_no"] = normalized["packing_list_number"]
        if "packingListNo" in normalized and "packing_list_no" not in normalized:
            normalized["packing_list_no"] = normalized["packingListNo"]
        if "packingListNumber" in normalized and "packing_list_no" not in normalized:
            normalized["packing_list_no"] = normalized["packingListNumber"]
        if "packingListDate" in normalized and "packing_list_date" not in normalized:
            normalized["packing_list_date"] = normalized["packingListDate"]
        if "packingCondition" in normalized and "packing_condition" not in normalized:
            normalized["packing_condition"] = normalized["packingCondition"]
        if "totalWeight" in normalized and "total_weight" not in normalized:
            normalized["total_weight"] = normalized["totalWeight"]
        if "total_gross_weight_kg" in normalized and "total_weight" not in normalized:
            normalized["total_weight"] = normalized["total_gross_weight_kg"]
        if "gross_weight" in normalized and "total_weight" not in normalized:
            normalized["total_weight"] = normalized["gross_weight"]
        if "net_weight" in normalized and "weight" not in normalized:
            normalized["weight"] = normalized["net_weight"]
        if "remarks" in normalized and "remark" not in normalized:
            normalized["remark"] = normalized["remarks"]

        return normalized


class SupplierPackingListQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, validate=validate.Range(min=1))

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        resolved_pid = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("projectId")
        )
        if resolved_pid is not None and str(resolved_pid).strip() != "":
            normalized["project_id"] = str(resolved_pid).strip()

        resolved_sid = (
            normalized.get("supplier_id")
            if normalized.get("supplier_id") is not None
            else normalized.get("supplierId")
        )
        if resolved_sid is not None and str(resolved_sid).strip() != "":
            normalized["supplier_id"] = str(resolved_sid).strip()

        resolved_no = (
            normalized.get("packing_list_no")
            if normalized.get("packing_list_no") is not None
            else normalized.get("packing_list_number")
        )
        if resolved_no is not None and str(resolved_no).strip() != "":
            normalized["packing_list_no"] = str(resolved_no).strip()

        return normalized


class SupplierPackingListResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=False, allow_none=True)
    packing_list_no = fields.String(required=True)
    packing_list_number = fields.String(dump_only=True)
    packing_list_date = fields.Date(required=True)
    packing_condition = fields.String(allow_none=True)
    weight = fields.Decimal(as_string=True, places=3, allow_none=True)
    total_weight = fields.Decimal(as_string=True, places=3, allow_none=True)
    total_gross_weight_kg = fields.Decimal(dump_only=True, as_string=True, places=3, allow_none=True)
    gross_weight = fields.Decimal(attribute="total_weight", dump_only=True, as_string=True, places=3, allow_none=True)
    net_weight = fields.Decimal(attribute="weight", dump_only=True, as_string=True, places=3, allow_none=True)
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(
        fields.Nested(SupplierPackingListItemResponseSchema),
        required=True,
    )
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        required=False,
    )


class LatestSupplierPackingListQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True, validate=validate.Range(min=1))

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        resolved_pid = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("projectId")
        )
        if resolved_pid is not None and str(resolved_pid).strip() != "":
            normalized["project_id"] = str(resolved_pid).strip()
        return normalized


class LatestSupplierPackingListResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    total_gross_weight_kg = fields.Decimal(as_string=True, places=3, allow_none=True)
    total_weight = fields.Decimal(as_string=True, places=3, allow_none=True)
