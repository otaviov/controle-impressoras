"""create technician_specialties table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-15 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('technician_specialties',
        sa.Column('technician_id', sa.Integer(), nullable=False),
        sa.Column('printer_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['technician_id'], ['technicians.id'], ),
        sa.ForeignKeyConstraint(['printer_id'], ['printers.id'], ),
        sa.PrimaryKeyConstraint('technician_id', 'printer_id'),
    )


def downgrade() -> None:
    op.drop_table('technician_specialties')
