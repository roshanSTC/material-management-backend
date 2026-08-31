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
        "email": customer.email,
        "contact_number": customer.contact_number,
        "address": customer.address,
        "website_url": customer.website_url,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
    }


@customer_bp.post("")
@customer_bp.arguments(CustomerCreateSchema)
@customer_bp.response(201, CustomerResponseSchema)
@jwt_required()
def create(data):
    customer = create_customer(
        name=data["name"],
        email=data["email"],
        contact_number=data["contact_number"],
        address=data["address"],
        website_url=data.get("website_url"),
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
            email=data.get("email"),
            contact_number=data.get("contact_number"),
            address=data.get("address"),
            website_url=data.get("website_url"),
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