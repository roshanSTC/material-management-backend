from datetime import date, datetime
from marshmallow import EXCLUDE, Schema, ValidationError, fields


# =========================================================================
# FLEXIBLE INPUT FIELDS (Handles ISO timestamps, strings, empty values)
# =========================================================================
class FlexibleDate(fields.Field):
    """
    Parses dates from:
    - ISO datetime strings with time/timezone (e.g. "2026-10-26T10:00:00.000Z")
    - ISO date strings (e.g. "2026-10-26")
    - Local formats (e.g. "26-10-2026", "26/10/2026", "2026/10/26")
    - Empty strings or None -> returns None
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("allow_none", True)
        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        if isinstance(value, (datetime, date)):
            return value if isinstance(value, date) else value.date()
        if isinstance(value, str):
            s = value.strip()
            if "T" in s:
                s = s.split("T")[0]
            elif " " in s:
                s = s.split(" ")[0]
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(s, fmt).date()
                except ValueError:
                    pass
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return dt.date()
            except Exception:
                raise ValidationError("Not a valid date.")
        raise ValidationError("Not a valid date.")


class FlexibleDateTime(fields.Field):
    """
    Parses datetimes from ISO strings, with or without 'Z', or date strings.
    Empty strings or None -> returns None.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("allow_none", True)
        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        if isinstance(value, str):
            s = value.strip()
            s_clean = s.replace("Z", "")
            for fmt in (
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%d-%m-%Y",
                "%d/%m/%Y",
            ):
                try:
                    return datetime.strptime(s_clean, fmt)
                except ValueError:
                    pass
            try:
                return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                raise ValidationError("Not a valid datetime.")
        raise ValidationError("Not a valid datetime.")


class FlexibleFloat(fields.Field):
    """
    Parses floats from numbers or strings, strips commas, handles empty strings as None.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("allow_none", True)
        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                cleaned = value.replace(",", "").strip()
                if not cleaned:
                    return None
                return float(cleaned)
            except (ValueError, TypeError):
                raise ValidationError("Not a valid number.")
        raise ValidationError("Not a valid number.")


class FlexibleInt(fields.Field):
    """
    Parses integers from numbers or strings, strips commas, handles empty strings as None.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("allow_none", True)
        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, (float, str)):
            try:
                cleaned = str(value).replace(",", "").strip()
                if not cleaned:
                    return None
                return int(float(cleaned))
            except (ValueError, TypeError):
                raise ValidationError("Not a valid integer.")
        raise ValidationError("Not a valid integer.")


class BasePhase1Schema(Schema):
    class Meta:
        unknown = EXCLUDE


# =========================================================================
# 1. PRE-QUALIFICATION BID (FORM_01_PQB)
# =========================================================================
class PreQualificationBidItemSchema(BasePhase1Schema):
    id = fields.Int(dump_only=True)
    sr_no = FlexibleInt(allow_none=True)
    description = fields.Str(required=False, allow_none=True)
    material_name = fields.Str(required=False, allow_none=True)
    unit = fields.Str(allow_none=True)
    quantity = FlexibleFloat(allow_none=True)
    specifications = fields.Str(allow_none=True)


class PreQualificationBidCreateSchema(BasePhase1Schema):
    project_id = FlexibleInt(required=True)
    pqb_title = fields.Str(allow_none=True)
    pqb_no = fields.Str(required=False, allow_none=True)
    bid_number = fields.Str(required=False, allow_none=True)
    tender_name = fields.Str(required=False, allow_none=True)
    authority_name = fields.Str(required=False, allow_none=True)
    submission_deadline = FlexibleDateTime(required=False, allow_none=True)
    supply_locations = fields.Raw(required=False, allow_none=True)
    pqb_issuing_date = FlexibleDate(allow_none=True)
    pqb_closing_date_time = FlexibleDateTime(allow_none=True)
    pqb_opening_date_time = FlexibleDateTime(allow_none=True)
    mode_of_bid_submission = fields.Str(allow_none=True)
    supply_location = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    items = fields.List(fields.Nested(PreQualificationBidItemSchema), allow_none=True)
    requirements = fields.List(fields.Nested(PreQualificationBidItemSchema), allow_none=True)


