from app.extensions.database import db
from app.models import Customer, CustomerQuery, CustomerQueryItem, Project


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_customer(customer_id: int) -> Customer | None:
    return db.session.get(Customer, customer_id)


def create_customer_query(
    *,
    project_id: int,
    customer_id: int,
    qo_date,
    remark: str | None,
    items: list[dict],
) -> CustomerQuery:
    customer_query = CustomerQuery(
        project_id=project_id,
        customer_id=customer_id,
        qo_date=qo_date,
        remark=remark.strip() if remark else None,
    )

    for item_data in items:
        item = CustomerQueryItem(
            material_name=item_data["material_name"].strip(),
            quantity=item_data["quantity"],
        )

        customer_query.items.append(item)

    db.session.add(customer_query)

    return customer_query


def list_customer_queries() -> list[CustomerQuery]:
    return db.session.execute(
        db.select(CustomerQuery)
        .order_by(CustomerQuery.id.desc())
    ).scalars().all()


def get_customer_query(
    customer_query_id: int,
) -> CustomerQuery | None:
    return db.session.get(CustomerQuery, customer_query_id)