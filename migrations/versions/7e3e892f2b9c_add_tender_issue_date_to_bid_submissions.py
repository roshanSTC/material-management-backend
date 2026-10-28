"""add tender_issue_date to bid_submissions

Revision ID: 7e3e892f2b9c
Revises: d4e5f6a7b8c9
Create Date: 2026-10-28 11:12:12.879824

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e3e892f2b9c'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE bid_submissions ADD COLUMN IF NOT EXISTS tender_issue_date DATE;")


def downgrade():
    op.execute("ALTER TABLE bid_submissions DROP COLUMN IF EXISTS tender_issue_date;")
