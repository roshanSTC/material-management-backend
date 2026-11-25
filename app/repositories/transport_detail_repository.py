import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select

from app.extensions.database import db
from app.models import Project, TransportDetail


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_transport_detail(transport_detail_id: int) -> TransportDetail | None:
    return db.session.get(TransportDetail, transport_detail_id)


def get_transport_detail_by_project_id(project_id: int) -> TransportDetail | None:
    stmt = (
        select(TransportDetail)
        .where(TransportDetail.project_id == project_id)
        .order_by(TransportDetail.id.desc())
    )
    return db.session.execute(stmt).scalars().first()


def list_transport_details(
    project_id: int | None = None,
    transportation_mode: str | None = None,
    lr_rr_awb_no: str | None = None,
) -> list[TransportDetail]:
    stmt = select(TransportDetail).order_by(TransportDetail.id.desc())

    if project_id is not None:
        stmt = stmt.where(TransportDetail.project_id == project_id)
    if transportation_mode is not None:
        stmt = stmt.where(TransportDetail.transportation_mode == transportation_mode.lower())
    if lr_rr_awb_no is not None:
        stmt = stmt.where(TransportDetail.lr_rr_awb_no == lr_rr_awb_no)

    return list(db.session.execute(stmt).scalars().all())


from app.utils.remark_utils import normalize_remark_for_db


def _normalize_optional_string(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return normalize_remark_for_db(value)
    cleaned = str(value).strip()
    return cleaned if cleaned else None


def _parse_date_val(val) -> date | None:
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    if not s:
        return None
    if "T" in s:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    return date.fromisoformat(s[:10])


def _parse_decimal_val(val) -> Decimal | None:
    if val is None:
        return None
    if isinstance(val, (int, float, Decimal)):
        return Decimal(str(val))
    s = str(val).strip()
    if not s:
        return None
    match = re.search(r"[-+]?(?:\d*\.\d+|\d+)", s)
    if not match:
        return None
    return Decimal(match.group(0))


def create_transport_detail(*, data: dict) -> TransportDetail:
    detail_date = _parse_date_val(data.get("lr_rr_awb_date"))
    charges = _parse_decimal_val(data.get("total_transportation_charges"))
    mode_val = str(data.get("transportation_mode") or "").strip().lower()
    lr_val = _normalize_optional_string(data.get("lr_rr_awb_no"))
    from_loc = str(data.get("from_location", "")).strip()
    to_loc = str(data.get("to_location", "")).strip()
    remark_val = _normalize_optional_string(
        data.get("remark") or data.get("remarks")
    )

    detail = TransportDetail(
        project_id=data["project_id"],
        transportation_mode=mode_val,
        lr_rr_awb_no=lr_val,
        lr_rr_awb_date=detail_date,
        from_location=from_loc,
        to_location=to_loc,
        total_transportation_charges=charges,
        remark=remark_val,
    )
    db.session.add(detail)
    db.session.flush()
    return detail


def update_transport_detail(
    detail: TransportDetail,
    data: dict,
) -> TransportDetail:
    if "project_id" in data:
        detail.project_id = data["project_id"]

    if "transportation_mode" in data and data["transportation_mode"] is not None:
        detail.transportation_mode = str(data["transportation_mode"]).strip().lower()

    if "lr_rr_awb_date" in data:
        dt = _parse_date_val(data["lr_rr_awb_date"])
        if dt is not None:
            detail.lr_rr_awb_date = dt

    if "lr_rr_awb_no" in data:
        detail.lr_rr_awb_no = _normalize_optional_string(data["lr_rr_awb_no"])

    if "from_location" in data and data["from_location"] is not None:
        detail.from_location = str(data["from_location"]).strip()

    if "to_location" in data and data["to_location"] is not None:
        detail.to_location = str(data["to_location"]).strip()

    if "total_transportation_charges" in data:
        detail.total_transportation_charges = _parse_decimal_val(data["total_transportation_charges"])

    if "remark" in data or "remarks" in data:
        detail.remark = _normalize_optional_string(
            data.get("remark") or data.get("remarks")
        )

    detail.updated_at = datetime.utcnow()
    db.session.flush()
    return detail


def delete_transport_detail(transport_detail_id: int) -> list[str]:
    detail = get_transport_detail(transport_detail_id)
    if detail is None:
        return []

    from app.models import Attachment

    attachments = Attachment.query.filter_by(
        entity_type="transport_detail",
        entity_id=transport_detail_id,
    ).all()

    storage_keys = []
    for att in attachments:
        if att.storage_key:
            storage_keys.append(att.storage_key)
        db.session.delete(att)

    db.session.delete(detail)
    db.session.flush()
    return storage_keys
