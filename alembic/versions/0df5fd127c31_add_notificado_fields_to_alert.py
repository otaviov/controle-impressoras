"""add_notificado_fields_to_alert

Revision ID: 0df5fd127c31
Revises: 43f9d2337797
Create Date: 2026-06-02 16:47:18.668008

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0df5fd127c31'
down_revision: Union[str, None] = '43f9d2337797'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('alerts') as batch_op:
        batch_op.add_column(sa.Column('notificado', sa.Boolean(), nullable=False, server_default=sa.text('0')))
        batch_op.add_column(sa.Column('notificado_em', sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('alerts') as batch_op:
        batch_op.drop_column('notificado_em')
        batch_op.drop_column('notificado')
