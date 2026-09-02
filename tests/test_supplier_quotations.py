import json

from app.extensions.database import db
from app.models import Supplier


def _headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}


def _payload(project_id, supplier_id):
    return {
        "project_id": project_id,
        "supplier_id": supplier_id,
        "quotation_number": " SQ-2026-001 ",
        "quotation_date": "2026-09-02",
        "quotation_value": "125000.50",
        "validity": "30 days",
        "incoterms": "CIF",
        "payment_terms": "50% advance",
        "delivery_period": "4 weeks",
        "remark": "Initial quotation",
        "items": [
            {
                "material_name": " Stainless Steel Pipe ",
                "quantity": "10.000",
            }
        ],
    }


def _multipart(payload):
    return {"data": json.dumps(payload)}


def test_create_and_get_supplier_quotation(
    client,
    access_token,
    project,
):
    response = client.post(
        "/api/v1/supplier-quotations",
        headers=_headers(access_token),
        data=_multipart(_payload(project.id, project.supplier_id)),
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["project_id"] == project.id
    assert body["supplier_id"] == project.supplier_id
    assert body["quotation_number"] == "SQ-2026-001"
    assert body["quotation_value"] == "125000.50"
    assert body["items"] == [
        {
            "id": body["items"][0]["id"],
            "material_name": "Stainless Steel Pipe",
            "quantity": "10.000",
        }
    ]
    assert body["attachments"] == []

    get_response = client.get(
        f"/api/v1/supplier-quotations/{body['id']}",
        headers=_headers(access_token),
    )
    assert get_response.status_code == 200
    assert get_response.get_json()["id"] == body["id"]


def test_list_supplier_quotations_supports_filters(
    client,
    access_token,
    project,
):
    client.post(
        "/api/v1/supplier-quotations",
        headers=_headers(access_token),
        data=_multipart(_payload(project.id, project.supplier_id)),
    )

    response = client.get(
        f"/api/v1/supplier-quotations?project_id={project.id}",
        headers=_headers(access_token),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert len(body) == 1
    assert body[0]["project_id"] == project.id


def test_patch_supplier_quotation_only_changes_supplied_fields(
    client,
    access_token,
    project,
):
    create_response = client.post(
        "/api/v1/supplier-quotations",
        headers=_headers(access_token),
        data=_multipart(_payload(project.id, project.supplier_id)),
    )
    quotation_id = create_response.get_json()["id"]

    response = client.patch(
        f"/api/v1/supplier-quotations/{quotation_id}",
        headers=_headers(access_token),
        data=_multipart(
            {
                "quotation_value": "130000.00",
                "items": [
                    {"material_name": "Updated Pipe", "quantity": "12.500"}
                ],
            }
        ),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["quotation_number"] == "SQ-2026-001"
    assert body["quotation_value"] == "130000.00"
    assert body["items"][0]["material_name"] == "Updated Pipe"
    assert body["items"][0]["quantity"] == "12.500"


def test_create_rejects_supplier_from_another_project(
    client,
    access_token,
    project,
):
    supplier = Supplier(
        name="Unrelated Supplier",
        email="unrelated@example.com",
        contact_number="7777777777",
        address="Other Address",
    )
    db.session.add(supplier)
    db.session.commit()

    response = client.post(
        "/api/v1/supplier-quotations",
        headers=_headers(access_token),
        data=_multipart(_payload(project.id, supplier.id)),
    )

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "SUPPLIER_PROJECT_MISMATCH"


def test_create_rejects_invalid_payload_and_requires_authentication(
    client,
    access_token,
    project,
):
    unauthorized_response = client.post(
        "/api/v1/supplier-quotations",
        data=_multipart(_payload(project.id, project.supplier_id)),
    )
    assert unauthorized_response.status_code == 401

    payload = _payload(project.id, project.supplier_id)
    payload["quotation_number"] = "   "
    payload["items"] = []
    invalid_response = client.post(
        "/api/v1/supplier-quotations",
        headers=_headers(access_token),
        data=_multipart(payload),
    )
    assert invalid_response.status_code == 422
    assert invalid_response.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_get_and_patch_unknown_supplier_quotation_return_404(
    client,
    access_token,
):
    get_response = client.get(
        "/api/v1/supplier-quotations/999999",
        headers=_headers(access_token),
    )
    assert get_response.status_code == 404

    patch_response = client.patch(
        "/api/v1/supplier-quotations/999999",
        headers=_headers(access_token),
        data=_multipart({"remark": "Does not exist"}),
    )
    assert patch_response.status_code == 404
    assert patch_response.get_json()["error"]["code"] == "SUPPLIER_QUOTATION_NOT_FOUND"
