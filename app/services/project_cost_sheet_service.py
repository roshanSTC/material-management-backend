from datetime import datetime
from decimal import Decimal

from app.extensions.database import db
from app.models import CostSheet, CostSheetItem
from app.repositories.project_cost_sheet_repository import (
    create_cost_sheet,
    create_price_history,
    get_cost_sheet,
    get_cost_sheet_item,
    get_project,
    get_user,
    list_cost_sheets_by_project,
)
from app.services.cost_sheet_service import calculate_cost_sheet


class ProjectCostSheetError(Exception):
    """Base error for persistent project cost-sheet operations."""


class ProjectNotFoundError(ProjectCostSheetError):
    pass


class CostSheetNotFoundError(ProjectCostSheetError):
    pass


class CostSheetItemNotFoundError(ProjectCostSheetError):
    pass


class CostSheetItemMismatchError(ProjectCostSheetError):
    pass


class UserNotFoundError(ProjectCostSheetError):
    pass


def create_project_cost_sheet(*, project_id: int, data: dict, created_by: int) -> CostSheet:
    project = get_project(project_id, lock=True)
    if project is None:
        raise ProjectNotFoundError(f"Project with id {project_id} was not found.")
    _validate_user(created_by)

    # Compute calculation output
    items_for_calc = [
        {
            "quotationNumber": item.get("quotationNumber") or "",
            "quotationIndex": item.get("quotationIndex") or "",
            "itemDescription": item.get("itemDescription", ""),
            "itemCode": item.get("itemCode", ""),
            "pricePerUnitEur": float(item["pricePerUnitEur"]),
            "quantity": float(item["quantity"]),
            "customsDutyRate": (
                float(item["customsDutyRate"])
                if item.get("customsDutyRate") is not None
                else None
            ),
        }
        for item in data["items"]
    ]
    output = calculate_cost_sheet(
        global_params=data["globalParams"],
        items=items_for_calc,
    )

    cost_sheet = create_cost_sheet(
        data=data,
        project_id=project.id,
        created_by=created_by,
        output=output,
    )
    db.session.flush()
    return cost_sheet


def list_project_cost_sheets(project_id: int | None = None) -> list[CostSheet]:
    if project_id is not None:
        _get_project_or_raise(project_id)
    return list_cost_sheets_by_project(project_id)


def get_project_cost_sheet(cost_sheet_id: int) -> CostSheet:
    cost_sheet = get_cost_sheet(cost_sheet_id)
    if cost_sheet is None:
        raise CostSheetNotFoundError(
            f"Cost sheet with id {cost_sheet_id} was not found."
        )
    return cost_sheet


def update_cost_sheet_item_rate(
    *,
    cost_sheet_id: int,
    cost_sheet_item_id: int,
    data: dict,
    changed_by: int,
) -> tuple[CostSheet, CostSheetItem, bool]:
    cost_sheet = get_project_cost_sheet(cost_sheet_id)
    item = get_cost_sheet_item(cost_sheet_item_id, lock=True)
    if item is None:
        raise CostSheetItemNotFoundError(
            f"Cost sheet item with id {cost_sheet_item_id} was not found."
        )
    if item.cost_sheet_id != cost_sheet.id:
        raise CostSheetItemMismatchError(
            "The cost sheet item does not belong to the selected cost sheet."
        )
    _validate_user(changed_by)

    new_price = Decimal(str(data["pricePerUnitEur"]))
    if item.price_per_unit_eur == new_price:
        return cost_sheet, item, False

    history_data = {**data, "pricePerUnitEur": new_price}
    create_price_history(item=item, data=history_data, changed_by=changed_by)
    cost_sheet.updated_at = datetime.utcnow()

    # Recalculate and persist updated output
    output = calculate_cost_sheet(
        global_params=cost_sheet.global_params,
        items=[_calculation_item(i) for i in cost_sheet.items],
    )
    cost_sheet.output = output

    db.session.flush()
    return cost_sheet, item, True