class PreQualificationBidUpdateSchema(BasePhase1Schema):
    pqb_title = fields.Str(allow_none=True)
    pqb_no = fields.Str(allow_none=True)
    bid_number = fields.Str(allow_none=True)
    tender_name = fields.Str(allow_none=True)
    pqb_issuing_date = FlexibleDate(allow_none=True)
    pqb_closing_date_time = FlexibleDateTime(allow_none=True)
    pqb_opening_date_time = FlexibleDateTime(allow_none=True)
    mode_of_bid_submission = fields.Str(allow_none=True)
    supply_location = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    items = fields.List(fields.Nested(PreQualificationBidItemSchema), allow_none=True)
    requirements = fields.List(fields.Nested(PreQualificationBidItemSchema), allow_none=True)


# =========================================================================
# 2. BID DOCUMENT FOR PQB (FORM_02_PQB_BID_DOCUMENT)
# =========================================================================
class PqbBidDocumentItemSchema(BasePhase1Schema):
    id = fields.Int(dump_only=True)
    sr_no = FlexibleInt(allow_none=True)
    description = fields.Str(allow_none=True)
    material_name = fields.Str(allow_none=True)
    hsn_sac = fields.Str(allow_none=True)
    quantity = FlexibleFloat(allow_none=True)
    unit_price = FlexibleFloat(allow_none=True)
    total_amount = FlexibleFloat(allow_none=True)


class PqbBidDocumentCreateSchema(BasePhase1Schema):
    project_id = FlexibleInt(required=True)
    pqb_title = fields.Str(allow_none=True)
    pqb_no = fields.Str(required=True)
    pqb_issue_date = FlexibleDate(allow_none=True)
    pqb_closing_date_time = FlexibleDateTime(allow_none=True)
    pqb_opening_date_time = FlexibleDateTime(allow_none=True)
    total_corrigendum_issued = FlexibleInt(allow_none=True)
    total_no_corrigendum_issued = FlexibleInt(allow_none=True)
    status = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    items = fields.List(fields.Nested(PqbBidDocumentItemSchema), allow_none=True)
    form_code = fields.Str(allow_none=True)
    attachments_count = FlexibleInt(allow_none=True)


class PqbBidDocumentUpdateSchema(BasePhase1Schema):
    pqb_title = fields.Str(allow_none=True)
    pqb_no = fields.Str(allow_none=True)
    pqb_issue_date = FlexibleDate(allow_none=True)
    pqb_closing_date_time = FlexibleDateTime(allow_none=True)
    pqb_opening_date_time = FlexibleDateTime(allow_none=True)
    total_corrigendum_issued = FlexibleInt(allow_none=True)
    total_no_corrigendum_issued = FlexibleInt(allow_none=True)
    status = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    items = fields.List(fields.Nested(PqbBidDocumentItemSchema), allow_none=True)
    form_code = fields.Str(allow_none=True)
    attachments_count = FlexibleInt(allow_none=True)


# =========================================================================
# 3. CORRIGENDUM (FORM_03_CORRIGENDUM)
# =========================================================================
class CorrigendumCreateSchema(BasePhase1Schema):
    project_id = FlexibleInt(required=True)
    corrigendum_no = fields.Str(required=True)
    against_tender_no = fields.Str(allow_none=True)
    tender_title = fields.Str(allow_none=True)
    issue_date = FlexibleDate(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)


class CorrigendumUpdateSchema(BasePhase1Schema):
    corrigendum_no = fields.Str(allow_none=True)
    against_tender_no = fields.Str(allow_none=True)
    tender_title = fields.Str(allow_none=True)
    issue_date = FlexibleDate(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)


# =========================================================================
# 4. LIMITED TENDER ENQUIRY (FORM_04_LTE)
# =========================================================================
class LimitedTenderEnquiryItemSchema(BasePhase1Schema):
    id = fields.Int(dump_only=True)
    sr_no = FlexibleInt(allow_none=True)
    description = fields.Str(required=False, allow_none=True)
    material_name = fields.Str(required=False, allow_none=True)
    unit = fields.Str(allow_none=True)
    quantity = FlexibleFloat(allow_none=True)


class LimitedTenderEnquiryCreateSchema(BasePhase1Schema):
    project_id = FlexibleInt(required=True)
    pqb_no = fields.Str(allow_none=True)
    tender_title = fields.Str(allow_none=True)
    tender_enquiry_no = fields.Str(required=True)
    tender_issue_date = FlexibleDate(allow_none=True)
    bid_submission_due_date_time = FlexibleDateTime(allow_none=True)
    bid_opening_date_time = FlexibleDateTime(allow_none=True)
    tender_fee = FlexibleFloat(allow_none=True)
    emd = FlexibleFloat(allow_none=True)
    tender_validity = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    items = fields.List(fields.Nested(LimitedTenderEnquiryItemSchema), allow_none=True)
    requirements = fields.List(fields.Nested(LimitedTenderEnquiryItemSchema), allow_none=True)


