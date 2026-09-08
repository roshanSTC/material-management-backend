"""update customs clearances table

Revision ID: e991b42fdaca
Revises: b8c4d2e135fa
Create Date: 2026-09-08 13:01:25.324274

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e991b42fdaca'
down_revision = 'b8c4d2e135fa'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('customs_clearances', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bill_of_entry_no', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('boe_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('customs_location', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('challan_no', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('transaction_ref_no', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('total_customs_amount', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.alter_column('bill_of_entry_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.create_index(batch_op.f('ix_customs_clearances_bill_of_entry_no'), ['bill_of_entry_no'], unique=False)

    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE customs_clearances
        SET customs_location = customs_location_port,
            challan_no = challan_number,
            transaction_ref_no = transaction_payment_reference
    """))

    with op.batch_alter_table('customs_clearances', schema=None) as batch_op:
        batch_op.drop_column('transaction_payment_reference')
        batch_op.drop_column('challan_number')
        batch_op.drop_column('customs_location_port')


def downgrade():
    with op.batch_alter_table('customs_clearances', schema=None) as batch_op:
        batch_op.add_column(sa.Column('customs_location_port', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('challan_number', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('transaction_payment_reference', sa.VARCHAR(length=255), autoincrement=False, nullable=True))

    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE customs_clearances
        SET customs_location_port = customs_location,
            challan_number = challan_no,
            transaction_payment_reference = transaction_ref_no
    """))

    with op.batch_alter_table('customs_clearances', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_customs_clearances_bill_of_entry_no'))
        batch_op.alter_column('bill_of_entry_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.drop_column('total_customs_amount')
        batch_op.drop_column('transaction_ref_no')
        batch_op.drop_column('challan_no')
        batch_op.drop_column('customs_location')
        batch_op.drop_column('boe_date')
        batch_op.drop_column('bill_of_entry_no')
