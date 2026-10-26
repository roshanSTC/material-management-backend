from collections.abc import Mapping
from datetime import date, datetime

from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    pre_load,
    validate,
)

from app.schemas.attachment import AttachmentResponseSchema


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
        return date.fromisoformat(s[:10])
    except Exception:
        pass
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValidationError(f"Invalid date format: {val}. Expected YYYY-MM-DD.")


def _normalize_import_logistics_payload(raw_data):
    if not isinstance(raw_data, Mapping):
        return raw_data
    normalized = dict(raw_data)

    # Date normalization
    raw_date = (
        normalized.get("date")
        or normalized.get("lr_rr_awb_date")
        or normalized.get("lr_rr_date")
        or normalized.get("transport_date")
        or normalized.get("logistics_date")
    )
    if raw_date is not None:
        d = _parse_date(raw_date)
        if d is not None:
            normalized["date"] = d.isoformat()
            normalized["lr_rr_awb_date"] = d.isoformat()
            normalized["transport_date"] = d.isoformat()

    # Logistic type / mode normalization
    raw_mode = (
        normalized.get("logistic_type")
        or normalized.get("transportation_mode")
        or normalized.get("transport_mode")
        or normalized.get("mode")
    )
    if raw_mode:
        mode_str = str(raw_mode).strip().lower()
        if "air" in mode_str:
            norm_type = "air"
        elif any(s in mode_str for s in ("sea", "ocean", "ship")):
            norm_type = "sea"
        elif "form_code" in normalized or "from_location" in normalized or "transportation_mode" in normalized:
            # If coming from transportation details form, map road/train to air category
            norm_type = "air"
        else:
            norm_type = mode_str

        normalized["logistic_type"] = norm_type
        if "transportation_mode" not in normalized:
            normalized["transportation_mode"] = raw_mode
        if "transport_mode" not in normalized:
            normalized["transport_mode"] = norm_type
    elif "logistic_type" not in normalized:
        normalized["logistic_type"] = "air"
        normalized["transportation_mode"] = "Air Cargo"
        normalized["transport_mode"] = "air"

    # Number / Waybill aliases
    raw_no = (
        normalized.get("lr_rr_awb_no")
        or normalized.get("lr_no")
        or normalized.get("rr_no")
        or normalized.get("awb_no")
        or normalized.get("lr_number")
        or normalized.get("airway_bill_no")
        or normalized.get("airway_bill_number")
        or normalized.get("bill_of_lading_no")
    )
    if raw_no:
        clean_no = str(raw_no).strip()
        normalized["lr_rr_awb_no"] = clean_no
        l_type = normalized.get("logistic_type", "air")
        if l_type == "sea":
            if "bill_of_lading_no" not in normalized:
                normalized["bill_of_lading_no"] = clean_no
        else:
            if "airway_bill_no" not in normalized:
                normalized["airway_bill_no"] = clean_no

    # Air fields aliases
    if "airway_bill_number" in normalized and "airway_bill_no" not in normalized:
        normalized["airway_bill_no"] = normalized["airway_bill_number"]
    if "flight_number" in normalized and "flight_no" not in normalized:
        normalized["flight_no"] = normalized["flight_number"]

    # Location aliases
    from_loc = normalized.get("from_location") or normalized.get("fromLocation")
    if from_loc:
        clean_from = str(from_loc).strip()
        normalized["from_location"] = clean_from
        if normalized.get("logistic_type") == "sea":
            if "port_of_loading" not in normalized:
                normalized["port_of_loading"] = clean_from
        else:
            if "airport_of_loading" not in normalized:
                normalized["airport_of_loading"] = clean_from

    to_loc = normalized.get("to_location") or normalized.get("toLocation")
    if to_loc:
        clean_to = str(to_loc).strip()
        normalized["to_location"] = clean_to
        if "port_of_discharge" not in normalized:
            normalized["port_of_discharge"] = clean_to

    # Charges aliases
    charges = (
        normalized.get("total_transportation_charges")
        or normalized.get("totalTransportationCharges")
        or normalized.get("transport_charges")
        or normalized.get("transportCharges")
    )
    if charges is not None and str(charges).strip() != "":
        normalized["total_transportation_charges"] = charges
        normalized["transport_charges"] = charges

    # String stripping
    for k in (
        "airway_bill_no",
        "flight_name",
        "flight_no",
        "airport_of_loading",
        "port_of_discharge",
        "bill_of_lading_no",
        "vessel_name",
        "voyage_no",
        "port_of_loading",
        "lr_rr_awb_no",
        "lr_no",
        "rr_no",
        "awb_no",
        "from_location",
        "to_location",
    ):
        if k in normalized and isinstance(normalized[k], str):
            normalized[k] = normalized[k].strip()

    if "remarks" in normalized and not normalized.get("remark"):
        normalized["remark"] = normalized["remarks"]
    elif "remark" in normalized and not normalized.get("remarks"):
        normalized["remarks"] = normalized["remark"]

    return normalized


class ImportLogisticsCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=False, allow_none=True)
    logistic_type = fields.String(
        required=True,
        validate=validate.OneOf(
            ["air", "sea"],
            error="logistic_type must be either 'air' or 'sea'.",
        ),
    )
    date = fields.Date(required=True)
    port_of_discharge = fields.String(allow_none=True, load_default=None)
    remark = fields.Raw(allow_none=True, load_default=None)
    remarks = fields.Raw(allow_none=True, load_default=None)

    # Air transport fields
    airway_bill_no = fields.String(allow_none=True, load_default=None)
    flight_name = fields.String(allow_none=True, load_default=None)
    flight_no = fields.String(allow_none=True, load_default=None)
    airport_of_loading = fields.String(allow_none=True, load_default=None)

    # Sea transport fields
    bill_of_lading_no = fields.String(allow_none=True, load_default=None)
    vessel_name = fields.String(allow_none=True, load_default=None)
    voyage_no = fields.String(allow_none=True, load_default=None)
    port_of_loading = fields.String(allow_none=True, load_default=None)

    # Transportation Details (Form 21) aliases
    transportation_mode = fields.Raw(allow_none=True, load_default=None)
    transport_mode = fields.Raw(allow_none=True, load_default=None)
    lr_rr_awb_no = fields.String(allow_none=True, load_default=None)
    lr_rr_awb_date = fields.Date(allow_none=True, load_default=None)
    transport_date = fields.Date(allow_none=True, load_default=None)
    from_location = fields.String(allow_none=True, load_default=None)
    to_location = fields.String(allow_none=True, load_default=None)
    total_transportation_charges = fields.Decimal(allow_none=True, load_default=None, as_string=True, places=2)
    transport_charges = fields.Decimal(allow_none=True, load_default=None, as_string=True, places=2)
    items = fields.Raw(allow_none=True, load_default=None)
    attachments_count = fields.Raw(allow_none=True, load_default=None)
    form_code = fields.Raw(allow_none=True, load_default=None)

    @pre_load
    def prepare_data(self, data, **kwargs):
        return _normalize_import_logistics_payload(data)


class ImportLogisticsUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    supplier_id = fields.Integer(required=False, allow_none=True)
    logistic_type = fields.String(
        required=False,
        validate=validate.OneOf(
            ["air", "sea"],
            error="logistic_type must be either 'air' or 'sea'.",
        ),
    )
    date = fields.Date(required=False)
    port_of_discharge = fields.String(allow_none=True)
    remark = fields.Raw(allow_none=True)
    remarks = fields.Raw(allow_none=True)

    # Air transport fields
    airway_bill_no = fields.String(allow_none=True)
    flight_name = fields.String(allow_none=True)
    flight_no = fields.String(allow_none=True)
    airport_of_loading = fields.String(allow_none=True)

    # Sea transport fields
    bill_of_lading_no = fields.String(allow_none=True)
    vessel_name = fields.String(allow_none=True)
    voyage_no = fields.String(allow_none=True)
    port_of_loading = fields.String(allow_none=True)

    # Transportation Details (Form 21) aliases
    transportation_mode = fields.Raw(allow_none=True)
    transport_mode = fields.Raw(allow_none=True)
    lr_rr_awb_no = fields.String(allow_none=True)
    lr_rr_awb_date = fields.Date(allow_none=True)
    transport_date = fields.Date(allow_none=True)
    from_location = fields.String(allow_none=True)
    to_location = fields.String(allow_none=True)
    total_transportation_charges = fields.Decimal(allow_none=True, as_string=True, places=2)
    transport_charges = fields.Decimal(allow_none=True, as_string=True, places=2)
    items = fields.Raw(allow_none=True)
    attachments_count = fields.Raw(allow_none=True)
    form_code = fields.Raw(allow_none=True)

    @pre_load
    def prepare_data(self, data, **kwargs):
        return _normalize_import_logistics_payload(data)


class ImportLogisticsQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, allow_none=True)


class ImportLogisticsResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(allow_none=True)
    logistic_type = fields.String(required=True)
    date = fields.Date(required=True)
    port_of_discharge = fields.String(allow_none=True)
    remarks = fields.Raw(allow_none=True)

    # Air fields
    airway_bill_no = fields.String(allow_none=True)
    flight_name = fields.String(allow_none=True)
    flight_no = fields.String(allow_none=True)
    airport_of_loading = fields.String(allow_none=True)

    # Sea fields
    bill_of_lading_no = fields.String(allow_none=True)
    vessel_name = fields.String(allow_none=True)
    voyage_no = fields.String(allow_none=True)
    port_of_loading = fields.String(allow_none=True)

    # Transport Details aliases
    transportation_mode = fields.String(dump_only=True)
    transport_mode = fields.String(dump_only=True)
    lr_rr_awb_no = fields.String(dump_only=True)
    lr_rr_awb_date = fields.Date(dump_only=True)
    transport_date = fields.Date(dump_only=True)
    from_location = fields.String(dump_only=True)
    to_location = fields.String(dump_only=True)
    total_transportation_charges = fields.Decimal(dump_only=True, as_string=True, places=2)
    transport_charges = fields.Decimal(dump_only=True, as_string=True, places=2)

    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)

    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_default=[],
    )
