"""convert customer query attachments to generic entities

Revision ID: 818b06b097f2
Revises: a220212ca32e
"""

from alembic import op
import sqlalchemy as sa


revision = "818b06b097f2"
down_revision = "a220212ca32e"
branch_labels = None
depends_on = None


def upgrade():

    # Add generic entity columns temporarily as nullable
    with op.batch_alter_table(
        "attachments",
        schema=None,
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "entity_type",
                sa.String(length=100),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "entity_id",
                sa.Integer(),
                nullable=True,
            )
        )

    # Convert existing customer-query attachments
    op.execute(
        """
        UPDATE attachments
        SET
            entity_type = 'customer_query',
            entity_id = customer_query_id
        WHERE customer_query_id IS NOT NULL
        """
    )

    # Make generic entity fields mandatory
    # and remove customer-query-specific fields.
    with op.batch_alter_table(
        "attachments",
        schema=None,
    ) as batch_op:

        batch_op.alter_column(
            "entity_type",
            existing_type=sa.String(length=100),
            nullable=False,
        )

        batch_op.alter_column(
            "entity_id",
            existing_type=sa.Integer(),
            nullable=False,
        )

        batch_op.create_index(
            "ix_attachments_entity_type",
            ["entity_type"],
            unique=False,
        )

        batch_op.create_index(
            "ix_attachments_entity_id",
            ["entity_id"],
            unique=False,
        )

        batch_op.create_index(
            "ix_attachments_entity",
            ["entity_type", "entity_id"],
            unique=False,
        )

        batch_op.drop_constraint(
            "fk_attachments_customer_query_id",
            type_="foreignkey",
        )

        batch_op.drop_index(
            "ix_attachments_customer_query_id",
        )

        batch_op.drop_column(
            "customer_query_id"
        )


def downgrade():

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

    # Restore customer-query relationships
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

        batch_op.drop_column(
            "entity_id"
        )

        batch_op.drop_column(
            "entity_type"
        )