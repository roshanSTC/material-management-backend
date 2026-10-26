from app.extensions.database import db
from app.models import Attachment, ImportLogistics
from app.repositories import import_logistics_repository as repository
from app.services.project_step_service import sync_import_logistics_step
from app.utils.remark_utils import normalize_remark_for_db


class ImportLogisticsError(Exception):
    pass


class ImportLogisticsNotFoundError(ImportLogisticsError):
    pass


class ProjectNotFoundError(ImportLogisticsError):
    pass


class SupplierNotFoundError(ImportLogisticsError):
    pass


def get_import_logistics_record(logistics_id: int) -> ImportLogistics:
    logistics = repository.get_import_logistics(logistics_id)
    if not logistics:
        raise ImportLogisticsNotFoundError(
            f"Import logistics record with ID {logistics_id} not found."
        )
    return logistics


def list_import_logistics_records(
    project_id: int | None = None,
    supplier_id: int | None = None,
    logistic_type: str | None = None,
) -> list[ImportLogistics]:
    return repository.list_import_logistics(
        project_id=project_id,
        supplier_id=supplier_id,
        logistic_type=logistic_type,
    )


def create_import_logistics_transaction(data: dict, user_id: int | None = None) -> ImportLogistics:
    project_id = data["project_id"]
    project = repository.get_project(project_id)
    if not project:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    supplier_id = data.get("supplier_id")
    if not supplier_id:
        supplier_id = project.supplier_id
        data["supplier_id"] = supplier_id

    if supplier_id:
        supplier = repository.get_supplier(supplier_id)
        if not supplier:
            raise SupplierNotFoundError(f"Supplier with ID {supplier_id} not found.")

    logistics = repository.create_import_logistics(data)
    try:
        sync_import_logistics_step(project_id)
    except Exception:
        pass
    db.session.flush()

    # If transport detail fields are present, also sync TransportDetail
    from_loc = data.get("from_location")
    to_loc = data.get("to_location")
    charges = data.get("total_transportation_charges") or data.get("transport_charges")
    if from_loc or to_loc or charges:
        try:
            from app.models import TransportDetail
            from app.schemas.import_logistics import _parse_date
            td = TransportDetail(
                project_id=project_id,
                transport_mode=data.get("transport_mode") or data.get("logistic_type") or "air",
                lr_no=data.get("lr_rr_awb_no") or data.get("airway_bill_no") or data.get("bill_of_lading_no"),
                awb_no=data.get("lr_rr_awb_no") or data.get("airway_bill_no"),
                date=_parse_date(data.get("date")),
                from_location=from_loc or data.get("airport_of_loading") or data.get("port_of_loading") or "N/A",
                to_location=to_loc or data.get("port_of_discharge") or "N/A",
                transport_charges=charges,
                remark=normalize_remark_for_db(data.get("remark") or data.get("remarks")),
            )
            db.session.add(td)
            db.session.flush()
        except Exception:
            pass

    remarks_val = data.get("remarks") if "remarks" in data else data.get("remark")
    from app.services.step_remark_service import sync_step_remarks
    sync_step_remarks(
        project_id=project_id,
        step_number=11,
        remarks_data=remarks_val,
        default_user_id=user_id,
        entity_id=logistics.id,
    )

    return logistics


def update_import_logistics_transaction(
    logistics_id: int,
    data: dict,
    user_id: int | None = None,
) -> ImportLogistics:
    logistics = repository.get_import_logistics(logistics_id)
    if not logistics:
        raise ImportLogisticsNotFoundError(
            f"Import logistics record with ID {logistics_id} not found."
        )

    if "project_id" in data and data["project_id"] != logistics.project_id:
        project = repository.get_project(data["project_id"])
        if not project:
            raise ProjectNotFoundError(
                f"Project with ID {data['project_id']} not found."
            )

    if "supplier_id" in data and data["supplier_id"] is not None:
        supplier = repository.get_supplier(data["supplier_id"])
        if not supplier:
            raise SupplierNotFoundError(
                f"Supplier with ID {data['supplier_id']} not found."
            )

    updated = repository.update_import_logistics(logistics, data)
    try:
        sync_import_logistics_step(updated.project_id)
    except Exception:
        pass
    db.session.flush()

    if "remarks" in data or "remark" in data:
        remarks_val = data.get("remarks") if "remarks" in data else data.get("remark")
        from app.services.step_remark_service import sync_step_remarks
        sync_step_remarks(
            project_id=updated.project_id,
            step_number=11,
            remarks_data=remarks_val,
            default_user_id=user_id,
            entity_id=updated.id,
        )

    return updated


def delete_import_logistics_transaction(logistics_id: int) -> list[str]:
    logistics = repository.get_import_logistics(logistics_id)
    if not logistics:
        raise ImportLogisticsNotFoundError(
            f"Import logistics record with ID {logistics_id} not found."
        )

    project_id = logistics.project_id

    # Collect and delete attachments
    attachments = (
        Attachment.query.filter_by(
            entity_type="import_logistics",
            entity_id=logistics.id,
        ).all()
    )
    storage_keys = [att.storage_key for att in attachments if att.storage_key]

    for att in attachments:
        db.session.delete(att)
    repository.delete_import_logistics(logistics)
    try:
        sync_import_logistics_step(project_id)
    except Exception:
        pass
    db.session.flush()

    from app.services.step_remark_service import sync_step_remarks
    sync_step_remarks(
        project_id=project_id,
        step_number=11,
        remarks_data=None,
        entity_id=logistics_id,
    )

    return storage_keys

