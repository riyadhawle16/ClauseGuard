"""create_missing_info_flags_table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-22 05:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'missing_info_flags',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('document_id', sa.CHAR(36), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('category', sa.String(length=60), nullable=False),
        sa.Column('category_name', sa.String(length=120), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('evidence_clause_id', sa.CHAR(36), sa.ForeignKey('clauses.id'), nullable=True),
        sa.Column('evidence_page_number', sa.Integer(), nullable=True),
        sa.Column('detection_method', sa.String(length=20), nullable=False, server_default='RULE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_missing_info_flags_document_id', 'missing_info_flags', ['document_id'])


def downgrade() -> None:
    op.drop_index('ix_missing_info_flags_document_id', table_name='missing_info_flags')
    op.drop_table('missing_info_flags')
