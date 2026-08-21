"""create_documents_table

Revision ID: a1b2c3d4e5f6
Revises: 278031280507
Create Date: 2026-08-22 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '278031280507'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'documents',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('user_id', sa.CHAR(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('processing_status', sa.String(length=20), nullable=False, server_default='uploaded'),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_documents_user_id'), 'documents', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_documents_user_id'), table_name='documents')
    op.drop_table('documents')
