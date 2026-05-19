"""initial_schema

Revision ID: initial
Revises:
Create Date: 2026-05-18
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
