"""add_responsavel_to_activities

Revision ID: 4113ad29b4c6
Revises: b2c3d4e5f6a7
Create Date: 2026-06-05 16:20:56.050336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4113ad29b4c6'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('responsavel', sa.String(length=120), nullable=False, server_default=""))


def downgrade() -> None:
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.drop_column('responsavel')