class LimitedTenderEnquiryUpdateSchema(BasePhase1Schema):
    pqb_no = fields.Str(allow_none=True)
    tender_title = fields.Str(allow_none=True)
    tender_enquiry_no = fields.Str(allow_none=True)
    tender_issue_date = FlexibleDate(allow_none=True)
    bid_submission_due_date_time = FlexibleDateTime(allow_none=True)
    bid_opening_date_time = FlexibleDateTime(allow_none=True)
    tender_fee = FlexibleFloat(allow_none=True)
    emd = FlexibleFloat(allow_none=True)
    tender_validity = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    items = fields.List(fields.Nested(LimitedTenderEnquiryItemSchema), allow_none=True)
    requirements = fields.List(fields.Nested(LimitedTenderEnquiryItemSchema), allow_none=True)


# =========================================================================
# 5. NOTIFICATION OF AWARD OF CONTRACT (FORM_05_NAC)
# =========================================================================
class NotificationAwardItemSchema(BasePhase1Schema):
    id = fields.Int(dump_only=True)
    sr_no = FlexibleInt(allow_none=True)
    description = fields.Str(required=False, allow_none=True)
    material_name = fields.Str(required=False, allow_none=True)
    quantity = FlexibleFloat(allow_none=True)
    per_unit_price = FlexibleFloat(allow_none=True)
    total_amount = FlexibleFloat(allow_none=True)


class NotificationAwardCreateSchema(BasePhase1Schema):
    project_id = FlexibleInt(required=True)
    nac_no = fields.Str(required=True)
    nac_date = FlexibleDate(allow_none=True)
    nac_title = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    items = fields.List(fields.Nested(NotificationAwardItemSchema), allow_none=True)
    awarded_materials = fields.List(fields.Nested(NotificationAwardItemSchema), allow_none=True)


class NotificationAwardUpdateSchema(BasePhase1Schema):
    nac_no = fields.Str(allow_none=True)
    nac_date = FlexibleDate(allow_none=True)
    nac_title = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    items = fields.List(fields.Nested(NotificationAwardItemSchema), allow_none=True)
    awarded_materials = fields.List(fields.Nested(NotificationAwardItemSchema), allow_none=True)


# =========================================================================
# 6. CONSULTANCY INVOICE (FORM_06_CONSULTANCY_INVOICE)
# =========================================================================
class ConsultancyInvoiceCreateSchema(BasePhase1Schema):
    project_id = FlexibleInt(required=True)
    invoice_no = fields.Str(required=True)
    invoice_date = FlexibleDate(allow_none=True)
    party_name = fields.Str(allow_none=True)
    invoice_reference = fields.Str(allow_none=True)
    total_value_eur = FlexibleFloat(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)


class ConsultancyInvoiceUpdateSchema(BasePhase1Schema):
    invoice_no = fields.Str(allow_none=True)
    invoice_date = FlexibleDate(allow_none=True)
    party_name = fields.Str(allow_none=True)
    invoice_reference = fields.Str(allow_none=True)
    total_value_eur = FlexibleFloat(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)


# =========================================================================
# 7. EXPRESSION OF INTEREST (FORM_07_EOI)
# =========================================================================
class ExpressionOfInterestItemSchema(BasePhase1Schema):
    id = fields.Int(dump_only=True)
    sr_no = FlexibleInt(allow_none=True)
    description = fields.Str(required=False, allow_none=True)
    material_name = fields.Str(required=False, allow_none=True)
    unit = fields.Str(allow_none=True)
    quantity = FlexibleFloat(allow_none=True)


class ExpressionOfInterestCreateSchema(BasePhase1Schema):
    project_id = FlexibleInt(required=True)
    eoi_title = fields.Str(allow_none=True)
    eoi_no = fields.Str(required=True)
    eoi_date = FlexibleDate(allow_none=True)
    eoi_closing_date_time = FlexibleDateTime(allow_none=True)
    eoi_opening_date_time = FlexibleDateTime(allow_none=True)
    mode_of_submission = fields.Str(allow_none=True)
    supply_location = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    items = fields.List(fields.Nested(ExpressionOfInterestItemSchema), allow_none=True)
    requirements = fields.List(fields.Nested(ExpressionOfInterestItemSchema), allow_none=True)


