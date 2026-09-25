import datetime
from flask.json.provider import DefaultJSONProvider
import marshmallow.fields


DATE_RESPONSE_FORMAT = "%d-%m-%Y"
DATE_INPUT_FORMATS = (
    "%d-%m-%Y",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%Y/%m/%d",
)


def format_date_response(val):
    if val is None or val == "":
        return None
    if isinstance(val, datetime.datetime):
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
    _marshmallow_date_configured = True
