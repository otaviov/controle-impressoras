"""add ultima_revisao to printers

Revision ID: 1a2b3c4d5e6f
Revises: 01c2af25a419
Create Date: 2026-06-09 18:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '01c2af25a419'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('printers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ultima_revisao', sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('printers', schema=None) as batch_op:
        batch_op.drop_column('ultima_revisao')
