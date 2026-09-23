from app.extensions.database import db
from app.models.project import Project
from app.models.step_remark import StepRemark
from app.repositories.step_remark_repository import (
    create_remark,
    delete_remark,
    get_remark,
    list_remarks_for_project,
    list_remarks_for_step,
)


class ProjectNotFoundError(Exception):
    """Raised when the specified project does not exist."""


class InvalidStepNumberError(Exception):
    """Raised when an invalid step number is provided."""


class RemarkNotFoundError(Exception):
    """Raised when the specified remark does not exist."""


STEP_NAMES = {
    1: "Customer Query to ST",
    2: "Request Quotation from Supplier",
    3: "Supplier's Quotation",
    4: "Cost Sheet Preparation",
    5: "Quotation to Customer",
    6: "Customer issues Tender",
    7: "S.T. submits Bid Documents",
    8: "Customer issues Purchase Order (PO)",
    9: "S.T. places Order Confirmation with Supplier",
    10: "Supplier raises Bill / Invoice",
    11: "Material delivered to India",
    12: "Customs Clearance",
    13: "Customer Delivery with S.T. Billing",
    14: "Customer makes Payment to S.T.",
    15: "S.T. makes Payment to Partner / Supplier",
}


def serialize_remark(remark: StepRemark) -> dict:
    user_display = None
    if remark.author:
        name_parts = [p for p in (remark.author.first_name, remark.author.last_name) if p]
        user_display = " ".join(name_parts) if name_parts else remark.author.email

    return {
        "id": remark.id,
        "project_id": remark.project_id,
        "step_number": remark.step_number,
        "remark": remark.remark,
        "user": user_display,
        "user_id": remark.user_id,
        "created_at": remark.created_at,
        "updated_at": remark.updated_at,
    }


def add_step_remark(
    *,
    project_id: int,
    step_number: int,
    remark_text: str,
    user_id: int | None = None,
) -> dict:
    if not (1 <= step_number <= 15):
        raise InvalidStepNumberError(f"step_number must be between 1 and 15. Got {step_number}.")

    project = db.session.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with id {project_id} was not found.")

    cleaned_text = remark_text.strip() if remark_text else ""
    if not cleaned_text:
        raise ValueError("Remark text cannot be empty.")

    remark_obj = create_remark(
        project_id=project_id,
        step_number=step_number,
        remark=cleaned_text,
        user_id=user_id,
    )
    db.session.commit()

    return serialize_remark(remark_obj)


def get_project_remarks_grouped(project_id: int) -> list[dict]:
    project = db.session.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with id {project_id} was not found.")

    from app.models.project_step import ProjectStep
    from app.utils.remark_utils import normalize_remark_for_response

    all_remarks = list_remarks_for_project(project_id)

    remarks_by_step = {step_num: [] for step_num in range(1, 16)}
    for r in all_remarks:
        if r.step_number in remarks_by_step:
            remarks_by_step[r.step_number].append(serialize_remark(r))

    project_steps = ProjectStep.query.filter_by(project_id=project_id).all()
    step_map = {ps.step_number: ps for ps in project_steps}

    for step_num in range(1, 16):
        if step_num in step_map:
            ps = step_map[step_num]
            data = ps.data or {}
            raw = data.get("remarks") if data.get("remarks") is not None else data.get("remark")
            if raw:
                step_remarks = normalize_remark_for_response(raw)
                if not remarks_by_step[step_num]:
                    remarks_by_step[step_num] = step_remarks

    return [
        {
            "step_number": step_num,
            "step_name": STEP_NAMES.get(step_num, f"Step {step_num}"),
            "remarks": remarks_by_step[step_num],
        }
        for step_num in range(1, 16)
    ]


def delete_step_remark(
    *,
    project_id: int,
    remark_id: int,
) -> None:
    project = db.session.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with id {project_id} was not found.")

    remark_obj = get_remark(remark_id)
    if remark_obj is None or remark_obj.project_id != project_id:
        raise RemarkNotFoundError(
            f"Remark with id {remark_id} was not found for project {project_id}."
        )

    delete_remark(remark_obj)
    db.session.commit()


def sync_step_remarks(
    *,
    project_id: int,
    step_number: int,
    remarks_data,
    default_user_id: int | None = None,
) -> list[StepRemark]:
    """
    Synchronizes remarks for a given project and step_number with the step_remarks table.
    - If remarks_data is None or empty, deletes existing remarks for that step.
    - If remarks_data has items, updates existing StepRemark records where id matches,
      creates new StepRemark records for new items, and removes any not in the incoming list.
    """
    from datetime import datetime
    from app.models.user import User
    from app.utils.remark_utils import normalize_remark_for_response

    project = db.session.get(Project, project_id)
    if project is None:
        return []

    existing_remarks = (
        db.session.execute(
            db.select(StepRemark)
            .where(
                StepRemark.project_id == project_id,
                StepRemark.step_number == step_number,
            )
            .order_by(StepRemark.id.asc())
        )
        .scalars()
        .all()
    )
    existing_map = {r.id: r for r in existing_remarks}

    parsed_items = normalize_remark_for_response(remarks_data)

    matched_ids = set()
    result_remarks = []

    for item in parsed_items:
        if isinstance(item, str):
            text = item.strip()
            item_dict = {}
        elif isinstance(item, dict):
            text = str(item.get("remark") or item.get("text") or "").strip()
            item_dict = item
        else:
            text = str(item).strip()
            item_dict = {}

        if not text:
            continue

        # Extract and validate user_id
        uid = None
        raw_uid = item_dict.get("user_id")
        if raw_uid is not None:
            try:
                uid = int(raw_uid)
            except (ValueError, TypeError):
                uid = None

        if uid is None and default_user_id is not None:
            try:
                uid = int(default_user_id)
            except (ValueError, TypeError):
                uid = None

        if uid is not None and db.session.get(User, uid) is None:
            uid = None

        # Extract created_at
        created_dt = None
        raw_created = item_dict.get("created_at")
        if isinstance(raw_created, datetime):
            created_dt = raw_created.replace(tzinfo=None)
        elif isinstance(raw_created, str) and raw_created.strip():
            try:
                clean_str = raw_created.replace("Z", "")
                created_dt = datetime.fromisoformat(clean_str).replace(tzinfo=None)
            except (ValueError, TypeError):
                created_dt = None

        if created_dt is None:
            created_dt = datetime.utcnow()

        # Check for matching existing integer ID
        raw_id = item_dict.get("id")
        item_id = None
        if isinstance(raw_id, int):
            item_id = raw_id
        elif isinstance(raw_id, str) and raw_id.isdigit():
            item_id = int(raw_id)

        if item_id and item_id in existing_map and item_id not in matched_ids:
            r = existing_map[item_id]
            r.remark = text
            if uid is not None:
                r.user_id = uid
            r.updated_at = datetime.utcnow()
            matched_ids.add(r.id)
            result_remarks.append(r)
        else:
            new_r = StepRemark(
                project_id=project_id,
                step_number=step_number,
                remark=text,
                user_id=uid,
                created_at=created_dt,
                updated_at=created_dt,
            )
            db.session.add(new_r)
            result_remarks.append(new_r)

    for r in existing_remarks:
        if r.id not in matched_ids:
            db.session.delete(r)

    db.session.flush()
    return result_remarks


