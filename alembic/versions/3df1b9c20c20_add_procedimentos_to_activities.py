"""add_procedimentos_to_activities

Revision ID: 3df1b9c20c20
Revises: 4113ad29b4c6
Create Date: 2026-06-05 17:15:07.351949

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3df1b9c20c20'
down_revision: Union[str, Sequence[str], None] = '4113ad29b4c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('procedimentos', sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.drop_column('procedimentos')