class ExpressionOfInterestUpdateSchema(BasePhase1Schema):
    eoi_title = fields.Str(allow_none=True)
    eoi_no = fields.Str(allow_none=True)
    eoi_date = FlexibleDate(allow_none=True)
    eoi_closing_date_time = FlexibleDateTime(allow_none=True)
    eoi_opening_date_time = FlexibleDateTime(allow_none=True)
    mode_of_submission = fields.Str(allow_none=True)
    supply_location = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    items = fields.List(fields.Nested(ExpressionOfInterestItemSchema), allow_none=True)
    requirements = fields.List(fields.Nested(ExpressionOfInterestItemSchema), allow_none=True)


# =========================================================================
# 8. BID DOCUMENT TECHNO-COMMERCIAL (FORM_29_BID_DOC_TECHNO_COMMERCIAL)
# =========================================================================
class BidDocumentTechnoCommercialItemSchema(BasePhase1Schema):
    id = fields.Int(dump_only=True)
    sr_no = FlexibleInt(allow_none=True)
    description = fields.Str(allow_none=True)
    material_name = fields.Str(allow_none=True)
    hsn_sac = fields.Str(allow_none=True)
    quantity = FlexibleFloat(allow_none=True)
    unit_price = FlexibleFloat(allow_none=True)
    total_amount = FlexibleFloat(allow_none=True)


