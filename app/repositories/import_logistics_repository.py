from datetime import date, datetime

from sqlalchemy import select

from app.extensions.database import db
from app.models import ImportLogistics, Project, Supplier
from app.utils.remark_utils import normalize_remark_for_db


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_supplier(supplier_id: int) -> Supplier | None:
    return db.session.get(Supplier, supplier_id)


def get_import_logistics(logistics_id: int) -> ImportLogistics | None:
    return db.session.get(ImportLogistics, logistics_id)


def get_import_logistics_by_project_id(project_id: int) -> ImportLogistics | None:
    stmt = (
        select(ImportLogistics)
        .where(ImportLogistics.project_id == project_id)
        .order_by(ImportLogistics.id.desc())
    )
    return db.session.execute(stmt).scalars().first()


def list_import_logistics(
    project_id: int | None = None,
    supplier_id: int | None = None,
    transportation_mode: str | None = None,
) -> list[ImportLogistics]:
    stmt = select(ImportLogistics).order_by(ImportLogistics.id.desc())

    if project_id is not None:
        stmt = stmt.where(ImportLogistics.project_id == project_id)
    if supplier_id is not None:
        stmt = stmt.where(ImportLogistics.supplier_id == supplier_id)
    if transportation_mode is not None:
        stmt = stmt.where(ImportLogistics.transportation_mode == transportation_mode)

    return list(db.session.execute(stmt).scalars().all())


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


def create_import_logistics(data: dict) -> ImportLogistics:
    logistics = ImportLogistics(
        project_id=data["project_id"],
        supplier_id=data.get("supplier_id"),
        transportation_mode=data["transportation_mode"],
        lr_rr_awb_no=data.get("lr_rr_awb_no"),
        lr_rr_awb_date=_parse_date_val(data["lr_rr_awb_date"]),
        from_location=data.get("from_location"),
        to_location=data.get("to_location"),
        total_transportation_charges=data.get("total_transportation_charges"),
        remark=normalize_remark_for_db(data.get("remark")),
    )
    db.session.add(logistics)
    db.session.flush()
    return logistics


def update_import_logistics(logistics: ImportLogistics, data: dict) -> ImportLogistics:
    if "project_id" in data:
        logistics.project_id = data["project_id"]
    if "supplier_id" in data:
        logistics.supplier_id = data["supplier_id"]
    if "transportation_mode" in data and data["transportation_mode"] is not None:
        logistics.transportation_mode = data["transportation_mode"]
    if "lr_rr_awb_no" in data:
        logistics.lr_rr_awb_no = data["lr_rr_awb_no"]
    if "lr_rr_awb_date" in data and data["lr_rr_awb_date"] is not None:
        logistics.lr_rr_awb_date = _parse_date_val(data["lr_rr_awb_date"])
    if "from_location" in data:
        logistics.from_location = data["from_location"]
    if "to_location" in data:
        logistics.to_location = data["to_location"]
    if "total_transportation_charges" in data:
        logistics.total_transportation_charges = data["total_transportation_charges"]
    if "remark" in data:
        logistics.remark = normalize_remark_for_db(data["remark"])

    logistics.updated_at = datetime.utcnow()
    db.session.flush()
    return logistics


def delete_import_logistics(logistics: ImportLogistics) -> None:
    db.session.delete(logistics)
    db.session.flush()

