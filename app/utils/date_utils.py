import datetime
from flask.json.provider import DefaultJSONProvider
import marshmallow.fields


IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
DATE_RESPONSE_FORMAT = "%d-%m-%Y"
DATE_INPUT_FORMATS = (
    "%d-%m-%Y",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%Y/%m/%d",
)


def to_ist(val):
    if val is None or val == "":
        return None
    if isinstance(val, datetime.datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=datetime.timezone.utc)
        return val.astimezone(IST)
    if isinstance(val, str):
        try:
            dt = datetime.datetime.fromisoformat(val.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt.astimezone(IST)
        except Exception:
            return val
    return val


def format_date_response(val):
    if val is None or val == "":
        return None
    if isinstance(val, datetime.datetime):
        val = to_ist(val)
        return val.strftime(DATE_RESPONSE_FORMAT)
    if isinstance(val, datetime.date):
        return val.strftime(DATE_RESPONSE_FORMAT)
    if isinstance(val, str):
        val_str = val.strip()
        for fmt in DATE_INPUT_FORMATS:
            try:
                dt = datetime.datetime.strptime(val_str, fmt)
                return dt.strftime(DATE_RESPONSE_FORMAT)
            except ValueError:
                pass
        return val
    return val


def parse_date_input(val):
    if val is None or val == "":
        return None
    if isinstance(val, datetime.date) and not isinstance(val, datetime.datetime):
        return val
    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, str):
        val_str = val.strip()
        for fmt in DATE_INPUT_FORMATS:
            try:
                dt = datetime.datetime.strptime(val_str, fmt)
                return dt.date()
            except ValueError:
                pass
        raise ValueError(f"Cannot parse date '{val}'. Expected DD-MM-YYYY or YYYY-MM-DD.")
    raise ValueError(f"Cannot parse date of type {type(val).__name__}.")


class CustomJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, datetime.date) and not isinstance(o, datetime.datetime):
            return o.strftime(DATE_RESPONSE_FORMAT)
        if isinstance(o, datetime.datetime):
            if o.tzinfo is None:
                o = o.replace(tzinfo=datetime.timezone.utc)
            return o.astimezone(IST).isoformat()
        return super().default(o)


_marshmallow_date_configured = False


def configure_marshmallow_date_format():
    global _marshmallow_date_configured
    if _marshmallow_date_configured:
        return

    orig_serialize = marshmallow.fields.Date._serialize
    orig_deserialize = marshmallow.fields.Date._deserialize

    def _custom_serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        if isinstance(value, datetime.date):
            return value.strftime(DATE_RESPONSE_FORMAT)
        return orig_serialize(self, value, attr, obj, **kwargs)

    def _custom_deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        if isinstance(value, datetime.date):
            return value
        if isinstance(value, str):
            val_str = value.strip()
            for fmt in DATE_INPUT_FORMATS:
                try:
                    return datetime.datetime.strptime(val_str, fmt).date()
                except ValueError:
                    pass
        return orig_deserialize(self, value, attr, data, **kwargs)

    marshmallow.fields.Date._serialize = _custom_serialize
    marshmallow.fields.Date._deserialize = _custom_deserialize

    orig_dt_serialize = marshmallow.fields.DateTime._serialize

    def _custom_dt_serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        if isinstance(value, datetime.datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=datetime.timezone.utc)
            value = value.astimezone(IST)
        elif isinstance(value, str):
            try:
                dt = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                value = dt.astimezone(IST)
            except Exception:
                pass
        return orig_dt_serialize(self, value, attr, obj, **kwargs)

    marshmallow.fields.DateTime._serialize = _custom_dt_serialize

    _marshmallow_date_configured = True
