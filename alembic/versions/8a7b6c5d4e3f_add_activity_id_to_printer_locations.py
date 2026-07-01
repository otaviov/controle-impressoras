"""Add activity_id to printer_locations

Revision ID: 8a7b6c5d4e3f
Revises: 7899a6741eeb
Create Date: 2026-07-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8a7b6c5d4e3f'
down_revision: Union[str, None] = '7899a6741eeb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('printer_locations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('activity_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_printer_locations_activity', 'activities', ['activity_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('printer_locations', schema=None) as batch_op:
        batch_op.drop_constraint('fk_printer_locations_activity', type_='foreignkey')
        batch_op.drop_column('activity_id')
