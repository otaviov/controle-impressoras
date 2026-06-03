"""add deleted_at columns for soft delete

Revision ID: 43f9d2337797
Revises: 860330a5ed5a
Create Date: 2026-06-02 16:02:04.880542

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '43f9d2337797'
down_revision: Union[str, Sequence[str], None] = '860330a5ed5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABELAS = ["printers", "activities", "companies", "parts", "technicians", "alerts", "transfers", "users"]


def upgrade() -> None:
    for tabela in TABELAS:
        with op.batch_alter_table(tabela, schema=None) as batch_op:
            batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    for tabela in TABELAS:
        with op.batch_alter_table(tabela, schema=None) as batch_op:
            batch_op.drop_column("deleted_at")
