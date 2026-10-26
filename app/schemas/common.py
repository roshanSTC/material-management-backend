from datetime import date, datetime
from marshmallow import ValidationError, fields


class FlexibleDate(fields.Field):
    """
    Parses dates from:
    - ISO datetime strings with time/timezone (e.g. "2026-10-25T18:30:00.000Z")
    - ISO date strings (e.g. "2026-10-25")
    - Local formats (e.g. "25-10-2026", "25/10/2026", "2026/10/25")
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

