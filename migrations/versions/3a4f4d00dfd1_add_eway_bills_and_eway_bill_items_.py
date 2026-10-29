"""add eway_bills and eway_bill_items tables

Revision ID: 3a4f4d00dfd1
Revises: 6d4bfaaec9ad
Create Date: 2026-10-29 15:39:49.575296

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a4f4d00dfd1'
down_revision = '6d4bfaaec9ad'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'eway_bills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('eway_bill_no', sa.String(length=100), nullable=True),
        sa.Column('eway_bill_date', sa.Date(), nullable=True),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('document_no', sa.String(length=100), nullable=True),
        sa.Column('document_date', sa.Date(), nullable=True),
        sa.Column('value', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('place_of_dispatch', sa.String(length=255), nullable=True),
        sa.Column('place_of_delivery', sa.String(length=255), nullable=True),
        sa.Column('transporter', sa.String(length=255), nullable=True),
        sa.Column('mode', sa.String(length=50), nullable=True),
        sa.Column('vehicle_trans_doc_no', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='completed'),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('eway_bills', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_eway_bills_project_id'), ['project_id'], unique=False)

    op.create_table(
        'eway_bill_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('eway_bill_id', sa.Integer(), nullable=False),
        sa.Column('sr_no', sa.Integer(), nullable=True),
        sa.Column('material_name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hsn_sac', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=18, scale=3), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['eway_bill_id'], ['eway_bills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('eway_bill_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_eway_bill_items_eway_bill_id'), ['eway_bill_id'], unique=False)


def downgrade():
    with op.batch_alter_table('eway_bill_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_eway_bill_items_eway_bill_id'))
    op.drop_table('eway_bill_items')

    with op.batch_alter_table('eway_bills', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_eway_bills_project_id'))
    op.drop_table('eway_bills')
