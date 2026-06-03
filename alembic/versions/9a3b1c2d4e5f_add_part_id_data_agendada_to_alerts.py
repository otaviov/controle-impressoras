"""add_part_id_data_agendada_to_alerts

Revision ID: 9a3b1c2d4e5f
Revises: 0df5fd127c31
Create Date: 2026-06-03 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9a3b1c2d4e5f'
down_revision: Union[str, None] = '0df5fd127c31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('alerts') as batch_op:
        batch_op.alter_column('printer_id', existing_type=sa.String(36), nullable=True)
        batch_op.add_column(sa.Column('part_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('data_agendada', sa.DateTime(), nullable=True))
        batch_op.create_index('ix_alert_part_id', ['part_id'])
        batch_op.create_foreign_key('fk_alert_part_id', 'parts', ['part_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('alerts') as batch_op:
        batch_op.drop_constraint('fk_alert_part_id', type_='foreignkey')
        batch_op.drop_index('ix_alert_part_id')
        batch_op.drop_column('data_agendada')
        batch_op.drop_column('part_id')
        batch_op.alter_column('printer_id', existing_type=sa.String(36), existing_nullable=True, nullable=False)
