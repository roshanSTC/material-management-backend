"""add step name to project steps

Revision ID: ff6c39a87bd3
Revises: bfacc4c67adf
Create Date: 2026-08-27 16:54:46.243665
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "ff6c39a87bd3"
down_revision = "bfacc4c67adf"
branch_labels = None
depends_on = None


STEP_NAMES = {
    1: "Customer Query to ST",
    2: "Request Quotation from Supplier",
    3: "Supplier's Quotation",
    4: "Cost Sheet Preparation",
    5: "Quotation to Customer",
    6: "Customer issues Tender",
    7: "S.T. submits Bid Documents",
    8: "Customer issues Purchase Order (PO)",
    9: "S.T. places Order Confirmation with Supplier",
    10: "Supplier raises Bill / Invoice",
    11: "Material delivered to India",
    12: "Customs Clearance",
    13: "S.T. delivers Material to Customer's Place with S.T. Billing",
    14: "Customer makes Payment to S.T.",
    15: "S.T. makes Payment to Partner / Supplier",
}


def upgrade():
    with op.batch_alter_table("project_steps", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "step_name",
                sa.String(length=255),
                nullable=True,
            )
        )

    step_names = {
        1: "Customer Query to ST",
        2: "Request Quotation from Supplier",
        3: "Supplier's Quotation",
        4: "Cost Sheet Preparation",
        5: "Quotation to Customer",
        6: "Customer issues Tender",
        7: "S.T. submits Bid Documents",
        8: "Customer issues Purchase Order (PO)",
        9: "S.T. places Order Confirmation with Supplier",
        10: "Supplier raises Bill / Invoice",
        11: "Material delivered to India",
        12: "Customs Clearance",
        13: "S.T. delivers Material to Customer's Place with S.T. Billing",
        14: "Customer makes Payment to S.T.",
        15: "S.T. makes Payment to Partner / Supplier",
    }

    for step_number, step_name in step_names.items():
        op.execute(
            sa.text(
                """
                UPDATE project_steps
                SET step_name = :step_name
                WHERE step_number = :step_number
                """
            ).bindparams(
                step_name=step_name,
                step_number=step_number,
            )
        )

    with op.batch_alter_table("project_steps", schema=None) as batch_op:
        batch_op.alter_column(
            "step_name",
            existing_type=sa.String(length=255),
            nullable=False,
        )
        
        
def downgrade():
    with op.batch_alter_table("project_steps", schema=None) as batch_op:
        batch_op.drop_constraint(
            "ck_project_step_status",
            type_="check",
        )

        batch_op.drop_constraint(
            "ck_project_step_number",
            type_="check",
        )

        batch_op.create_check_constraint(
            "ck_project_steps_step_number",
            "step_number >= 1 AND step_number <= 15",
        )

        batch_op.create_check_constraint(
            "ck_project_steps_status",
            "status::text = ANY (ARRAY['pending'::character varying, 'in_progress'::character varying, 'completed'::character varying]::text[])",
        )

        batch_op.drop_constraint(
            "uq_project_step_number",
            type_="unique",
        )

        batch_op.create_unique_constraint(
            "uq_project_steps_project_step",
            ["project_id", "step_number"],
        )

        batch_op.alter_column(
            "data",
            existing_type=postgresql.JSONB(astext_type=sa.Text()),
            type_=postgresql.JSON(astext_type=sa.Text()),
            existing_nullable=True,
        )

        batch_op.drop_column("step_name")