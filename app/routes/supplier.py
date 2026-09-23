from flask import current_app, jsonify
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
    delete_supplier,
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
        "nickname": supplier.nickname,
        "email": supplier.email,
        "contact_number": supplier.contact_number,
        "address": supplier.address,
        "street": supplier.street,
        "area": supplier.area,
        "city": supplier.city,
        "state": supplier.state,
        "pincode": supplier.pincode,
        "country": supplier.country,
        "website_url": supplier.website_url,
        "pocs": [
            {
                "id": poc.id,
                "name": poc.name,
                "email": poc.email,
                "contact_number": poc.contact_number,
                "designation": poc.designation,
            }
            for poc in supplier.pocs
        ] if supplier.pocs else [],
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
        address=data.get("address"),
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


@supplier_bp.delete("/<int:supplier_id>")
@supplier_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete(supplier_id):
    try:
        delete_supplier(supplier_id)
        return jsonify({
            "success": True,
            "message": f"Supplier {supplier_id} deleted successfully.",
            "data": {
                "id": supplier_id,
            },
        }), 200
    except SupplierNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "SUPPLIER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404
    except Exception:
        current_app.logger.exception("Failed to delete supplier")
        return {
            "success": False,
            "error": {
                "code": "SUPPLIER_DELETE_FAILED",
                "message": "Failed to delete supplier.",
            },
        }, 500
