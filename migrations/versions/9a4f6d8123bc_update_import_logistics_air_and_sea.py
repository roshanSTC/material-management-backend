"""update import logistics to support air and sea payloads

Revision ID: 9a4f6d8123bc
Revises: 0fd445b52e66
Create Date: 2026-09-08 11:58:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a4f6d8123bc'
down_revision = '0fd445b52e66'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('import_logistics', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('airway_bill_no', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('flight_no', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('bill_of_lading_no', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('vessel_name', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('voyage_no', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('port_of_loading', sa.String(length=255), nullable=True))
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=True)

    op.execute("UPDATE import_logistics SET date = logistics_date WHERE date IS NULL")
    op.execute("UPDATE import_logistics SET airway_bill_no = airway_bill_number WHERE airway_bill_no IS NULL")
    op.execute("UPDATE import_logistics SET flight_no = flight_number WHERE flight_no IS NULL")

    with op.batch_alter_table('import_logistics', schema=None) as batch_op:
        batch_op.alter_column('date', existing_type=sa.Date(), nullable=False)
        batch_op.drop_column('flight_number')
        batch_op.drop_column('airway_bill_number')
        batch_op.drop_column('logistics_date')


def downgrade():
    with op.batch_alter_table('import_logistics', schema=None) as batch_op:
        batch_op.add_column(sa.Column('logistics_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('airway_bill_number', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('flight_number', sa.String(length=100), nullable=True))

    op.execute("UPDATE import_logistics SET logistics_date = date WHERE logistics_date IS NULL")
    op.execute("UPDATE import_logistics SET airway_bill_number = airway_bill_no WHERE airway_bill_number IS NULL")
    op.execute("UPDATE import_logistics SET flight_number = flight_no WHERE flight_number IS NULL")

    with op.batch_alter_table('import_logistics', schema=None) as batch_op:
        batch_op.alter_column('logistics_date', existing_type=sa.Date(), nullable=False)
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column('port_of_loading')
        batch_op.drop_column('voyage_no')
        batch_op.drop_column('vessel_name')
        batch_op.drop_column('bill_of_lading_no')
        batch_op.drop_column('flight_no')
        batch_op.drop_column('airway_bill_no')
        batch_op.drop_column('date')

