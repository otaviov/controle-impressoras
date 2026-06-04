"""add_printer_locations

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-04 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('printer_locations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('printer_id', sa.String(36), nullable=False),
        sa.Column('local', sa.String(120), nullable=False),
        sa.Column('data', sa.DateTime(), nullable=True),
        sa.Column('observacao', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['printer_id'], ['printers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_printer_locations_printer_id', 'printer_locations', ['printer_id'])


def downgrade() -> None:
    op.drop_index('ix_printer_locations_printer_id', table_name='printer_locations')
    op.drop_table('printer_locations')
