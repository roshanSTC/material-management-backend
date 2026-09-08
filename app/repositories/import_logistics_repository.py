from datetime import date, datetime

from sqlalchemy import select

from app.extensions.database import db
from app.models import ImportLogistics, Project, Supplier


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
    logistic_type: str | None = None,
) -> list[ImportLogistics]:
    stmt = select(ImportLogistics).order_by(ImportLogistics.id.desc())

    if project_id is not None:
        stmt = stmt.where(ImportLogistics.project_id == project_id)
    if supplier_id is not None:
        stmt = stmt.where(ImportLogistics.supplier_id == supplier_id)
    if logistic_type is not None:
        stmt = stmt.where(ImportLogistics.logistic_type == logistic_type)

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
        logistic_type=data["logistic_type"],
        date=_parse_date_val(data["date"]),
        port_of_discharge=data.get("port_of_discharge"),
        remark=data.get("remark"),
        # Air fields
        airway_bill_no=data.get("airway_bill_no"),
        flight_name=data.get("flight_name"),
        flight_no=data.get("flight_no"),
        airport_of_loading=data.get("airport_of_loading"),
        # Sea fields
        bill_of_lading_no=data.get("bill_of_lading_no"),
        vessel_name=data.get("vessel_name"),
        voyage_no=data.get("voyage_no"),
        port_of_loading=data.get("port_of_loading"),
    )
    db.session.add(logistics)
    db.session.flush()
    return logistics


def update_import_logistics(logistics: ImportLogistics, data: dict) -> ImportLogistics:
    if "project_id" in data:
        logistics.project_id = data["project_id"]
    if "supplier_id" in data:
        logistics.supplier_id = data["supplier_id"]
    if "logistic_type" in data and data["logistic_type"] is not None:
        logistics.logistic_type = data["logistic_type"]
    if "date" in data and data["date"] is not None:
        logistics.date = _parse_date_val(data["date"])
    if "port_of_discharge" in data:
        logistics.port_of_discharge = data["port_of_discharge"]
    if "remark" in data:
        logistics.remark = data["remark"]

    # Air fields
    if "airway_bill_no" in data:
        logistics.airway_bill_no = data["airway_bill_no"]
    if "flight_name" in data:
        logistics.flight_name = data["flight_name"]
    if "flight_no" in data:
        logistics.flight_no = data["flight_no"]
    if "airport_of_loading" in data:
        logistics.airport_of_loading = data["airport_of_loading"]

    # Sea fields
    if "bill_of_lading_no" in data:
        logistics.bill_of_lading_no = data["bill_of_lading_no"]
    if "vessel_name" in data:
        logistics.vessel_name = data["vessel_name"]
    if "voyage_no" in data:
        logistics.voyage_no = data["voyage_no"]
    if "port_of_loading" in data:
        logistics.port_of_loading = data["port_of_loading"]

    logistics.updated_at = datetime.utcnow()
    db.session.flush()
    return logistics


def delete_import_logistics(logistics: ImportLogistics) -> None:
    db.session.delete(logistics)
    db.session.flush()

