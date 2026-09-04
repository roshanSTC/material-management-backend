from app.extensions.database import db
from app.models import BidSubmission
from app.repositories.bid_submission_repository import (
    create_bid_submission,
    delete_bid_submission,
    get_bid_submission,
    get_customer_tender,
    get_latest_customer_tender_for_project,
    get_project,
    list_bid_submissions,
    update_bid_submission,
)
from app.services.attachment_service import delete_attachment
from app.services.project_step_service import sync_bid_submission_step


class BidSubmissionError(Exception):
    """Base error for bid submission operations."""


class ProjectNotFoundError(BidSubmissionError):
    pass


class TenderNotFoundError(BidSubmissionError):
    pass


class BidSubmissionNotFoundError(BidSubmissionError):
    pass


def _resolve_and_validate_parties(data: dict) -> tuple[int, int | None]:
    project_id = data.get("project_id")
    if not project_id:
        raise ProjectNotFoundError("Project ID is required.")

    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    tender_id = data.get("tender_id")
    if tender_id is None or tender_id == 0:
        latest_tender = get_latest_customer_tender_for_project(project_id)
        if latest_tender:
            tender_id = latest_tender.id
            data["tender_id"] = tender_id
            if not data.get("tender_title") and latest_tender.tender_title:
                data["tender_title"] = latest_tender.tender_title
            if not data.get("tender_number") and latest_tender.tender_number:
                data["tender_number"] = latest_tender.tender_number
        else:
            data["tender_id"] = None
    else:
        tender = get_customer_tender(tender_id)
        if tender is None:
            raise TenderNotFoundError(f"Customer tender with ID {tender_id} not found.")
        if tender.project_id != project_id:
            raise TenderNotFoundError(
                f"Customer tender ID {tender_id} does not belong to project {project_id}."
            )

    return project_id, data.get("tender_id")


def create_bid_submission_transaction(*, data: dict) -> BidSubmission:
    project_id, _ = _resolve_and_validate_parties(data)

    bid_submission = create_bid_submission(data=data)
    db.session.flush()

    sync_bid_submission_step(project_id)
    return bid_submission


def get_bid_submission_record(bid_submission_id: int) -> BidSubmission:
    submission = get_bid_submission(bid_submission_id)
    if submission is None:
        raise BidSubmissionNotFoundError(f"Bid submission with ID {bid_submission_id} not found.")
    return submission


def list_bid_submission_records(
    *,
    project_id: int | None = None,
) -> list[BidSubmission]:
    return list_bid_submissions(
        project_id=project_id,
    )


def update_bid_submission_transaction(
    *,
    bid_submission_id: int,
    data: dict,
) -> BidSubmission:
    bid_submission = get_bid_submission_record(bid_submission_id)
    previous_project_id = bid_submission.project_id

    if "project_id" in data or "tender_id" in data:
        check_data = {
            "project_id": data.get("project_id", bid_submission.project_id),
            "tender_id": data.get("tender_id", bid_submission.tender_id),
        }
        resolved_pid, resolved_tid = _resolve_and_validate_parties(check_data)
        if "project_id" in data:
            data["project_id"] = resolved_pid
        data["tender_id"] = resolved_tid

    bid_submission = update_bid_submission(bid_submission, data=data)
    db.session.flush()

    project_id = bid_submission.project_id
    sync_bid_submission_step(project_id)
    if previous_project_id != project_id:
        sync_bid_submission_step(previous_project_id)

    return bid_submission


def delete_bid_submission_transaction(bid_submission_id: int) -> list[str]:
    bid_submission = get_bid_submission_record(bid_submission_id)
    project_id = bid_submission.project_id

    # Clean up associated attachments in DB
    storage_keys = delete_attachment(
        entity_type="bid_submission",
        entity_id=bid_submission_id,
    )

    delete_bid_submission(bid_submission)
    db.session.flush()

    sync_bid_submission_step(project_id)
    return storage_keys

