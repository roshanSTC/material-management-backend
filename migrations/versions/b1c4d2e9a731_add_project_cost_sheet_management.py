"""add project cost sheet management

Revision ID: b1c4d2e9a731
Revises: a220212ca32e
Create Date: 2026-09-02
"""
from alembic import op
import sqlalchemy as sa


revision = "b1c4d2e9a731"
down_revision = "a220212ca32e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cost_sheets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("global_params", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('Draft', 'Approved', 'Archived')",
            name="ck_cost_sheets_status",
        ),
        sa.CheckConstraint(
            "version_number > 0",
            name="ck_cost_sheets_version_number",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "version_number",
            name="uq_cost_sheets_project_version",
        ),
    )
    with op.batch_alter_table("cost_sheets", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_cost_sheets_project_id"), ["project_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_cost_sheets_created_by"), ["created_by"], unique=False)

    op.create_table(
        "cost_sheet_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cost_sheet_id", sa.Integer(), nullable=False),
        sa.Column("item_code", sa.String(length=100), nullable=False),
        sa.Column("item_description", sa.String(length=500), nullable=False),
        sa.Column("price_per_unit_eur", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=3), nullable=False),
        sa.Column("customs_duty_rate", sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "price_per_unit_eur > 0",
            name="ck_cost_sheet_items_positive_price",
        ),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_cost_sheet_items_positive_quantity",
        ),
        sa.CheckConstraint(
            "customs_duty_rate IS NULL OR customs_duty_rate BETWEEN 0 AND 1",
            name="ck_cost_sheet_items_duty_rate",
        ),
        sa.ForeignKeyConstraint(["cost_sheet_id"], ["cost_sheets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("cost_sheet_items", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_cost_sheet_items_cost_sheet_id"),
            ["cost_sheet_id"],
            unique=False,
        )

    op.create_table(
        "item_price_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cost_sheet_item_id", sa.Integer(), nullable=False),
        sa.Column("old_price_eur", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("new_price_eur", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("supplier_name", sa.String(length=255), nullable=False),
        sa.Column("change_reason", sa.Text(), nullable=False),
        sa.Column("changed_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "old_price_eur > 0 AND new_price_eur > 0",
            name="ck_item_price_history_positive_prices",
        ),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["cost_sheet_item_id"], ["cost_sheet_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("item_price_history", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_item_price_history_cost_sheet_item_id"),
            ["cost_sheet_item_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_item_price_history_changed_by"),
            ["changed_by"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("item_price_history", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_item_price_history_changed_by"))
        batch_op.drop_index(batch_op.f("ix_item_price_history_cost_sheet_item_id"))
    op.drop_table("item_price_history")

    with op.batch_alter_table("cost_sheet_items", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_cost_sheet_items_cost_sheet_id"))
    op.drop_table("cost_sheet_items")

    with op.batch_alter_table("cost_sheets", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_cost_sheets_created_by"))
        batch_op.drop_index(batch_op.f("ix_cost_sheets_project_id"))
    op.drop_table("cost_sheets")
