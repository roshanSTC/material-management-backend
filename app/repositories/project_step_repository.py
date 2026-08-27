from app.extensions.database import db
from app.models import Project, ProjectStep


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_step(
    project_id: int,
    step_number: int,
) -> ProjectStep | None:
    return ProjectStep.query.filter_by(
        project_id=project_id,
        step_number=step_number,
    ).first()


def get_project_steps(project_id: int) -> list[ProjectStep]:
    return (
        ProjectStep.query
        .filter_by(project_id=project_id)
        .order_by(ProjectStep.step_number)
        .all()
    )


def add_step(step: ProjectStep) -> ProjectStep:
    db.session.add(step)
    return step