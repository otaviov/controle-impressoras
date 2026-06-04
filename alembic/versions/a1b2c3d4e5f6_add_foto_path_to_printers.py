"""add_foto_path_to_printers

Revision ID: a1b2c3d4e5f6
Revises: 9a3b1c2d4e5f
Create Date: 2026-06-04 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9a3b1c2d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('printers') as batch_op:
        batch_op.add_column(sa.Column('foto_path', sa.String(255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('printers') as batch_op:
        batch_op.drop_column('foto_path')
