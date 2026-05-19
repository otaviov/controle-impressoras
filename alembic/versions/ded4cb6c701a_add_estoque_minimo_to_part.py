"""add_estoque_minimo_to_part

Revision ID: ded4cb6c701a
Revises: initial
Create Date: 2026-05-18 14:57:26.514563

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ded4cb6c701a'
down_revision: Union[str, Sequence[str], None] = 'initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('parts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('estoque_minimo', sa.Integer(), nullable=False, server_default=sa.text('1')))


def downgrade() -> None:
    with op.batch_alter_table('parts', schema=None) as batch_op:
        batch_op.drop_column('estoque_minimo')
