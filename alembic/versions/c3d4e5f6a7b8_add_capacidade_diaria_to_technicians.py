"""add capacidade_diaria to technicians

Revision ID: c3d4e5f6a7b8
Revises: b1c2d3e4f5a6
Create Date: 2026-06-15 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('technicians', schema=None) as batch_op:
        batch_op.add_column(sa.Column('capacidade_diaria', sa.Integer(), nullable=False, server_default=sa.text('5')))


def downgrade() -> None:
    with op.batch_alter_table('technicians', schema=None) as batch_op:
        batch_op.drop_column('capacidade_diaria')
