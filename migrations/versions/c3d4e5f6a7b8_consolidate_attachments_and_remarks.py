"""consolidate attachments and step_remarks into single unified tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a1
Create Date: 2026-10-17 17:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a1'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Update attachments table: add upload_key
    with op.batch_alter_table('attachments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('upload_key', sa.String(length=80), nullable=True))
        batch_op.create_index('idx_attachments_upload_key', ['upload_key'])

    # 2. Update step_remarks table: add step_id and user_name, update check constraint
    with op.batch_alter_table('step_remarks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('step_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('user_name', sa.String(length=100), nullable=True))
        batch_op.create_foreign_key(
            'fk_step_remarks_step_id',
            'project_steps',
            ['step_id'],
            ['id'],
            ondelete='CASCADE'
        )
        batch_op.create_index('idx_step_remarks_step_id', ['step_id'])
        batch_op.drop_constraint('ck_step_remarks_step_number', type_='check')
        batch_op.create_check_constraint('ck_step_remarks_step_number', 'step_number >= 1')

    # 3. Drop redundant tables
    op.drop_table('project_step_attachments')
    op.drop_table('project_step_remarks')


def downgrade():
    # 1. Re-create project_step_remarks
    op.create_table(
        'project_step_remarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('step_id', sa.Integer(), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_name', sa.String(length=100), nullable=True),
        sa.Column('remark', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['step_id'], ['project_steps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_project_step_remarks_step_id', 'project_step_remarks', ['step_id'])

    # 2. Re-create project_step_attachments
    op.create_table(
        'project_step_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('step_id', sa.Integer(), nullable=False),
        sa.Column('upload_key', sa.String(length=80), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['step_id'], ['project_steps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_project_step_attachments_step_id', 'project_step_attachments', ['step_id'])

    # 3. Revert step_remarks
    with op.batch_alter_table('step_remarks', schema=None) as batch_op:
        batch_op.drop_constraint('ck_step_remarks_step_number', type_='check')
        batch_op.create_check_constraint('ck_step_remarks_step_number', 'step_number >= 1 AND step_number <= 15')
        batch_op.drop_index('idx_step_remarks_step_id')
        batch_op.drop_constraint('fk_step_remarks_step_id', type_='foreignkey')
        batch_op.drop_column('user_name')
        batch_op.drop_column('step_id')

    # 4. Revert attachments
    with op.batch_alter_table('attachments', schema=None) as batch_op:
        batch_op.drop_index('idx_attachments_upload_key')
        batch_op.drop_column('upload_key')

