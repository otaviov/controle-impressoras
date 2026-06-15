"""create maintenance_schedules table

Revision ID: b1c2d3e4f5a6
Revises: a605d5c373df
Create Date: 2026-06-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'a605d5c373df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('maintenance_schedules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('printer_id', sa.String(length=36), nullable=False),
        sa.Column('tipo', sa.String(length=20), nullable=False),
        sa.Column('intervalo_dias', sa.Integer(), nullable=True),
        sa.Column('intervalo_paginas', sa.Integer(), nullable=True),
        sa.Column('contador_inicial', sa.Integer(), nullable=True),
        sa.Column('contador_atual', sa.Integer(), nullable=True),
        sa.Column('ultima_geracao', sa.DateTime(), nullable=True),
        sa.Column('proxima_geracao', sa.DateTime(), nullable=True),
        sa.Column('proxima_meta_paginas', sa.Integer(), nullable=True),
        sa.Column('dias_aviso', sa.Integer(), nullable=False, server_default=sa.text('7')),
        sa.Column('observacao', sa.Text(), nullable=False, server_default=''),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['printer_id'], ['printers.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('maintenance_schedules', schema=None) as batch_op:
        batch_op.create_index('ix_maintenance_schedules_printer_id', ['printer_id'])


def downgrade() -> None:
    with op.batch_alter_table('maintenance_schedules', schema=None) as batch_op:
        batch_op.drop_index('ix_maintenance_schedules_printer_id')
    op.drop_table('maintenance_schedules')
