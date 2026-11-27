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


from app.utils.remark_utils import normalize_remark_for_db


def _normalize_optional_string(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return normalize_remark_for_db(value)
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


def _parse_date_val(val) -> date | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    s = str(val).strip()
    if not s:
        return None
    if "T" in s:
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        except Exception:
            return None
    try:
        return date.fromisoformat(s)
    except Exception:
        return None


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
    for idx, item in enumerate(items, start=1):
        desc = str(item.get("description") or "").strip()
        quantity_val = _parse_decimal_val(item.get("quantity")) or Decimal("1")
        unit_price_val = _parse_decimal_val(item.get("unit_price"))
        total_amount_val = _parse_decimal_val(item.get("total_amount"))
        if total_amount_val is None and unit_price_val is not None:
            total_amount_val = (quantity_val * unit_price_val).quantize(Decimal("0.01"))
        hsn_sac_val = _normalize_optional_string(item.get("hsn_sac"))

        sub_item = BidSubmissionItem(
            sr_no=item.get("sr_no") if item.get("sr_no") is not None else idx,
            description=desc,
            hsn_sac=hsn_sac_val,
            unit_price=unit_price_val,
            quantity=quantity_val,
            total_amount=total_amount_val,
            currency=_normalize_optional_string(item.get("currency")),
        )
        bid_submission.items.append(sub_item)


def create_bid_submission(*, data: dict) -> BidSubmission:
    t_issue_date = _parse_date_val(data.get("tender_issue_date"))
    if t_issue_date is None and data.get("project_id"):
        latest_tender = get_latest_customer_tender_for_project(data["project_id"])
        if latest_tender and getattr(latest_tender, "tender_issue_date", None):
            t_issue_date = latest_tender.tender_issue_date
    if t_issue_date is None and data.get("bid_submission_date"):
        t_issue_date = _parse_date_val(data.get("bid_submission_date"))

    submission = BidSubmission(
        project_id=data["project_id"],
        tender_id=data.get("tender_id"),
        customer_name=_normalize_optional_string(data.get("customer_name")),
        tender_title=_normalize_optional_string(data.get("tender_title")),
        tender_no=str(data.get("tender_no") or "").strip(),
        tender_issue_date=t_issue_date,
        total_no_corrigendum_issued=data.get("total_no_corrigendum_issued"),
        bid_submission_date=_parse_datetime_val(data.get("bid_submission_date")),
        delivery_terms=_normalize_optional_string(data.get("delivery_terms")),
        delivery_period=_normalize_optional_string(data.get("delivery_period")),
        payment_terms=_normalize_optional_string(data.get("payment_terms")),
        bid_validity=_normalize_optional_string(data.get("bid_validity")),
        warranty_period=_normalize_optional_string(data.get("warranty_period")),
        gst_pct=_parse_decimal_val(data.get("gst_pct")),
        total_net_amount=_parse_decimal_val(data.get("total_net_amount")),
        gst_amount=_parse_decimal_val(data.get("gst_amount")),
        total_gross_amount=_parse_decimal_val(data.get("total_gross_amount")),
        currency_unit=_normalize_optional_string(data.get("currency_unit")),
        currency_symbol=_normalize_optional_string(data.get("currency_symbol")),
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


def get_latest_bid_submission_for_project(project_id: int) -> BidSubmission | None:
    return (
        db.session.execute(
            db.select(BidSubmission)
            .options(selectinload(BidSubmission.items))
            .where(BidSubmission.project_id == project_id)
            .order_by(BidSubmission.id.desc())
        )
        .scalars()
        .first()
    )


def update_bid_submission(
    bid_submission: BidSubmission,
    *,
    data: dict,
) -> BidSubmission:
    if "project_id" in data:
        bid_submission.project_id = data["project_id"]
    if "tender_id" in data:
        bid_submission.tender_id = data["tender_id"]
    if "customer_name" in data:
        bid_submission.customer_name = _normalize_optional_string(data["customer_name"])
    if "tender_title" in data:
        bid_submission.tender_title = _normalize_optional_string(data["tender_title"])
    if "tender_issue_date" in data:
        bid_submission.tender_issue_date = _parse_date_val(data["tender_issue_date"])
    if "total_no_corrigendum_issued" in data:
        bid_submission.total_no_corrigendum_issued = data["total_no_corrigendum_issued"]
    if "bid_submission_date" in data:
        bid_submission.bid_submission_date = _parse_datetime_val(data["bid_submission_date"])
    if "tender_no" in data and data["tender_no"] is not None:
        bid_submission.tender_no = str(data["tender_no"]).strip()
    if "delivery_terms" in data:
        bid_submission.delivery_terms = _normalize_optional_string(data["delivery_terms"])
    if "delivery_period" in data:
        bid_submission.delivery_period = _normalize_optional_string(data["delivery_period"])
    if "payment_terms" in data:
        bid_submission.payment_terms = _normalize_optional_string(data["payment_terms"])
    if "bid_validity" in data:
        bid_submission.bid_validity = _normalize_optional_string(data["bid_validity"])
    if "warranty_period" in data:
        bid_submission.warranty_period = _normalize_optional_string(data["warranty_period"])
    if "gst_pct" in data:
        bid_submission.gst_pct = _parse_decimal_val(data["gst_pct"])
    if "total_net_amount" in data:
        bid_submission.total_net_amount = _parse_decimal_val(data["total_net_amount"])
    if "gst_amount" in data:
        bid_submission.gst_amount = _parse_decimal_val(data["gst_amount"])
    if "total_gross_amount" in data:
        bid_submission.total_gross_amount = _parse_decimal_val(data["total_gross_amount"])
    if "currency_unit" in data:
        bid_submission.currency_unit = _normalize_optional_string(data["currency_unit"])
    if "currency_symbol" in data:
        bid_submission.currency_symbol = _normalize_optional_string(data["currency_symbol"])
    if "remark" in data or "remarks" in data:
        bid_submission.remark = _normalize_optional_string(
            data.get("remark") or data.get("remarks")
        )

    if "items" in data and data["items"] is not None:
        _replace_items(bid_submission, data["items"])

    return bid_submission


def delete_bid_submission(bid_submission: BidSubmission) -> None:
    db.session.delete(bid_submission)