class BidDocumentTechnoCommercialCreateSchema(BasePhase1Schema):
    project_id = FlexibleInt(required=True)
    customer_name = fields.Str(allow_none=True)
    tender_title = fields.Str(allow_none=True)
    tender_no = fields.Str(allow_none=True)
    tender_number = fields.Str(allow_none=True)
    tender_issue_date = FlexibleDate(allow_none=True)
    total_no_corrigendum_issued = FlexibleInt(allow_none=True)
    total_corrigendum_issued = FlexibleInt(allow_none=True)
    bid_submission_date = FlexibleDate(allow_none=True)
    delivery_terms = fields.Str(allow_none=True)
    delivery_period = fields.Str(allow_none=True)
    bid_validity = fields.Str(allow_none=True)
    payment_terms = fields.Str(allow_none=True)
    warranty_period = fields.Str(allow_none=True)
    gst_pct = FlexibleFloat(allow_none=True)
    gst_rate = FlexibleFloat(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    status = fields.Str(allow_none=True)
    form_code = fields.Str(allow_none=True)
    attachments_count = FlexibleInt(allow_none=True)
    items = fields.List(fields.Nested(BidDocumentTechnoCommercialItemSchema), allow_none=True)


class BidDocumentTechnoCommercialUpdateSchema(BasePhase1Schema):
    customer_name = fields.Str(allow_none=True)
    tender_title = fields.Str(allow_none=True)
    tender_no = fields.Str(allow_none=True)
    tender_number = fields.Str(allow_none=True)
    tender_issue_date = FlexibleDate(allow_none=True)
    total_no_corrigendum_issued = FlexibleInt(allow_none=True)
    total_corrigendum_issued = FlexibleInt(allow_none=True)
    bid_submission_date = FlexibleDate(allow_none=True)
    delivery_terms = fields.Str(allow_none=True)
    delivery_period = fields.Str(allow_none=True)
    bid_validity = fields.Str(allow_none=True)
    payment_terms = fields.Str(allow_none=True)
    warranty_period = fields.Str(allow_none=True)
    gst_pct = FlexibleFloat(allow_none=True)
    gst_rate = FlexibleFloat(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    status = fields.Str(allow_none=True)
    form_code = fields.Str(allow_none=True)
    attachments_count = FlexibleInt(allow_none=True)
    items = fields.List(fields.Nested(BidDocumentTechnoCommercialItemSchema), allow_none=True)


# =========================================================================
# 9. TECHNO-COMMERCIAL TENDER (FORM_30_TECHNO_COMMERCIAL_TENDER)
# =========================================================================
class TechnoCommercialTenderItemSchema(BasePhase1Schema):
    id = fields.Int(dump_only=True)
    sr_no = FlexibleInt(allow_none=True)
    description = fields.Str(allow_none=True)
    material_name = fields.Str(allow_none=True)
    unit = fields.Str(allow_none=True)
    quantity = FlexibleFloat(allow_none=True)


class TechnoCommercialTenderCreateSchema(BasePhase1Schema):
    project_id = FlexibleInt(required=True)
    pqb_no = fields.Str(allow_none=True)
    tender_title = fields.Str(allow_none=True)
    tender_no = fields.Str(allow_none=True)
    tender_number = fields.Str(allow_none=True)
    tender_enquiry_no = fields.Str(allow_none=True)
    tender_issue_date = FlexibleDate(allow_none=True)
    bid_submission_due_date_time = FlexibleDateTime(allow_none=True)
    bid_opening_date_time = FlexibleDateTime(allow_none=True)
    tender_fee = FlexibleFloat(allow_none=True)
    emd = FlexibleFloat(allow_none=True)
    tender_validity = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    status = fields.Str(allow_none=True)
    form_code = fields.Str(allow_none=True)
    attachments_count = FlexibleInt(allow_none=True)
    items = fields.List(fields.Nested(TechnoCommercialTenderItemSchema), allow_none=True)


class TechnoCommercialTenderUpdateSchema(BasePhase1Schema):
    pqb_no = fields.Str(allow_none=True)
    tender_title = fields.Str(allow_none=True)
    tender_no = fields.Str(allow_none=True)
    tender_number = fields.Str(allow_none=True)
    tender_enquiry_no = fields.Str(allow_none=True)
    tender_issue_date = FlexibleDate(allow_none=True)
    bid_submission_due_date_time = FlexibleDateTime(allow_none=True)
    bid_opening_date_time = FlexibleDateTime(allow_none=True)
    tender_fee = FlexibleFloat(allow_none=True)
    emd = FlexibleFloat(allow_none=True)
    tender_validity = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    status = fields.Str(allow_none=True)
    form_code = fields.Str(allow_none=True)
    attachments_count = FlexibleInt(allow_none=True)
    items = fields.List(fields.Nested(TechnoCommercialTenderItemSchema), allow_none=True)


# =========================================================================
# 10. BID DOCUMENT LTE (FORM_31_BID_DOC_LTE)
# =========================================================================
class BidDocumentLteItemSchema(BasePhase1Schema):
    id = fields.Int(dump_only=True)
    sr_no = FlexibleInt(allow_none=True)
    description = fields.Str(allow_none=True)
    material_name = fields.Str(allow_none=True)
    hsn_sac = fields.Str(allow_none=True)
    quantity = FlexibleFloat(allow_none=True)
    unit_price = FlexibleFloat(allow_none=True)
    total_amount = FlexibleFloat(allow_none=True)


class BidDocumentLteCreateSchema(BasePhase1Schema):
    project_id = FlexibleInt(required=True)
    customer_name = fields.Str(allow_none=True)
    tender_title = fields.Str(allow_none=True)
    tender_no = fields.Str(allow_none=True)
    tender_number = fields.Str(allow_none=True)
    tender_issue_date = FlexibleDate(allow_none=True)
    total_no_corrigendum_issued = FlexibleInt(allow_none=True)
    total_corrigendum_issued = FlexibleInt(allow_none=True)
    bid_submission_date = FlexibleDate(allow_none=True)
    delivery_terms = fields.Str(allow_none=True)
    delivery_period = fields.Str(allow_none=True)
    bid_validity = fields.Str(allow_none=True)
    payment_terms = fields.Str(allow_none=True)
    warranty_period = fields.Str(allow_none=True)
    gst_pct = FlexibleFloat(allow_none=True)
    gst_rate = FlexibleFloat(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    status = fields.Str(allow_none=True)
    form_code = fields.Str(allow_none=True)
    attachments_count = FlexibleInt(allow_none=True)
    items = fields.List(fields.Nested(BidDocumentLteItemSchema), allow_none=True)


class BidDocumentLteUpdateSchema(BasePhase1Schema):
    customer_name = fields.Str(allow_none=True)
    tender_title = fields.Str(allow_none=True)
    tender_no = fields.Str(allow_none=True)
    tender_number = fields.Str(allow_none=True)
    tender_issue_date = FlexibleDate(allow_none=True)
    total_no_corrigendum_issued = FlexibleInt(allow_none=True)
    total_corrigendum_issued = FlexibleInt(allow_none=True)
    bid_submission_date = FlexibleDate(allow_none=True)
    delivery_terms = fields.Str(allow_none=True)
    delivery_period = fields.Str(allow_none=True)
    bid_validity = fields.Str(allow_none=True)
    payment_terms = fields.Str(allow_none=True)
    warranty_period = fields.Str(allow_none=True)
    gst_pct = FlexibleFloat(allow_none=True)
    gst_rate = FlexibleFloat(allow_none=True)
    remark = fields.Str(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    status = fields.Str(allow_none=True)
    form_code = fields.Str(allow_none=True)
    attachments_count = FlexibleInt(allow_none=True)
    items = fields.List(fields.Nested(BidDocumentLteItemSchema), allow_none=True)
