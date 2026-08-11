"""add_marca_categoria_fornecedor_to_parts

Revision ID: f1a2b3c4d5e6
Revises: aa953b7eee9b
Create Date: 2026-07-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'aa953b7eee9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("PRAGMA foreign_keys = OFF")
    with op.batch_alter_table('parts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('marca', sa.String(100), server_default=''))
        batch_op.add_column(sa.Column('categoria', sa.String(100), server_default=''))
        batch_op.add_column(sa.Column('fornecedor', sa.String(150), server_default=''))
    op.execute("PRAGMA foreign_keys = ON")


def downgrade() -> None:
    op.execute("PRAGMA foreign_keys = OFF")
    with op.batch_alter_table('parts', schema=None) as batch_op:
        batch_op.drop_column('fornecedor')
        batch_op.drop_column('categoria')
        batch_op.drop_column('marca')
    op.execute("PRAGMA foreign_keys = ON")
