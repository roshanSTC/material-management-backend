import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models import BidSubmission, BidSubmissionItem, CustomerTender, Project


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_customer_tender(tender_id: int) -> CustomerTender | None:
    return db.session.get(CustomerTender, tender_id)


def get_latest_customer_tender_for_project(project_id: int) -> CustomerTender | None:
    return (
        db.session.execute(
            db.select(CustomerTender)
            .where(CustomerTender.project_id == project_id)
            .order_by(CustomerTender.id.desc())
        )
        .scalars()
        .first()
    )


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned if cleaned else None


def _parse_datetime_val(val) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime.combine(val, datetime.min.time())
    s = str(val).strip()
    if not s:
        return None
    if "T" in s:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    return datetime.fromisoformat(s)


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


def _replace_items(bid_submission: BidSubmission, items: list[dict]) -> None:
    bid_submission.items.clear()
    for item in items:
        desc = (
            item.get("description")
            or item.get("material_name")
            or ""
        )
        quantity_val = _parse_decimal_val(item.get("quantity")) or Decimal("1")
        unit_price_val = _parse_decimal_val(item.get("unit_price"))
        net_total_val = _parse_decimal_val(
            item.get("net_total") or item.get("net_amount")
        )
        total_val = _parse_decimal_val(
            item.get("total") or item.get("total_amount")
        )
        hsn_sac_val = _normalize_optional_string(item.get("hsn_sac"))

        sub_item = BidSubmissionItem(
            description=desc,
            hsn_sac=hsn_sac_val,
            unit_price=unit_price_val,
            quantity=quantity_val,
            net_total=net_total_val,
            total=total_val,
        )
        bid_submission.items.append(sub_item)


def create_bid_submission(*, data: dict) -> BidSubmission:
    submission = BidSubmission(
        project_id=data["project_id"],
        tender_id=data.get("tender_id"),
        tender_title=_normalize_optional_string(
            data.get("tender_title") or data.get("tender_name")
        ),
        submission_date=_parse_datetime_val(data.get("submission_date")),
        tender_number=str(
            data.get("tender_number") or data.get("submission_number") or ""
        ).strip(),
        delivery_term=_normalize_optional_string(
            data.get("delivery_term") or data.get("delivery_terms")
        ),
        period=_normalize_optional_string(data.get("period")),
        payment_term=_normalize_optional_string(
            data.get("payment_term") or data.get("payment_terms")
        ),
        validity=_normalize_optional_string(data.get("validity")),
        warranty_period=_normalize_optional_string(data.get("warranty_period")),
        gst_rate=_parse_decimal_val(data.get("gst_rate")),
        remark=_normalize_optional_string(
            data.get("remark") or data.get("remarks")
        ),
    )

    if "items" in data and data["items"]:
        _replace_items(submission, data["items"])

    db.session.add(submission)
    db.session.flush()
    return submission


def get_bid_submission(bid_submission_id: int) -> BidSubmission | None:
    return db.session.execute(
        db.select(BidSubmission)
        .options(selectinload(BidSubmission.items))
        .where(BidSubmission.id == bid_submission_id)
    ).scalar_one_or_none()


def list_bid_submissions(
    *,
    project_id: int | None = None,
) -> list[BidSubmission]:
    statement = db.select(BidSubmission).options(
        selectinload(BidSubmission.items)
    )
    if project_id is not None:
        statement = statement.where(BidSubmission.project_id == project_id)

    return db.session.execute(
        statement.order_by(BidSubmission.id.desc())
    ).scalars().all()


def update_bid_submission(
    bid_submission: BidSubmission,
    *,
    data: dict,
) -> BidSubmission:
    if "project_id" in data:
        bid_submission.project_id = data["project_id"]
    if "tender_id" in data:
        bid_submission.tender_id = data["tender_id"]
    if "tender_title" in data or "tender_name" in data:
        bid_submission.tender_title = _normalize_optional_string(
            data.get("tender_title") or data.get("tender_name")
        )
    if "submission_date" in data:
        bid_submission.submission_date = _parse_datetime_val(data["submission_date"])
    if "tender_number" in data or "submission_number" in data:
        num_val = data.get("tender_number") or data.get("submission_number")
        if num_val is not None:
            bid_submission.tender_number = str(num_val).strip()
    if "delivery_term" in data or "delivery_terms" in data:
        bid_submission.delivery_term = _normalize_optional_string(
            data.get("delivery_term") or data.get("delivery_terms")
        )
    if "period" in data:
        bid_submission.period = _normalize_optional_string(data["period"])
    if "payment_term" in data or "payment_terms" in data:
        bid_submission.payment_term = _normalize_optional_string(
            data.get("payment_term") or data.get("payment_terms")
        )
    if "validity" in data:
        bid_submission.validity = _normalize_optional_string(data["validity"])
    if "warranty_period" in data:
        bid_submission.warranty_period = _normalize_optional_string(data["warranty_period"])
    if "gst_rate" in data:
        bid_submission.gst_rate = _parse_decimal_val(data["gst_rate"])
    if "remark" in data or "remarks" in data:
        bid_submission.remark = _normalize_optional_string(
            data.get("remark") or data.get("remarks")
        )

    if "items" in data and data["items"] is not None:
        _replace_items(bid_submission, data["items"])

    return bid_submission


def delete_bid_submission(bid_submission: BidSubmission) -> None:
    db.session.delete(bid_submission)

