"""add part_movements, part_reservations, purchase_requisitions

Revision ID: 7899a6741eeb
Revises: f6a7b8c9d0e1
Create Date: 2026-06-15 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7899a6741eeb'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('part_movements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('part_id', sa.Integer(), sa.ForeignKey('parts.id'), nullable=False, index=True),
        sa.Column('activity_id', sa.Integer(), sa.ForeignKey('activities.id'), nullable=True, index=True),
        sa.Column('tipo', sa.String(length=30), nullable=False),
        sa.Column('quantidade', sa.Integer(), nullable=False),
        sa.Column('saldo_anterior', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('saldo_posterior', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('observacao', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('part_reservations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('part_id', sa.Integer(), sa.ForeignKey('parts.id'), nullable=False, index=True),
        sa.Column('activity_id', sa.Integer(), sa.ForeignKey('activities.id'), nullable=False, index=True),
        sa.Column('quantidade', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='reservada'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('purchase_requisitions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('part_id', sa.Integer(), sa.ForeignKey('parts.id'), nullable=False, index=True),
        sa.Column('quantidade_sugerida', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pendente'),
        sa.Column('observacao', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('purchase_requisitions')
    op.drop_table('part_reservations')
    op.drop_table('part_movements')
