"""update bills of entry table to match payload

Revision ID: b8c4d2e135fa
Revises: 9a4f6d8123bc
Create Date: 2026-09-08 12:31:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8c4d2e135fa'
down_revision = '9a4f6d8123bc'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('bills_of_entry', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bill_of_entry_no', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('total_duty', sa.Numeric(precision=18, scale=2), nullable=True))

    op.execute("UPDATE bills_of_entry SET bill_of_entry_no = bill_of_entry_number WHERE bill_of_entry_no IS NULL")
    op.execute("UPDATE bills_of_entry SET date = entry_date WHERE date IS NULL")

    with op.batch_alter_table('bills_of_entry', schema=None) as batch_op:
        batch_op.alter_column('bill_of_entry_no', existing_type=sa.String(length=100), nullable=False)
        batch_op.alter_column('date', existing_type=sa.Date(), nullable=False)
        batch_op.drop_column('bill_of_entry_number')
        batch_op.drop_column('entry_date')


def downgrade():
    with op.batch_alter_table('bills_of_entry', schema=None) as batch_op:
        batch_op.add_column(sa.Column('entry_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('bill_of_entry_number', sa.String(length=100), nullable=True))

    op.execute("UPDATE bills_of_entry SET bill_of_entry_number = bill_of_entry_no WHERE bill_of_entry_number IS NULL")
    op.execute("UPDATE bills_of_entry SET entry_date = date WHERE entry_date IS NULL")

    with op.batch_alter_table('bills_of_entry', schema=None) as batch_op:
        batch_op.alter_column('entry_date', existing_type=sa.Date(), nullable=False)
        batch_op.alter_column('bill_of_entry_number', existing_type=sa.String(length=100), nullable=False)
        batch_op.drop_column('total_duty')
        batch_op.drop_column('date')
        batch_op.drop_column('bill_of_entry_no')

