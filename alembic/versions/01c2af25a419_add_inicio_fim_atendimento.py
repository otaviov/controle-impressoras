"""add_inicio_fim_atendimento

Revision ID: 01c2af25a419
Revises: 370e4ecbc5dc
Create Date: 2026-06-05 18:08:33.665588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '01c2af25a419'
down_revision: Union[str, Sequence[str], None] = '370e4ecbc5dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('inicio_atendimento', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('fim_atendimento', sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.drop_column('inicio_atendimento')
        batch_op.drop_column('fim_atendimento')
