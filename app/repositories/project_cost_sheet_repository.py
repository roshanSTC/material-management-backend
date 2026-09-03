from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models import CostSheet, CostSheetItem, ItemPriceHistory, Project, User


def get_project(project_id: int, *, lock: bool = False) -> Project | None:
    statement = db.select(Project).where(Project.id == project_id)
    if lock:
        statement = statement.with_for_update()
    return db.session.execute(statement).scalar_one_or_none()


def get_user(user_id: int) -> User | None:
    return db.session.get(User, user_id)


def get_cost_sheet(cost_sheet_id: int) -> CostSheet | None:
    return db.session.execute(
        db.select(CostSheet)
        .options(
            selectinload(CostSheet.items).selectinload(CostSheetItem.price_history)
        )
        .where(CostSheet.id == cost_sheet_id)
    ).scalar_one_or_none()


def list_cost_sheets_by_project(project_id: int | None = None) -> list[CostSheet]:
    statement = db.select(CostSheet).options(
        selectinload(CostSheet.items).selectinload(CostSheetItem.price_history)
    )
    if project_id is not None:
        statement = statement.where(CostSheet.project_id == project_id).order_by(
            CostSheet.version_number.desc()
        )
    else:
        statement = statement.order_by(CostSheet.created_at.desc())
    return db.session.execute(statement).scalars().all()


def get_next_version_number(project_id: int) -> int:
    latest_version = db.session.execute(
        db.select(func.max(CostSheet.version_number)).where(
            CostSheet.project_id == project_id
        )
    ).scalar_one()
    return (latest_version or 0) + 1


def create_cost_sheet(
    *,
    data: dict,
    project_id: int,
    created_by: int,
    output: dict | None = None,
) -> CostSheet:
    cost_sheet = CostSheet(
        project_id=project_id,
        version_number=get_next_version_number(project_id),
        title=data["title"].strip(),
        global_params=data["globalParams"],
        output=output or {},
        status=data.get("status", "Draft"),
        created_by=created_by,
    )
    for item_data in data["items"]:
        cost_sheet.items.append(
            CostSheetItem(
                quotation_number=(
                    item_data.get("quotationNumber")
                    or item_data.get("quotation_number")
                ),
                quotation_index=(
                    item_data.get("quotationIndex")
                    or item_data.get("quotation_index")
                ),
                item_code=item_data["itemCode"].strip(),
                item_description=item_data["itemDescription"].strip(),
                price_per_unit_eur=item_data["pricePerUnitEur"],
                quantity=item_data["quantity"],
                customs_duty_rate=item_data.get("customsDutyRate"),
            )
        )
    db.session.add(cost_sheet)
    return cost_sheet


def get_cost_sheet_item(
    cost_sheet_item_id: int,
    *,
    lock: bool = False,
) -> CostSheetItem | None:
    statement = db.select(CostSheetItem).where(CostSheetItem.id == cost_sheet_item_id)
    if lock:
        statement = statement.with_for_update()
    return db.session.execute(statement).scalar_one_or_none()


def create_price_history(
    *,
    item: CostSheetItem,
    data: dict,
    changed_by: int,
) -> ItemPriceHistory:
    price_history = ItemPriceHistory(
        old_price_eur=item.price_per_unit_eur,
        new_price_eur=data["pricePerUnitEur"],
        supplier_name=data["supplierName"].strip(),
        change_reason=data["changeReason"].strip(),
        changed_by=changed_by,
    )
    item.price_history.append(price_history)
    item.price_per_unit_eur = data["pricePerUnitEur"]
    return price_history
