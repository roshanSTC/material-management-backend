from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models import Customer, CustomerQuery, CustomerQueryItem, Project


from app.utils.remark_utils import normalize_remark_for_db


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_customer(customer_id: int) -> Customer | None:
    return db.session.get(Customer, customer_id)


def create_customer_query(
    *,
    project_id: int,
    customer_id: int | None = None,
    customer_name: str | None = None,
    query_date,
    remark: str | None,
    items: list[dict],
) -> CustomerQuery:
    customer_query = CustomerQuery(
        project_id=project_id,
        customer_id=customer_id,
        customer_name=customer_name.strip() if isinstance(customer_name, str) and customer_name.strip() else None,
        query_date=query_date,
        remark=normalize_remark_for_db(remark),
    )

    for idx, item_data in enumerate(items, start=1):
        item = CustomerQueryItem(
            sr_no=item_data.get("sr_no") if item_data.get("sr_no") is not None else idx,
            description=str(item_data["description"]).strip(),
            quantity=item_data["quantity"],
        )

        customer_query.items.append(item)

    db.session.add(customer_query)

    return customer_query


def list_customer_queries(
    *,
    project_id: int | None = None,
    customer_id: int | None = None,
) -> list[CustomerQuery]:
    statement = db.select(CustomerQuery)
    if project_id is not None:
        statement = statement.where(CustomerQuery.project_id == project_id)
    if customer_id is not None:
        statement = statement.where(CustomerQuery.customer_id == customer_id)

    return db.session.execute(
        statement.order_by(CustomerQuery.id.desc())
    ).scalars().all()


def get_customer_query(
    customer_query_id: int,
) -> CustomerQuery | None:
    return db.session.get(CustomerQuery, customer_query_id)


def get_latest_customer_query_for_project(
    project_id: int,
) -> CustomerQuery | None:
    return db.session.execute(
        db.select(CustomerQuery)
        .options(selectinload(CustomerQuery.items))
        .where(CustomerQuery.project_id == project_id)
        .order_by(CustomerQuery.id.desc())
    ).scalars().first()