def serialize_cost_sheet_metadata(cost_sheet: CostSheet) -> dict:
    output = cost_sheet.output
    if not output:
        output = calculate_cost_sheet(
            global_params=cost_sheet.global_params,
            items=[_calculation_item(item) for item in cost_sheet.items],
        )

    price_histories = [
        history
        for item in cost_sheet.items
        for history in item.price_history
    ]
    price_histories.sort(key=lambda history: (history.created_at, history.id), reverse=True)
    latest_price_change = price_histories[0] if price_histories else None

    cumulative_cost = (
        output.get("columnTotals", {}).get("totalCostInr", 0.0)
        if isinstance(output, dict)
        else 0.0
    )

    return {
        "id": cost_sheet.id,
        "project_id": cost_sheet.project_id,
        "product_id": cost_sheet.project_id,
        "versionNumber": cost_sheet.version_number,
        "title": cost_sheet.title,
        "globalParams": cost_sheet.global_params,
        "output": output,
        "status": cost_sheet.status,
        "createdBy": cost_sheet.created_by,
        "createdAt": cost_sheet.created_at,
        "updatedAt": cost_sheet.updated_at,
        "totalItemCount": len(cost_sheet.items),
        "cumulativeProjectCostInr": cumulative_cost,
        "hasRateIncrease": any(
            history.new_price_eur > history.old_price_eur
            for history in price_histories
        ),
        "latestPriceChange": _serialize_price_history(latest_price_change),
        "recentPriceChanges": [
            _serialize_price_history(history) for history in price_histories[:10]
        ],
        "items": [_serialize_item(item) for item in cost_sheet.items],
    }


def cost_sheet_export_payload(cost_sheet: CostSheet) -> tuple[dict, list[dict]]:
    return cost_sheet.global_params, [
        {
            "quotationNumber": item.quotation_number or cost_sheet.title,
            "quotationIndex": item.quotation_index or f"V{cost_sheet.version_number}-{item.id}",
            "itemDescription": item.item_description,
            "itemCode": item.item_code,
            "pricePerUnitEur": float(item.price_per_unit_eur),
            "quantity": float(item.quantity),
            "customsDutyRate": (
                float(item.customs_duty_rate)
                if item.customs_duty_rate is not None
                else None
            ),
        }
        for item in cost_sheet.items
    ]


def _get_project_or_raise(project_id: int):
    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with id {project_id} was not found.")
    return project


def _validate_user(user_id: int) -> None:
    if get_user(user_id) is None:
        raise UserNotFoundError(f"User with id {user_id} was not found.")


def _calculation_item(item: CostSheetItem) -> dict:
    return {
        "quotationNumber": item.quotation_number or "",
        "quotationIndex": item.quotation_index or "",
        "itemDescription": item.item_description,
        "itemCode": item.item_code,
        "pricePerUnitEur": float(item.price_per_unit_eur),
        "quantity": float(item.quantity),
        "customsDutyRate": (
            float(item.customs_duty_rate)
            if item.customs_duty_rate is not None
            else None
        ),
    }


def _serialize_item(item: CostSheetItem) -> dict:
    latest_price_change = item.price_history[0] if item.price_history else None
    return {
        "id": item.id,
        "quotationNumber": item.quotation_number,
        "quotationIndex": item.quotation_index,
        "itemCode": item.item_code,
        "itemDescription": item.item_description,
        "pricePerUnitEur": float(item.price_per_unit_eur),
        "quantity": float(item.quantity),
        "customsDutyRate": (
            float(item.customs_duty_rate)
            if item.customs_duty_rate is not None
            else None
        ),
        "hasRateIncrease": bool(
            latest_price_change
            and latest_price_change.new_price_eur > latest_price_change.old_price_eur
        ),
        "latestPriceChange": _serialize_price_history(latest_price_change),
        "createdAt": item.created_at,
        "updatedAt": item.updated_at,
    }


def _serialize_price_history(history) -> dict | None:
    if history is None:
        return None
    return {
        "id": history.id,
        "oldPriceEur": float(history.old_price_eur),
        "newPriceEur": float(history.new_price_eur),
        "supplierName": history.supplier_name,
        "changeReason": history.change_reason,
        "changedBy": history.changed_by,
        "createdAt": history.created_at,
        "isRateIncrease": history.new_price_eur > history.old_price_eur,
    }
