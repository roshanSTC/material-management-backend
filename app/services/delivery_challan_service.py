from decimal import Decimal

from app.extensions.database import db
from app.models import DeliveryChallan
from app.repositories.delivery_challan_repository import (
    create_delivery_challan,
    delete_delivery_challan,
    get_delivery_challan,
    get_project,
    list_delivery_challans,
    update_delivery_challan,
)


class DeliveryChallanError(Exception):
    """Base error for delivery challan operations."""


class ProjectNotFoundError(DeliveryChallanError):
    pass


class DeliveryChallanNotFoundError(DeliveryChallanError):
    pass


def _calculate_amounts(data: dict) -> None:
    items = data.get("items") or []
    item_net_sum = Decimal("0.00")

    for item in items:
        qty = item.get("quantity")
        unit_price = item.get("unit_price")
        net_amt = item.get("net_amount")

        if net_amt is None and qty is not None and unit_price is not None:
            try:
                computed_net = (Decimal(str(qty)) * Decimal(str(unit_price))).quantize(
                    Decimal("0.01")
                )
                item["net_amount"] = str(computed_net)
                item_net_sum += computed_net
            except Exception:
                pass
        elif net_amt is not None:
            try:
                item_net_sum += Decimal(str(net_amt))
            except Exception:
                pass

    gst_rate = data.get("gst_rate")
    gst_amount = data.get("gst_amount")
    if gst_amount is None and gst_rate is not None and item_net_sum > 0:
        try:
            computed_gst = (
                item_net_sum * Decimal(str(gst_rate)) / Decimal("100")
            ).quantize(Decimal("0.01"))
            data["gst_amount"] = str(computed_gst)
        except Exception:
            pass

    net_total = data.get("net_total")
    if net_total is None and item_net_sum > 0:
        try:
            gst_val = Decimal(str(data.get("gst_amount") or 0))
            round_val = Decimal(str(data.get("round_off") or 0))
            data["net_total"] = str(
                (item_net_sum + gst_val + round_val).quantize(Decimal("0.01"))
            )
        except Exception:
            pass


def create_delivery_challan_transaction(*, data: dict) -> DeliveryChallan:
    project_id = data.get("project_id")
    if not project_id:
        raise ProjectNotFoundError("Project ID is required.")

    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    _calculate_amounts(data)

    delivery_challan = create_delivery_challan(data=data)
    db.session.flush()

    return delivery_challan


def get_delivery_challan_record(delivery_challan_id: int) -> DeliveryChallan:
    delivery_challan = get_delivery_challan(delivery_challan_id)
    if delivery_challan is None:
        raise DeliveryChallanNotFoundError(
            f"Delivery challan with ID {delivery_challan_id} not found."
        )
    return delivery_challan


def list_delivery_challan_records(
    *,
    project_id: int | None = None,
    delivery_challan_no: str | None = None,
) -> list[DeliveryChallan]:
    return list_delivery_challans(
        project_id=project_id,
        delivery_challan_no=delivery_challan_no,
    )


def update_delivery_challan_transaction(
    *,
    delivery_challan_id: int,
    data: dict,
) -> DeliveryChallan:
    delivery_challan = get_delivery_challan(delivery_challan_id)
    if delivery_challan is None:
        raise DeliveryChallanNotFoundError(
            f"Delivery challan with ID {delivery_challan_id} not found."
        )

    if "project_id" in data:
        project_id = data["project_id"]
        project = get_project(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    if "items" in data:
        _calculate_amounts(data)

    updated_delivery_challan = update_delivery_challan(
        delivery_challan=delivery_challan,
        data=data,
    )
    db.session.flush()

    return updated_delivery_challan


def delete_delivery_challan_transaction(delivery_challan_id: int) -> list[str]:
    delivery_challan = get_delivery_challan(delivery_challan_id)
    if delivery_challan is None:
        raise DeliveryChallanNotFoundError(
            f"Delivery challan with ID {delivery_challan_id} not found."
        )

    storage_keys = delete_delivery_challan(delivery_challan_id)
    db.session.flush()
    return storage_keys

