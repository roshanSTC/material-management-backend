"""seed forms 32, 33, 34 in form_definitions

Revision ID: a1b2c3d4e5f6
Revises: 949a7f5b5e23
Create Date: 2026-11-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '949a7f5b5e23'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO form_definitions (id, form_code, name, category, phase_id, icon, description, has_table, is_active, created_at)
        VALUES 
          (32, 'FORM_32_EWAY_BILL', 'E-Way Bill', 'Logistics & Customs', 'phase-3', 'pi pi-truck', 'Electronic waybill for transport of goods, route, and vehicle dispatch details', true, true, NOW()),
          (33, 'FORM_33_STE', 'Single Tender Enquiry (STE)', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-briefcase', 'Single Tender Enquiry (STE) terms, tender fee, EMD, schedule, and items', true, true, NOW()),
          (34, 'FORM_34_BID_DOC_STE', 'Bid Document for STE', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-book', 'Bid Document for Single Tender Enquiry (STE), terms, corrigendum, items, and values', true, true, NOW())
        ON CONFLICT (id) DO UPDATE SET 
          form_code = EXCLUDED.form_code,
          name = EXCLUDED.name,
          category = EXCLUDED.category,
          phase_id = EXCLUDED.phase_id,
          icon = EXCLUDED.icon,
          description = EXCLUDED.description,
          has_table = EXCLUDED.has_table,
          is_active = EXCLUDED.is_active;
    """)
    op.execute("SELECT setval('form_definitions_id_seq', (SELECT MAX(id) FROM form_definitions));")


def downgrade():
    op.execute("DELETE FROM form_definitions WHERE id IN (32, 33, 34);")
