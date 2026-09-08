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


class CustomerDeliveryPackingListItemCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    package_no = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
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
    weight = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
    )

    @pre_load
    def normalize_item_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # Handle package_no
        pkg_no = (
            normalized.get("package_no")
            if normalized.get("package_no") is not None
            else normalized.get("packageNo")
        )
        if pkg_no is not None:
            normalized["package_no"] = str(pkg_no).strip()

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

        # Handle weight / total_weight_kg / weight_per_unit_kg
        w = (
            normalized.get("weight")
            if normalized.get("weight") is not None
            else normalized.get("total_weight_kg")
        )
        if w is None:
            w = normalized.get("weight_per_unit_kg")
        if w is not None:
            normalized["weight"] = w

        return normalized


class CustomerDeliveryPackingListItemUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=False, allow_none=True)
    package_no = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
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
    weight = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
    )


class CustomerDeliveryPackingListItemResponseSchema(Schema):
    id = fields.Integer(dump_only=True)
    packing_list_id = fields.Integer(dump_only=True)
    package_no = fields.String(dump_only=True)
    material_name = fields.String(dump_only=True)
    hsn_code = fields.String(dump_only=True)
    quantity = fields.Decimal(dump_only=True, as_string=True, places=3)
    weight = fields.Decimal(dump_only=True, as_string=True, places=3)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class CustomerDeliveryPackingListCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True)
    packing_list_no = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    packing_list_date = fields.Date(required=True)
    total_no_of_packs = fields.Integer(
        required=False,
        allow_none=True,
    )
    packing_condition = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    net_weight = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    gross_weight = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    remark = fields.String(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(CustomerDeliveryPackingListItemCreateSchema),
        required=False,
        load_default=list,
    )

    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # Handle packing_list_no / packing_list_number
        pl_no = (
            normalized.get("packing_list_no")
            if normalized.get("packing_list_no") is not None
            else normalized.get("packingListNo")
        )
        if pl_no is None:
            pl_no = (
                normalized.get("packing_list_number")
                if normalized.get("packing_list_number") is not None
                else normalized.get("packingListNumber")
            )
        if pl_no is not None:
            normalized["packing_list_no"] = str(pl_no).strip()

        # Handle packing_list_date
        pl_date = (
            normalized.get("packing_list_date")
            if normalized.get("packing_list_date") is not None
            else normalized.get("packingListDate")
        )
        if pl_date is not None:
            parsed = _parse_date(pl_date)
            if parsed is not None:
                normalized["packing_list_date"] = parsed.isoformat()

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

        # Handle total_no_of_packs
        tnop = (
            normalized.get("total_no_of_packs")
            if normalized.get("total_no_of_packs") is not None
            else normalized.get("totalNoOfPacks")
        )
        if tnop is not None:
            try:
                normalized["total_no_of_packs"] = int(tnop)
            except (ValueError, TypeError):
                pass

        # Handle packing_condition
        cond = (
            normalized.get("packing_condition")
            if normalized.get("packing_condition") is not None
            else normalized.get("packingCondition")
        )
        if cond is not None:
            normalized["packing_condition"] = str(cond).strip()

        # Handle net_weight / net_weight_kg
        nw = (
            normalized.get("net_weight")
            if normalized.get("net_weight") is not None
            else normalized.get("netWeight")
        )
        if nw is None:
            nw = normalized.get("net_weight_kg")
        if nw is not None:
            normalized["net_weight"] = str(nw).strip()

        # Handle gross_weight / gross_weight_kg
        gw = (
            normalized.get("gross_weight")
            if normalized.get("gross_weight") is not None
            else normalized.get("grossWeight")
        )
        if gw is None:
            gw = normalized.get("gross_weight_kg")
        if gw is not None:
            normalized["gross_weight"] = str(gw).strip()

        # Handle remark / remarks
        rem = (
            normalized.get("remark")
            if normalized.get("remark") is not None
            else normalized.get("remarks")
        )
        if rem is not None:
            normalized["remark"] = rem

        return normalized


class CustomerDeliveryPackingListUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    packing_list_no = fields.String(
        required=False,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    packing_list_date = fields.Date(required=False)
    total_no_of_packs = fields.Integer(
        required=False,
        allow_none=True,
    )
    packing_condition = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    net_weight = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    gross_weight = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    remark = fields.String(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(CustomerDeliveryPackingListItemCreateSchema),
        required=False,
    )

    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        if "packing_list_no" in normalized or "packing_list_number" in normalized or "packingListNo" in normalized:
            pl_no = normalized.get("packing_list_no") or normalized.get("packing_list_number") or normalized.get("packingListNo")
            if pl_no is not None:
                normalized["packing_list_no"] = str(pl_no).strip()

        if "packing_list_date" in normalized or "packingListDate" in normalized:
            pl_date = normalized.get("packing_list_date") or normalized.get("packingListDate")
            if pl_date is not None:
                parsed = _parse_date(pl_date)
                if parsed is not None:
                    normalized["packing_list_date"] = parsed.isoformat()

        if "project_id" in normalized or "projectId" in normalized:
            pid = normalized.get("project_id") or normalized.get("projectId")
            if pid is not None:
                try:
                    normalized["project_id"] = int(pid)
                except (ValueError, TypeError):
                    pass

        if "total_no_of_packs" in normalized or "totalNoOfPacks" in normalized:
            tnop = normalized.get("total_no_of_packs") or normalized.get("totalNoOfPacks")
            if tnop is not None:
                try:
                    normalized["total_no_of_packs"] = int(tnop)
                except (ValueError, TypeError):
                    pass

        if "packing_condition" in normalized or "packingCondition" in normalized:
            cond = normalized.get("packing_condition") or normalized.get("packingCondition")
            if cond is not None:
                normalized["packing_condition"] = str(cond).strip()

        if "net_weight" in normalized or "net_weight_kg" in normalized or "netWeight" in normalized:
            nw = normalized.get("net_weight") or normalized.get("net_weight_kg") or normalized.get("netWeight")
            if nw is not None:
                normalized["net_weight"] = str(nw).strip()

        if "gross_weight" in normalized or "gross_weight_kg" in normalized or "grossWeight" in normalized:
            gw = normalized.get("gross_weight") or normalized.get("gross_weight_kg") or normalized.get("grossWeight")
            if gw is not None:
                normalized["gross_weight"] = str(gw).strip()

        if "remark" in normalized or "remarks" in normalized:
            rem = normalized.get("remark") or normalized.get("remarks")
            if rem is not None:
                normalized["remark"] = rem

        return normalized


class CustomerDeliveryPackingListResponseSchema(Schema):
    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    packing_list_no = fields.String(dump_only=True)
    packing_list_number = fields.String(dump_only=True)
    packing_list_date = fields.Date(dump_only=True)
    total_no_of_packs = fields.Integer(dump_only=True)
    packing_condition = fields.String(dump_only=True)
    net_weight = fields.String(dump_only=True)
    gross_weight = fields.String(dump_only=True)
    remark = fields.String(dump_only=True)
    remarks = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    items = fields.List(
        fields.Nested(CustomerDeliveryPackingListItemResponseSchema),
        dump_only=True,
    )
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_only=True,
    )


class CustomerDeliveryPackingListQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    packing_list_no = fields.String(required=False)

