"""add_deleted_at_to_part_movements

Revision ID: aa953b7eee9b
Revises: b5f6a7c8d9e0
Create Date: 2026-07-15 17:12:43.424357

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa953b7eee9b'
down_revision: Union[str, Sequence[str], None] = 'b5f6a7c8d9e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('part_movements', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))

def downgrade() -> None:
    with op.batch_alter_table('part_movements', schema=None) as batch_op:
        batch_op.drop_column('deleted_at')
