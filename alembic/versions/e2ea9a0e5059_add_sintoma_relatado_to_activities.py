"""add_sintoma_relatado_to_activities

Revision ID: e2ea9a0e5059
Revises: 3df1b9c20c20
Create Date: 2026-06-05 17:42:45.220479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2ea9a0e5059'
down_revision: Union[str, Sequence[str], None] = '3df1b9c20c20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sintoma_relatado', sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.drop_column('sintoma_relatado')
