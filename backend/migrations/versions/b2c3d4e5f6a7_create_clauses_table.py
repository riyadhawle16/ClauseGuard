"""create_clauses_table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-22 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'clauses',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('document_id', sa.CHAR(36), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('clause_number', sa.Integer(), nullable=False),
        sa.Column('heading', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_clauses_document_id'), 'clauses', ['document_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_clauses_document_id'), table_name='clauses')
    op.drop_table('clauses')
