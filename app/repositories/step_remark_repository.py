from app.extensions.database import db
from app.models.step_remark import StepRemark


def create_remark(
    *,
    project_id: int,
    step_number: int,
    remark: str,
    user_id: int | None = None,
) -> StepRemark:
    remark_obj = StepRemark(
        project_id=project_id,
        step_number=step_number,
        remark=remark,
        user_id=user_id,
    )
    db.session.add(remark_obj)
    db.session.flush()
    return remark_obj


def list_remarks_for_project(project_id: int) -> list[StepRemark]:
    return (
        db.session.execute(
            db.select(StepRemark)
            .where(StepRemark.project_id == project_id)
            .order_by(StepRemark.step_number.asc(), StepRemark.created_at.asc())
        )
        .scalars()
        .all()
    )


def list_remarks_for_step(project_id: int, step_number: int) -> list[StepRemark]:
    return (
        db.session.execute(
            db.select(StepRemark)
            .where(
                StepRemark.project_id == project_id,
                StepRemark.step_number == step_number,
            )
            .order_by(StepRemark.created_at.asc())
        )
        .scalars()
        .all()
    )


def get_remark(remark_id: int) -> StepRemark | None:
    return db.session.get(StepRemark, remark_id)


def delete_remark(remark_obj: StepRemark) -> None:
    db.session.delete(remark_obj)
    db.session.flush()

