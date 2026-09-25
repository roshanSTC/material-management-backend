from flask import current_app, jsonify
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.schemas.customer import (
    CustomerCreateSchema,
    CustomerResponseSchema,
    CustomerUpdateSchema,
)
from app.services.customer_service import (
    CustomerNotFoundError,
    create_customer,
    delete_customer,
    get_customer,
    list_customers,
    update_customer,
)


customer_bp = Blueprint(
    "customers",
    __name__,
    url_prefix="/api/v1/customers",
    description="Customer Management APIs",
)


def _customer_response(customer):
    return {
        "id": customer.id,
        "name": customer.name,
        "nickname": customer.nickname,
        "email": customer.email,
        "contact_number": customer.contact_number,
        "street": customer.street,
        "area": customer.area,
        "city": customer.city,
        "state": customer.state,
        "pincode": customer.pincode,
        "country": customer.country,
        "pocs": [
            {
                "id": poc.id,
                "name": poc.name,
                "email": poc.email,
                "contact_number": poc.contact_number,
                "designation": poc.designation,
            }
            for poc in customer.pocs
        ] if customer.pocs else [],
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
    }


@customer_bp.post("")
@customer_bp.doc(security=[{"BearerAuth": []}])
@customer_bp.arguments(CustomerCreateSchema)
@customer_bp.response(201, CustomerResponseSchema)
@jwt_required()
def create(data):
    customer = create_customer(
        name=data["name"],
        nickname=data.get("nickname"),
        street=data.get("street"),
        area=data.get("area"),
        city=data.get("city"),
        state=data.get("state"),
        pincode=data.get("pincode"),
        country=data.get("country"),
        pocs=data.get("pocs"),
        email=data.get("email"),
        contact_number=data.get("contact_number"),
    )

    return _customer_response(customer), 201


@customer_bp.get("")
@customer_bp.doc(security=[{"BearerAuth": []}])
@customer_bp.response(200, CustomerResponseSchema(many=True))
@jwt_required()
def list_all():
    customers = list_customers()

    return [
        _customer_response(customer)
        for customer in customers
    ], 200


@customer_bp.get("/<int:customer_id>")
@customer_bp.doc(security=[{"BearerAuth": []}])
@customer_bp.response(200, CustomerResponseSchema)
@jwt_required()
def get(customer_id):
    try:
        customer = get_customer(customer_id)
    except CustomerNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "CUSTOMER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    return _customer_response(customer), 200


@customer_bp.put("/<int:customer_id>")
@customer_bp.doc(security=[{"BearerAuth": []}])
@customer_bp.arguments(CustomerUpdateSchema)
@customer_bp.response(200, CustomerResponseSchema)
@jwt_required()
def update(data, customer_id):
    try:
        customer = update_customer(
            customer_id,
            name=data.get("name"),
            nickname=data.get("nickname"),
            street=data.get("street"),
            area=data.get("area"),
            city=data.get("city"),
            state=data.get("state"),
            pincode=data.get("pincode"),
            country=data.get("country"),
            pocs=data.get("pocs"),
            email=data.get("email"),
            contact_number=data.get("contact_number"),
        )
    except CustomerNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "CUSTOMER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    return _customer_response(customer), 200


@customer_bp.delete("/<int:customer_id>")
@customer_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete(customer_id):
    try:
        delete_customer(customer_id)
        return jsonify({
            "success": True,
            "message": f"Customer {customer_id} deleted successfully.",
            "data": {
                "id": customer_id,
            },
        }), 200
    except CustomerNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "CUSTOMER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404
    except Exception:
        current_app.logger.exception("Failed to delete customer")
        return {
            "success": False,
            "error": {
                "code": "CUSTOMER_DELETE_FAILED",
                "message": "Failed to delete customer.",
            },
        }, 500
