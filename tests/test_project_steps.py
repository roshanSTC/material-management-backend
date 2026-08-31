
import pytest

from app.extensions.database import db
from app.models import ProjectStep


VALID_STEP_DATA = {
    1: {
        "query_description": "Need 2x air compressors for Pune plant",
        "query_date": "2026-08-27",
        "remarks": "Urgent requirement",
    },
    2: {
        "quotation_requested_date": "2026-08-28",
        "supplier_contacted": True,
        "remarks": "",
    },
    3: {
        "quotation_amount": 52250,
        "quotation_date": "2026-08-29",
        "validity_days": 30,
        "remarks": "CIF",
    },
}


def auth_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
    }


def test_get_all_project_steps_returns_all_15(
    client,
    access_token,
    project,
):
    response = client.get(
        f"/api/v1/projects/{project.id}/steps",
        headers=auth_headers(access_token),
    )

    assert response.status_code == 200

    body = response.get_json()

    assert isinstance(body, list)
    assert len(body) == 15

    step_numbers = [step["step_number"] for step in body]

    assert step_numbers == list(range(1, 16))

    for step in body:
        assert step["project_id"] == project.id
        assert step["step_name"]
        assert step["status"] in {
            "pending",
            "in_progress",
            "completed",
        }

    pending_steps = [
        step
        for step in body
        if step["status"] == "pending"
    ]

    for step in pending_steps:
        assert step["id"] is None
        assert step["data"] is None
        assert step["completed_at"] is None


def test_get_all_project_steps_requires_authentication(
    client,
    project,
):
    response = client.get(
        f"/api/v1/projects/{project.id}/steps",
    )

    assert response.status_code == 401


def test_get_all_project_steps_project_not_found(
    client,
    access_token,
):
    response = client.get(
        "/api/v1/projects/999999/steps",
        headers=auth_headers(access_token),
    )

    assert response.status_code == 404


def test_get_single_project_step(
    client,
    access_token,
    project,
):
    response = client.get(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
    )

    assert response.status_code == 404


