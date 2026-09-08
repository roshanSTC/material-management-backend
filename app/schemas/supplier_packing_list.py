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
        required=True,
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
        if not desc and mat_name:
            desc = mat_name
        if not mat_name and desc:
            mat_name = desc

        if mat_name is not None:
            normalized["material_name"] = str(mat_name).strip()
        if desc is not None:
            normalized["description"] = str(desc).strip()

        # HSN aliases
        hsn = (
            normalized.get("hsn_code")
            if normalized.get("hsn_code") is not None
            else normalized.get("hsn_sac")
            if normalized.get("hsn_sac") is not None
            else normalized.get("hsn")
        )
        if hsn is not None:
            cleaned_hsn = str(hsn).strip()
            normalized["hsn_code"] = cleaned_hsn
            normalized["hsn_sac"] = cleaned_hsn

        # Quantity
        qty_val = (
            normalized.get("quantity")
            if normalized.get("quantity") is not None
            else normalized.get("qty")
        )
        if qty_val is not None:
            normalized["quantity"] = str(qty_val).strip()

        # Unit price
        price_val = (
            normalized.get("unit_price")
            if normalized.get("unit_price") is not None
            else normalized.get("unitPrice")
            if normalized.get("unitPrice") is not None
            else normalized.get("rate")
        )
        if price_val is not None:
            normalized["unit_price"] = str(price_val).strip()

        # Net amount
        net_val = (
            normalized.get("net_amount")
            if normalized.get("net_amount") is not None
            else normalized.get("netAmount")
        )
        if net_val is not None:
            normalized["net_amount"] = str(net_val).strip()

        # Weight / Unit weight / Total weight
        uweight_val = (
            normalized.get("unit_weight")
            if normalized.get("unit_weight") is not None
            else normalized.get("unitWeight")
            if normalized.get("unitWeight") is not None
            else normalized.get("unit_weight_kg")
            if normalized.get("unit_weight_kg") is not None
            else normalized.get("weight")
        )
        if uweight_val is not None:
            normalized["unit_weight"] = str(uweight_val).strip()

        weight_val = (
            normalized.get("weight")
            if normalized.get("weight") is not None
            else uweight_val
        )
        if weight_val is not None:
            normalized["weight"] = str(weight_val).strip()

        tot_weight_val = (
            normalized.get("total_weight")
            if normalized.get("total_weight") is not None
            else normalized.get("totalWeight")
        )
        if tot_weight_val is not None:
            normalized["total_weight"] = str(tot_weight_val).strip()

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


class SupplierPackingListItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
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
    remark = fields.String(
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

        # Weight / Total weight
        resolved_tot_weight = (
            normalized.get("total_weight")
            if normalized.get("total_weight") is not None
            else normalized.get("totalWeight")
            if normalized.get("totalWeight") is not None
            else normalized.get("total_gross_weight_kg")
            if normalized.get("total_gross_weight_kg") is not None
            else normalized.get("weight")
        )
        if resolved_tot_weight is not None:
            normalized["total_weight"] = str(resolved_tot_weight).strip()

        resolved_weight = (
            normalized.get("weight")
            if normalized.get("weight") is not None
            else resolved_tot_weight
        )
        if resolved_weight is not None:
            normalized["weight"] = str(resolved_weight).strip()

        # Remark / remarks
        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]

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
    remark = fields.String(
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
    supplier_id = fields.Integer(required=True)
    packing_list_no = fields.String(required=True)
    packing_list_number = fields.String(dump_only=True)
    packing_list_date = fields.Date(required=True)
    packing_condition = fields.String(allow_none=True)
    weight = fields.Decimal(as_string=True, places=3, allow_none=True)
    total_weight = fields.Decimal(as_string=True, places=3, allow_none=True)
    total_gross_weight_kg = fields.Decimal(dump_only=True, as_string=True, places=3, allow_none=True)
    remark = fields.String(allow_none=True)
    remarks = fields.String(dump_only=True)
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

