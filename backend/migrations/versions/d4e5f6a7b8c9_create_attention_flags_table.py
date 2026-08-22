"""create_attention_flags_table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-22 04:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'attention_flags',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('document_id', sa.CHAR(36), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('clause_id', sa.CHAR(36), sa.ForeignKey('clauses.id'), nullable=False),
        sa.Column('category', sa.String(length=60), nullable=False),
        sa.Column('category_name', sa.String(length=120), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('matched_text', sa.String(length=500), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='review'),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('detection_method', sa.String(length=20), nullable=False, server_default='rule'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_attention_flags_document_id', 'attention_flags', ['document_id'])


def downgrade() -> None:
    op.drop_index('ix_attention_flags_document_id', table_name='attention_flags')
    op.drop_table('attention_flags')
