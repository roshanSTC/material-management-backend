"""convert attachments to generic entities

Revision ID: a8c099933008
Revises: a220212ca32e
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa


revision = "a8c099933008"
down_revision = "a220212ca32e"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

    # Restore customer_query_id
    with op.batch_alter_table(
        "attachments",
        schema=None,
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "customer_query_id",
                sa.Integer(),
                nullable=True,
            )
        )

    # Restore existing customer query relationships
    op.execute(
        """
        UPDATE attachments
        SET customer_query_id = entity_id
        WHERE entity_type = 'customer_query'
        """
    )

    with op.batch_alter_table(
        "attachments",
        schema=None,
    ) as batch_op:

        batch_op.alter_column(
            "customer_query_id",
            existing_type=sa.Integer(),
            nullable=False,
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

        batch_op.drop_index(
            "ix_attachments_entity",
        )

        batch_op.drop_index(
            "ix_attachments_entity_id",
        )

        batch_op.drop_index(
            "ix_attachments_entity_type",
        )

        batch_op.drop_column("entity_id")
        batch_op.drop_column("entity_type")