from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.schemas.supplier import (
    SupplierCreateSchema,
    SupplierResponseSchema,
    SupplierUpdateSchema,
)
from app.services.supplier_service import (
    SupplierNotFoundError,
    create_supplier,
    get_supplier,
    list_suppliers,
    update_supplier,
)


supplier_bp = Blueprint(
    "suppliers",
    __name__,
    url_prefix="/api/v1/suppliers",
    description="Supplier Management APIs",
)


def _supplier_response(supplier):
    return {
        "id": supplier.id,
        "name": supplier.name,
        "email": supplier.email,
        "contact_number": supplier.contact_number,
        "address": supplier.address,
        "website_url": supplier.website_url,
        "created_at": supplier.created_at,
        "updated_at": supplier.updated_at,
    }


@supplier_bp.post("")
@supplier_bp.doc(security=[{"BearerAuth": []}])
@supplier_bp.arguments(SupplierCreateSchema)
@supplier_bp.response(201, SupplierResponseSchema)
@jwt_required()
def create(data):
    supplier = create_supplier(
        name=data["name"],
        email=data["email"],
        contact_number=data["contact_number"],
        address=data["address"],
        website_url=data.get("website_url"),
    )

    return _supplier_response(supplier), 201


@supplier_bp.get("")
@supplier_bp.doc(security=[{"BearerAuth": []}])
@supplier_bp.response(200, SupplierResponseSchema(many=True))
@jwt_required()
def list_all():
    suppliers = list_suppliers()

    return [
        _supplier_response(supplier)
        for supplier in suppliers
    ], 200


@supplier_bp.get("/<int:supplier_id>")
@supplier_bp.doc(security=[{"BearerAuth": []}])
@supplier_bp.response(200, SupplierResponseSchema)
@jwt_required()
def get(supplier_id):
    try:
        supplier = get_supplier(supplier_id)
    except SupplierNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "SUPPLIER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    return _supplier_response(supplier), 200


@supplier_bp.put("/<int:supplier_id>")
@supplier_bp.doc(security=[{"BearerAuth": []}])
@supplier_bp.arguments(SupplierUpdateSchema)
@supplier_bp.response(200, SupplierResponseSchema)
@jwt_required()
def update(data, supplier_id):
    try:
        supplier = update_supplier(
            supplier_id,
            name=data.get("name"),
            email=data.get("email"),
            contact_number=data.get("contact_number"),
            address=data.get("address"),
            website_url=data.get("website_url"),
        )
    except SupplierNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "SUPPLIER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    return _supplier_response(supplier), 200