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
        return date.fromisoformat(s[:10])
    except Exception:
        raise ValidationError(f"Invalid date format: {val}")


def _clean_decimal(val):
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    try:
        return float(Decimal(s.replace(",", "")))
    except Exception:
        return None


def _normalize_bill_of_entry_payload(raw_data, is_create=True):
    if not isinstance(raw_data, Mapping):
        return raw_data
    normalized = dict(raw_data)

    # Date normalization
    raw_date = (
        normalized.get("date")
        if normalized.get("date") is not None
        else (
            normalized.get("entry_date")
            if normalized.get("entry_date") is not None
            else (
                normalized.get("entryDate")
                if normalized.get("entryDate") is not None
                else (
                    normalized.get("bill_of_entry_date")
                    if normalized.get("bill_of_entry_date") is not None
                    else (
                        normalized.get("billOfEntryDate")
                        if normalized.get("billOfEntryDate") is not None
                        else (
                            normalized.get("boe_filing_date")
                            if normalized.get("boe_filing_date") is not None
                            else (
                                normalized.get("boeFilingDate")
                                if normalized.get("boeFilingDate") is not None
                                else (
                                    normalized.get("boe_date")
                                    if normalized.get("boe_date") is not None
                                    else (
                                        normalized.get("boeDate")
                                        if normalized.get("boeDate") is not None
                                        else (
                                            normalized.get("filing_date")
                                            if normalized.get("filing_date") is not None
                                            else (
                                                normalized.get("filingDate")
                                                if normalized.get("filingDate") is not None
                                                else (
                                                    normalized.get("duty_paid_date")
                                                    if normalized.get("duty_paid_date") is not None
                                                    else (
                                                        normalized.get("dutyPaidDate")
                                                        if normalized.get("dutyPaidDate") is not None
                                                        else (
                                                            normalized.get("shipment_date")
                                                            if normalized.get("shipment_date") is not None
                                                            else normalized.get("shipmentDate")
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    )
    if raw_date is not None and str(raw_date).strip() != "":
        parsed_d = _parse_date(raw_date)
        if parsed_d is not None:
            normalized["date"] = parsed_d.isoformat()
            normalized["entry_date"] = parsed_d.isoformat()
    elif raw_date == "":
        normalized["date"] = None
        normalized["entry_date"] = None
    elif is_create and ("date" not in normalized or normalized["date"] is None):
        today_iso = datetime.utcnow().date().isoformat()
        normalized["date"] = today_iso
        normalized["entry_date"] = today_iso

    # Bill of entry number alias normalization
    raw_boe_no = (
        normalized.get("bill_of_entry_no")
        if normalized.get("bill_of_entry_no") is not None
        else (
            normalized.get("bill_of_entry_number")
            if normalized.get("bill_of_entry_number") is not None
            else (
                normalized.get("billOfEntryNo")
                if normalized.get("billOfEntryNo") is not None
                else (
                    normalized.get("billOfEntryNumber")
                    if normalized.get("billOfEntryNumber") is not None
                    else (
                        normalized.get("boe_no")
                        if normalized.get("boe_no") is not None
                        else (
                            normalized.get("boeNumber")
                            if normalized.get("boeNumber") is not None
                            else (
                                normalized.get("boe_filing_no")
                                if normalized.get("boe_filing_no") is not None
                                else normalized.get("boeFilingNo")
                            )
                        )
                    )
                )
            )
        )
    )
    if raw_boe_no is not None and str(raw_boe_no).strip() != "":
        normalized["bill_of_entry_no"] = str(raw_boe_no).strip()
        normalized["bill_of_entry_number"] = str(raw_boe_no).strip()
    elif raw_boe_no == "":
        normalized["bill_of_entry_no"] = None

    # Project id normalization
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
        normalized["project_id"] = None

    # Total assessable value normalization
    tav = (
        normalized.get("total_assessable_value")
        if normalized.get("total_assessable_value") is not None
        else (
            normalized.get("totalAssessableValue")
            if normalized.get("totalAssessableValue") is not None
            else (
                normalized.get("assessable_value")
                if normalized.get("assessable_value") is not None
                else normalized.get("assessableValue")
            )
        )
    )
    if tav is not None and str(tav).strip() != "":
        clean_tav = _clean_decimal(tav)
        if clean_tav is not None:
            normalized["total_assessable_value"] = clean_tav
    elif tav == "":
        normalized["total_assessable_value"] = None

    # BCD (Basic Custom Duty) normalization
    bcd_val = (
        normalized.get("bcd")
        if normalized.get("bcd") is not None
        else (
            normalized.get("basic_custom_duty_bcd")
            if normalized.get("basic_custom_duty_bcd") is not None
            else (
                normalized.get("basicCustomDutyBcd")
                if normalized.get("basicCustomDutyBcd") is not None
                else (
                    normalized.get("basic_custom_duty")
                    if normalized.get("basic_custom_duty") is not None
                    else normalized.get("basicCustomDuty")
                )
            )
        )
    )
    if bcd_val is not None and str(bcd_val).strip() != "":
        clean_bcd = _clean_decimal(bcd_val)
        if clean_bcd is not None:
            normalized["bcd"] = clean_bcd
    elif bcd_val == "":
        normalized["bcd"] = None

    # SWS (Social Welfare Surcharge) normalization
    sws_val = (
        normalized.get("sws")
        if normalized.get("sws") is not None
        else (
            normalized.get("social_welfare_surcharge")
            if normalized.get("social_welfare_surcharge") is not None
            else normalized.get("socialWelfareSurcharge")
        )
    )
    if sws_val is not None and str(sws_val).strip() != "":
        clean_sws = _clean_decimal(sws_val)
        if clean_sws is not None:
            normalized["sws"] = clean_sws
    elif sws_val == "":
        normalized["sws"] = None

    # IGST normalization
    igst_val = (
        normalized.get("igst")
        if normalized.get("igst") is not None
        else (
            normalized.get("igst_amount")
            if normalized.get("igst_amount") is not None
            else normalized.get("igstAmount")
        )
    )
    if igst_val is not None and str(igst_val).strip() != "":
        clean_igst = _clean_decimal(igst_val)
        if clean_igst is not None:
            normalized["igst"] = clean_igst
    elif igst_val == "":
        normalized["igst"] = None

    # Total duty normalization / calculation
    td_val = (
        normalized.get("total_duty")
        if normalized.get("total_duty") is not None
        else (
            normalized.get("totalDuty")
            if normalized.get("totalDuty") is not None
            else (
                normalized.get("duty")
                if normalized.get("duty") is not None
                else (
                    normalized.get("duty_amount")
                    if normalized.get("duty_amount") is not None
                    else normalized.get("dutyAmount")
                )
            )
        )
    )
    if td_val is not None and str(td_val).strip() != "":
        clean_td = _clean_decimal(td_val)
        if clean_td is not None:
            normalized["total_duty"] = clean_td
    elif td_val == "":
        normalized["total_duty"] = None
    else:
        parts = [
            normalized.get("bcd"),
            normalized.get("sws"),
            normalized.get("igst"),
        ]
        if any(p is not None for p in parts):
            total = Decimal(0)
            for p in parts:
                if p is not None:
                    try:
                        total += Decimal(str(p))
                    except Exception:
                        pass
            normalized["total_duty"] = float(total)

    # Remarks normalization
    if "remarks" in normalized and not normalized.get("remark"):
        normalized["remark"] = normalized["remarks"]
    elif "remark" in normalized and not normalized.get("remarks"):
        normalized["remarks"] = normalized["remark"]

    return normalized


class BillOfEntryCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True)
    bill_of_entry_no = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
    )
    date = fields.Date(required=True)
    total_assessable_value = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    bcd = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    sws = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    igst = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    total_duty = fields.Decimal(
        as_string=False,
        allow_none=True,
        load_default=None,
    )
    remark = fields.Raw(allow_none=True, load_default=None)
    remarks = fields.Raw(allow_none=True, load_default=None)

    # Form 27 (FORM_27_SHIPPING_CLEARANCE) fields
    logistic_mode = fields.String(required=False, allow_none=True)
    shipment_date = fields.Raw(required=False, allow_none=True)
    awb_bl_no = fields.String(required=False, allow_none=True)
    flight_vessel_name = fields.String(required=False, allow_none=True)
    flight_vessel_no = fields.String(required=False, allow_none=True)
    port_loading = fields.String(required=False, allow_none=True)
    port_discharge = fields.String(required=False, allow_none=True)
    boe_filing_date = fields.Raw(required=False, allow_none=True)
    basic_custom_duty_bcd = fields.Raw(required=False, allow_none=True)
    duty_paid_date = fields.Raw(required=False, allow_none=True)
    challan_no = fields.String(required=False, allow_none=True)
    payment_ref_no = fields.String(required=False, allow_none=True)
    customs_location = fields.String(required=False, allow_none=True)
    cfs_name = fields.String(required=False, allow_none=True)
    items = fields.List(fields.Raw(), required=False, allow_none=True, load_default=[])
    attachments_count = fields.Integer(required=False, allow_none=True)
    form_code = fields.String(required=False, allow_none=True)

    @pre_load
    def prepare_data(self, data, **kwargs):
        return _normalize_bill_of_entry_payload(data, is_create=True)


class BillOfEntryUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    bill_of_entry_no = fields.String(
        required=False,
        validate=validate.Length(min=1, max=100),
    )
    date = fields.Date(required=False)
    total_assessable_value = fields.Decimal(
        as_string=False,
        allow_none=True,
    )
    bcd = fields.Decimal(
        as_string=False,
        allow_none=True,
    )
    sws = fields.Decimal(
        as_string=False,
        allow_none=True,
    )
    igst = fields.Decimal(
        as_string=False,
        allow_none=True,
    )
    total_duty = fields.Decimal(
        as_string=False,
        allow_none=True,
    )
    remark = fields.Raw(allow_none=True)
    remarks = fields.Raw(allow_none=True)

    # Form 27 (FORM_27_SHIPPING_CLEARANCE) fields
    logistic_mode = fields.String(required=False, allow_none=True)
    shipment_date = fields.Raw(required=False, allow_none=True)
    awb_bl_no = fields.String(required=False, allow_none=True)
    flight_vessel_name = fields.String(required=False, allow_none=True)
    flight_vessel_no = fields.String(required=False, allow_none=True)
    port_loading = fields.String(required=False, allow_none=True)
    port_discharge = fields.String(required=False, allow_none=True)
    boe_filing_date = fields.Raw(required=False, allow_none=True)
    basic_custom_duty_bcd = fields.Raw(required=False, allow_none=True)
    duty_paid_date = fields.Raw(required=False, allow_none=True)
    challan_no = fields.String(required=False, allow_none=True)
    payment_ref_no = fields.String(required=False, allow_none=True)
    customs_location = fields.String(required=False, allow_none=True)
    cfs_name = fields.String(required=False, allow_none=True)
    items = fields.List(fields.Raw(), required=False, allow_none=True)
    attachments_count = fields.Integer(required=False, allow_none=True)
    form_code = fields.String(required=False, allow_none=True)

    @pre_load
    def prepare_data(self, data, **kwargs):
        return _normalize_bill_of_entry_payload(data, is_create=False)


class BillOfEntryQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, allow_none=True)


class BillOfEntryResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    bill_of_entry_no = fields.String(required=True)
    bill_of_entry_number = fields.String(allow_none=True)
    boe_no = fields.String(allow_none=True)
    date = fields.Date(required=True)
    entry_date = fields.Date(allow_none=True)
    boe_filing_date = fields.Date(allow_none=True)
    boe_date = fields.Date(allow_none=True)
    total_assessable_value = fields.Raw(allow_none=True)
    bcd = fields.Raw(allow_none=True)
    basic_custom_duty_bcd = fields.Raw(allow_none=True)
    sws = fields.Raw(allow_none=True)
    igst = fields.Raw(allow_none=True)
    total_duty = fields.Raw(allow_none=True)
    duty = fields.Raw(allow_none=True)
    duty_amount = fields.Raw(allow_none=True)
    items = fields.List(fields.Raw(), dump_default=[])
    form_code = fields.String(dump_default="FORM_27_SHIPPING_CLEARANCE")
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)

    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_default=[],
    )


class LatestBillOfEntryQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        resolved_id = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("projectId")
        )
        if resolved_id is not None and str(resolved_id).strip() != "":
            normalized["project_id"] = str(resolved_id).strip()
        return normalized


class LatestBillOfEntryResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    bill_of_entry_no = fields.String(allow_none=True)
    date = fields.Date(allow_none=True)
    bcd = fields.Float(allow_none=True)
    sws = fields.Float(allow_none=True)
    igst = fields.Float(allow_none=True)
    duty = fields.Float(allow_none=True)