def test_get_single_saved_project_step(
    client,
    access_token,
    project,
):
    step = ProjectStep(
        project_id=project.id,
        step_number=1,
        step_name="Customer Query to ST",
        status="completed",
        data=VALID_STEP_DATA[1],
    )

    with client.application.app_context():
        db.session.add(step)
        db.session.commit()

    response = client.get(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["id"] == step.id
    assert body["project_id"] == project.id
    assert body["step_number"] == 1
    assert body["step_name"] == "Customer Query to ST"
    assert body["status"] == "completed"
    assert body["data"] == VALID_STEP_DATA[1]


def test_get_single_project_step_invalid_step_number(
    client,
    access_token,
    project,
):
    response = client.get(
        f"/api/v1/projects/{project.id}/steps/16",
        headers=auth_headers(access_token),
    )

    assert response.status_code == 422

    body = response.get_json()

    assert body["error"]["code"] == "INVALID_STEP_NUMBER"


def test_get_single_project_step_requires_authentication(
    client,
    project,
):
    response = client.get(
        f"/api/v1/projects/{project.id}/steps/1",
    )

    assert response.status_code == 401


def test_create_project_step(
    client,
    access_token,
    project,
):
    response = client.post(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json={
            "status": "completed",
            "data": VALID_STEP_DATA[1],
        },
    )

    assert response.status_code == 201

    body = response.get_json()

    assert body["id"] is not None
    assert body["project_id"] == project.id
    assert body["step_number"] == 1
    assert body["step_name"] == "Customer Query to ST"
    assert body["status"] == "completed"
    assert body["completed_at"] is not None
    assert body["data"] == VALID_STEP_DATA[1]


def test_create_in_progress_step(
    client,
    access_token,
    project,
):
    response = client.post(
        f"/api/v1/projects/{project.id}/steps/2",
        headers=auth_headers(access_token),
        json={
            "status": "in_progress",
            "data": VALID_STEP_DATA[2],
        },
    )

    assert response.status_code == 201

    body = response.get_json()

    assert body["status"] == "in_progress"
    assert body["completed_at"] is None


def test_create_pending_step(
    client,
    access_token,
    project,
):
    response = client.post(
        f"/api/v1/projects/{project.id}/steps/3",
        headers=auth_headers(access_token),
        json={
            "status": "pending",
            "data": None,
        },
    )

    assert response.status_code == 201

    body = response.get_json()

    assert body["status"] == "pending"
    assert body["completed_at"] is None
    assert body["data"] is None


def test_create_project_step_requires_authentication(
    client,
    project,
):
    response = client.post(
        f"/api/v1/projects/{project.id}/steps/1",
        json={
            "status": "completed",
            "data": VALID_STEP_DATA[1],
        },
    )

    assert response.status_code == 401


def test_create_project_step_project_not_found(
    client,
    access_token,
):
    response = client.post(
        "/api/v1/projects/999999/steps/1",
        headers=auth_headers(access_token),
        json={
            "status": "completed",
            "data": VALID_STEP_DATA[1],
        },
    )

    assert response.status_code == 404


def test_create_project_step_invalid_step_number(
    client,
    access_token,
    project,
):
    response = client.post(
        f"/api/v1/projects/{project.id}/steps/16",
        headers=auth_headers(access_token),
        json={
            "status": "completed",
            "data": {},
        },
    )

    assert response.status_code == 422

    body = response.get_json()

    assert body["error"]["code"] == "INVALID_STEP_NUMBER"


def test_create_project_step_invalid_status(
    client,
    access_token,
    project,
):
    response = client.post(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json={
            "status": "invalid",
            "data": VALID_STEP_DATA[1],
        },
    )

    assert response.status_code == 422


def test_create_project_step_unknown_data_field(
    client,
    access_token,
    project,
):
    response = client.post(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json={
            "status": "completed",
            "data": {
                "query_description": "Test",
                "unknown_field": "should not be accepted",
            },
        },
    )

    assert response.status_code == 422

    body = response.get_json()

    assert body["error"]["code"] == "INVALID_STEP_DATA"


def test_create_duplicate_project_step(
    client,
    access_token,
    project,
):
    payload = {
        "status": "completed",
        "data": VALID_STEP_DATA[1],
    }

    first_response = client.post(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json=payload,
    )

    assert second_response.status_code == 409

    body = second_response.get_json()

    assert body["error"]["code"] == "PROJECT_STEP_ALREADY_EXISTS"


def test_update_project_step(
    client,
    access_token,
    project,
):
    create_response = client.post(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json={
            "status": "in_progress",
            "data": VALID_STEP_DATA[1],
        },
    )

    assert create_response.status_code == 201

    update_response = client.put(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json={
            "status": "completed",
            "data": {
                **VALID_STEP_DATA[1],
                "remarks": "Updated requirement",
            },
        },
    )

    assert update_response.status_code == 200

    body = update_response.get_json()

    assert body["project_id"] == project.id
    assert body["step_number"] == 1
    assert body["status"] == "completed"
    assert body["completed_at"] is not None
    assert body["data"]["remarks"] == "Updated requirement"


def test_update_in_progress_clears_completed_at(
    client,
    access_token,
    project,
):
    client.post(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json={
            "status": "completed",
            "data": VALID_STEP_DATA[1],
        },
    )

    response = client.put(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json={
            "status": "in_progress",
            "data": VALID_STEP_DATA[1],
        },
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["status"] == "in_progress"
    assert body["completed_at"] is None


def test_update_pending_clears_completed_at(
    client,
    access_token,
    project,
):
    client.post(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json={
            "status": "completed",
            "data": VALID_STEP_DATA[1],
        },
    )

    response = client.put(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json={
            "status": "pending",
            "data": None,
        },
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["status"] == "pending"
    assert body["completed_at"] is None
    assert body["data"] is None


def test_update_unsaved_project_step_returns_404(
    client,
    access_token,
    project,
):
    response = client.put(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json={
            "status": "completed",
            "data": VALID_STEP_DATA[1],
        },
    )

    assert response.status_code == 404

    body = response.get_json()

    assert body["error"]["code"] == "PROJECT_STEP_NOT_FOUND"


def test_update_project_step_requires_authentication(
    client,
    project,
):
    response = client.put(
        f"/api/v1/projects/{project.id}/steps/1",
        json={
            "status": "completed",
            "data": VALID_STEP_DATA[1],
        },
    )

    assert response.status_code == 401


def test_update_project_step_invalid_status(
    client,
    access_token,
    project,
):
    client.post(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json={
            "status": "in_progress",
            "data": VALID_STEP_DATA[1],
        },
    )

    response = client.put(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json={
            "status": "finished",
            "data": VALID_STEP_DATA[1],
        },
    )

    assert response.status_code == 422


def test_update_project_step_unknown_data_field(
    client,
    access_token,
    project,
):
    client.post(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json={
            "status": "in_progress",
            "data": VALID_STEP_DATA[1],
        },
    )

    response = client.put(
        f"/api/v1/projects/{project.id}/steps/1",
        headers=auth_headers(access_token),
        json={
            "status": "completed",
            "data": {
                "query_description": "Updated",
                "invalid_field": "not allowed",
            },
        },
    )

    assert response.status_code == 422

    body = response.get_json()

    assert body["error"]["code"] == "INVALID_STEP_DATA"
