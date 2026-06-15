"""refactor technician_specialties to use modelo instead of printer_id

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('technician_specialties')
    op.create_table('technician_specialties',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('technician_id', sa.Integer(), sa.ForeignKey('technicians.id'), nullable=False),
        sa.Column('modelo', sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('technician_specialties')
    op.create_table('technician_specialties',
        sa.Column('technician_id', sa.Integer(), nullable=False),
        sa.Column('printer_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['technician_id'], ['technicians.id'], ),
        sa.ForeignKeyConstraint(['printer_id'], ['printers.id'], ),
        sa.PrimaryKeyConstraint('technician_id', 'printer_id'),
    )
