from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.schemas.customer_query import (
    CustomerQueryCreateSchema,
    CustomerQueryResponseSchema,
)
from app.services.customer_query_service import (
    CustomerNotFoundError,
    CustomerProjectMismatchError,
    ProjectNotFoundError,
    CustomerQueryNotFoundError,
    create_customer_query_transaction,
    get_customer_query_record,
    list_customer_query_records,
)


customer_query_bp = Blueprint(
    "customer_queries",
    __name__,
    url_prefix="/api/v1/customer-queries",
    description="Customer Query / Requirement APIs",
)


def _customer_query_response(customer_query):
    return {
        "id": customer_query.id,
        "project_id": customer_query.project_id,
        "customer_id": customer_query.customer_id,
        "qo_date": customer_query.qo_date,
        "remark": customer_query.remark,
        "created_at": customer_query.created_at,
        "updated_at": customer_query.updated_at,
        "items": [
            {
                "id": item.id,
                "material_name": item.material_name,
                "quantity": item.quantity,
            }
            for item in customer_query.items
        ],
    }


@customer_query_bp.post("")
@customer_query_bp.doc(security=[{"BearerAuth": []}])
@customer_query_bp.arguments(CustomerQueryCreateSchema)
@customer_query_bp.response(201, CustomerQueryResponseSchema)
@jwt_required()
def create(data):
    try:
        customer_query = create_customer_query_transaction(
            project_id=data["project_id"],
            customer_id=data["customer_id"],
            qo_date=data["qo_date"],
            remark=data.get("remark"),
            items=data["items"],
        )

        return _customer_query_response(customer_query), 201

    except ProjectNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except CustomerNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "CUSTOMER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except CustomerProjectMismatchError as exc:
        return {
            "success": False,
            "error": {
                "code": "CUSTOMER_PROJECT_MISMATCH",
                "message": str(exc),
            },
        }, 409
        
        

@customer_query_bp.get("")
@customer_query_bp.doc(security=[{"BearerAuth": []}])
@customer_query_bp.response(200, CustomerQueryResponseSchema(many=True))
@jwt_required()
def list_all():
    customer_queries = list_customer_query_records()

    return [
        _customer_query_response(customer_query)
        for customer_query in customer_queries
    ], 200
    
    
    
@customer_query_bp.get("/<int:customer_query_id>")
@customer_query_bp.doc(security=[{"BearerAuth": []}])
@customer_query_bp.response(200, CustomerQueryResponseSchema)
@jwt_required()
def get(customer_query_id):
    try:
        customer_query = get_customer_query_record(
            customer_query_id
        )
    except CustomerQueryNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "CUSTOMER_QUERY_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    return _customer_query_response(customer_query), 200