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
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        raise ValidationError(f"Invalid date format: {val}. Expected YYYY-MM-DD.")


def _normalize_import_logistics_payload(raw_data):
    if not isinstance(raw_data, Mapping):
        return raw_data
    normalized = dict(raw_data)

    # Date normalization
    if "date" in normalized:
        d = _parse_date(normalized["date"])
        if d is not None:
            normalized["date"] = d.isoformat()
    elif "logistics_date" in normalized:
        d = _parse_date(normalized["logistics_date"])
        if d is not None:
            normalized["date"] = d.isoformat()

    # Logistic type normalization
    if "logistic_type" in normalized and isinstance(normalized["logistic_type"], str):
        normalized["logistic_type"] = normalized["logistic_type"].strip().lower()

    # Air fields aliases
    if "airway_bill_number" in normalized and "airway_bill_no" not in normalized:
        normalized["airway_bill_no"] = normalized["airway_bill_number"]
    if "flight_number" in normalized and "flight_no" not in normalized:
        normalized["flight_no"] = normalized["flight_number"]

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
    ):
        if k in normalized and isinstance(normalized[k], str):
            normalized[k] = normalized[k].strip()

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
    remark = fields.String(allow_none=True, load_default=None)

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
    remark = fields.String(allow_none=True)

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

    @pre_load
    def prepare_data(self, data, **kwargs):
        return _normalize_import_logistics_payload(data)


class ImportLogisticsQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, allow_none=True)
    supplier_id = fields.Integer(required=False, allow_none=True)
    logistic_type = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["air", "sea"]),
    )


class ImportLogisticsResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(allow_none=True)
    logistic_type = fields.String(required=True)
    date = fields.Date(required=True)
    port_of_discharge = fields.String(allow_none=True)
    remark = fields.String(allow_none=True)

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

    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)

    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_default=[],
    )

