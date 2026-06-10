"""add urgencia_prox_manutencao to printers

Revision ID: 2b3c4d5e6f7a
Revises: 1a2b3c4d5e6f
Create Date: 2026-06-09 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2b3c4d5e6f7a'
down_revision: Union[str, Sequence[str], None] = '1a2b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('printers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('urgencia_prox_manutencao', sa.String(20), nullable=False, server_default='Normal'))


def downgrade() -> None:
    with op.batch_alter_table('printers', schema=None) as batch_op:
        batch_op.drop_column('urgencia_prox_manutencao')
