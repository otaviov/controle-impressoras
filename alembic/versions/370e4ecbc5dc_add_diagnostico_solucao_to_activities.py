"""add_diagnostico_solucao_to_activities

Revision ID: 370e4ecbc5dc
Revises: e2ea9a0e5059
Create Date: 2026-06-05 18:04:38.775529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '370e4ecbc5dc'
down_revision: Union[str, Sequence[str], None] = 'e2ea9a0e5059'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('diagnostico_tecnico', sa.Text(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column('solucao_aplicada', sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.drop_column('diagnostico_tecnico')
        batch_op.drop_column('solucao_aplicada')
