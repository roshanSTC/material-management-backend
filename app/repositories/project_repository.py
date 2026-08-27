
from app.extensions.database import db
from app.models import Project


def create_project(
    *,
    project_title: str,
    customer_id: int,
    supplier_id: int,
) -> Project:
    project = Project(
        project_title=project_title,
        customer_id=customer_id,
        supplier_id=supplier_id,
    )

    db.session.add(project)
    db.session.flush()

    return project


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def list_projects() -> list[Project]:
    return db.session.execute(
        db.select(Project)
        .order_by(Project.id.desc())
    ).scalars().all()


def update_project(project: Project) -> Project:
    db.session.flush()

    return project

