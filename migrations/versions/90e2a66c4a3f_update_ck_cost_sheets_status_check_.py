"""update ck_cost_sheets_status check constraint

Revision ID: 90e2a66c4a3f
Revises: 27da2294294f
Create Date: 2026-10-28 15:27:45.687755

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '90e2a66c4a3f'
down_revision = '27da2294294f'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("ALTER TABLE cost_sheets DROP CONSTRAINT IF EXISTS ck_cost_sheets_status;")
        op.execute(
            """
            ALTER TABLE cost_sheets ADD CONSTRAINT ck_cost_sheets_status
            CHECK (status IN ('Draft', 'Approved', 'Archived', 'completed', 'in_progress', 'pending', 'draft', 'approved', 'archived'));
            """
        )
    else:
        with op.batch_alter_table('cost_sheets') as batch_op:
            batch_op.drop_constraint('ck_cost_sheets_status', type_='check')
            batch_op.create_check_constraint(
                'ck_cost_sheets_status',
                "status IN ('Draft', 'Approved', 'Archived', 'completed', 'in_progress', 'pending', 'draft', 'approved', 'archived')"
            )


def downgrade():
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("ALTER TABLE cost_sheets DROP CONSTRAINT IF EXISTS ck_cost_sheets_status;")
        op.execute(
            """
            ALTER TABLE cost_sheets ADD CONSTRAINT ck_cost_sheets_status
            CHECK (status IN ('Draft', 'Approved', 'Archived'));
            """
        )
    else:
        with op.batch_alter_table('cost_sheets') as batch_op:
            batch_op.drop_constraint('ck_cost_sheets_status', type_='check')
            batch_op.create_check_constraint(
                'ck_cost_sheets_status',
                "status IN ('Draft', 'Approved', 'Archived')"
            )
