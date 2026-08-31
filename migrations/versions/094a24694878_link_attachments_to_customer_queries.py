"""link attachments to customer queries

Revision ID: 094a24694878
Revises: 74681f9a58fb
Create Date: 2026-08-31 17:30:51.938488

"""

from alembic import op
import sqlalchemy as sa


revision = "094a24694878"
down_revision = "74681f9a58fb"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        "attachments",
        schema=None,
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "customer_query_id",
                sa.Integer(),
                nullable=False,
            )
        )

        batch_op.drop_index(
            "ix_attachments_entity_id"
        )

        batch_op.create_index(
            "ix_attachments_customer_query_id",
            ["customer_query_id"],
            unique=False,
        )

        batch_op.create_foreign_key(
            "fk_attachments_customer_query_id",
            "customer_queries",
            ["customer_query_id"],
            ["id"],
        )

        batch_op.drop_column("project_id")
        batch_op.drop_column("step_number")


def downgrade():
    with op.batch_alter_table(
        "attachments",
        schema=None,
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "project_id",
                sa.Integer(),
                nullable=False,
            )
        )

        batch_op.add_column(
            sa.Column(
                "step_number",
                sa.Integer(),
                nullable=False,
            )
        )

        batch_op.drop_constraint(
            "fk_attachments_customer_query_id",
            type_="foreignkey",
        )

        batch_op.drop_index(
            "ix_attachments_customer_query_id"
        )

        batch_op.create_index(
            "ix_attachments_entity_id",
            ["project_id"],
            unique=False,
        )

        batch_op.drop_column("customer_query_id")