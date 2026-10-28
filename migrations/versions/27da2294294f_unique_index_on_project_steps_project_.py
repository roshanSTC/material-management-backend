"""unique index on project steps project id and form code

Revision ID: 27da2294294f
Revises: a999d7255390
Create Date: 2026-10-28 14:30:30.432797

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '27da2294294f'
down_revision = 'a999d7255390'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Delete any duplicate steps per (project_id, form_code), keeping lowest id
    if is_postgres:
        op.execute(
            """
            DELETE FROM project_steps
            WHERE id IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (PARTITION BY project_id, form_code ORDER BY id ASC) as rnum
                    FROM project_steps
                    WHERE form_code IS NOT NULL
                ) t WHERE t.rnum > 1
            );
            """
        )
        op.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_project_steps_project_form_code
            ON project_steps (project_id, form_code)
            WHERE form_code IS NOT NULL;
            """
        )
    else:
        op.execute(
            """
            DELETE FROM project_steps
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM project_steps
                WHERE form_code IS NOT NULL
                GROUP BY project_id, form_code
            ) AND form_code IS NOT NULL;
            """
        )
        op.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_project_steps_project_form_code
            ON project_steps (project_id, form_code)
            WHERE form_code IS NOT NULL;
            """
        )


def downgrade():
    op.execute("DROP INDEX IF EXISTS uq_project_steps_project_form_code;")
