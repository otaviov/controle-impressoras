"""add indexes and increase ip_rede

Revision ID: d46315348779
Revises: ded4cb6c701a
Create Date: 2026-06-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd46315348779'
down_revision: Union[str, Sequence[str], None] = 'ded4cb6c701a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # increase ip_rede from 15 to 45
    with op.batch_alter_table('printers', schema=None) as batch_op:
        batch_op.alter_column('ip_rede',
               existing_type=sa.VARCHAR(length=15),
               type_=sa.String(length=45),
               existing_nullable=False,
               existing_server_default=sa.text("('')"))

    # fix status_atividade default
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.alter_column('status_atividade',
               existing_type=sa.VARCHAR(length=30),
               existing_server_default=sa.text("'concluida'"),
               nullable=False)

    # indexes
    op.create_index(op.f('ix_parts_codigo'), 'parts', ['codigo'], unique=False)
    op.create_index(op.f('ix_companies_cnpj'), 'companies', ['cnpj'], unique=False)
    op.create_index(op.f('ix_activities_kind'), 'activities', ['kind'], unique=False)
    op.create_index(op.f('ix_activities_numero_recibo'), 'activities', ['numero_recibo'], unique=False)
    op.create_index(op.f('ix_activities_status_atividade'), 'activities', ['status_atividade'], unique=False)
    op.create_index(op.f('ix_transfers_numero_os'), 'transfers', ['numero_os'], unique=False)
    op.create_index(op.f('ix_transfers_tipo'), 'transfers', ['tipo'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_transfers_tipo'), table_name='transfers')
    op.drop_index(op.f('ix_transfers_numero_os'), table_name='transfers')
    op.drop_index(op.f('ix_activities_status_atividade'), table_name='activities')
    op.drop_index(op.f('ix_activities_numero_recibo'), table_name='activities')
    op.drop_index(op.f('ix_activities_kind'), table_name='activities')
    op.drop_index(op.f('ix_companies_cnpj'), table_name='companies')
    op.drop_index(op.f('ix_parts_codigo'), table_name='parts')

    with op.batch_alter_table('printers', schema=None) as batch_op:
        batch_op.alter_column('ip_rede',
               existing_type=sa.String(length=45),
               type_=sa.VARCHAR(length=15),
               existing_nullable=False,
               existing_server_default=sa.text("('')"))
