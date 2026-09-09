"""update transport details schema

Revision ID: b2e519c83fa4
Revises: a1c49e72b38f
Create Date: 2026-09-09 10:48:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2e519c83fa4'
down_revision = 'a1c49e72b38f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('transport_details', schema=None) as batch_op:
        batch_op.add_column(sa.Column('transport_mode', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('lr_no', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('rr_no', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('awb_no', sa.String(length=100), nullable=True))

    op.execute("UPDATE transport_details SET transport_mode = transportation_mode WHERE transport_mode IS NULL AND transportation_mode IS NOT NULL")
    op.execute("UPDATE transport_details SET lr_no = lr_number WHERE lr_no IS NULL AND lr_number IS NOT NULL")
    op.execute("UPDATE transport_details SET date = transport_date WHERE date IS NULL AND transport_date IS NOT NULL")

    with op.batch_alter_table('transport_details', schema=None) as batch_op:
        batch_op.alter_column('transport_mode', existing_type=sa.String(length=50), nullable=False)
        batch_op.alter_column('date', existing_type=sa.Date(), nullable=False)
        batch_op.drop_column('transportation_mode')
        batch_op.drop_column('lr_number')
        batch_op.drop_column('transport_date')


def downgrade():
    with op.batch_alter_table('transport_details', schema=None) as batch_op:
        batch_op.add_column(sa.Column('transport_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('lr_number', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('transportation_mode', sa.String(length=100), nullable=True))

    op.execute("UPDATE transport_details SET transportation_mode = transport_mode WHERE transportation_mode IS NULL AND transport_mode IS NOT NULL")
    op.execute("UPDATE transport_details SET lr_number = lr_no WHERE lr_number IS NULL AND lr_no IS NOT NULL")
    op.execute("UPDATE transport_details SET transport_date = date WHERE transport_date IS NULL AND date IS NOT NULL")

    with op.batch_alter_table('transport_details', schema=None) as batch_op:
        batch_op.alter_column('transportation_mode', existing_type=sa.String(length=100), nullable=False)
        batch_op.alter_column('transport_date', existing_type=sa.Date(), nullable=False)
        batch_op.drop_column('awb_no')
        batch_op.drop_column('rr_no')
        batch_op.drop_column('date')
        batch_op.drop_column('lr_no')
        batch_op.drop_column('transport_mode')
