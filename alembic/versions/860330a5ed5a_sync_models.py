"""sync models with DB

Revision ID: 860330a5ed5a
Revises: d46315348779
Create Date: 2026-06-01 11:24:43.623550

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '860330a5ed5a'
down_revision: Union[str, Sequence[str], None] = 'd46315348779'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    # Fix index names to match model __table_args__
    op.drop_index('ix_parts_codigo', table_name='parts')
    op.create_index('ix_part_codigo', 'parts', ['codigo'], unique=False)

    op.drop_index('ix_companies_cnpj', table_name='companies')
    op.create_index('ix_company_cnpj', 'companies', ['cnpj'], unique=False)

    op.drop_index('ix_transfers_numero_os', table_name='transfers')
    op.create_index('ix_transfer_numero_os', 'transfers', ['numero_os'], unique=False)

    op.drop_index('ix_transfers_tipo', table_name='transfers')
    op.create_index('ix_transfer_tipo', 'transfers', ['tipo'], unique=False)

    op.drop_index('ix_users_username', table_name='users')
    op.create_index('ix_user_username', 'users', ['username'], unique=False)

    # Add missing alert index
    op.create_index('ix_alerts_printer_id', 'alerts', ['printer_id'], unique=False)

    # Cleanup leftover temp table from failed migration
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_alerts")

    # Users: drop empresa_id, add email unique constraint
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('empresa_id')
        batch_op.create_unique_constraint('uq_users_email', ['email'])

    # Printers: tipo VARCHAR(50)->80, add patrimony unique, drop old columns
    with op.batch_alter_table('printers', schema=None) as batch_op:
        batch_op.alter_column('patrimonio',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=80),
               existing_nullable=False)
        batch_op.create_unique_constraint('uq_printers_patrimonio', ['patrimonio'])
        batch_op.drop_column('tecnico_revisao')
        batch_op.drop_column('ultima_revisao_data')

    # Alerts: titulo VARCHAR(150)->200
    with op.batch_alter_table('alerts', schema=None) as batch_op:
        batch_op.alter_column('titulo',
               existing_type=sa.VARCHAR(length=150),
               type_=sa.String(length=200),
               existing_nullable=False)

    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table('alerts', schema=None) as batch_op:
        batch_op.alter_column('titulo',
               existing_type=sa.String(length=200),
               type_=sa.VARCHAR(length=150),
               existing_nullable=False)

    with op.batch_alter_table('printers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ultima_revisao_data', sa.DATETIME(), nullable=True))
        batch_op.add_column(sa.Column('tecnico_revisao', sa.TEXT(), nullable=True))
        batch_op.drop_constraint('uq_printers_patrimonio', type_='unique')
        batch_op.alter_column('patrimonio',
               existing_type=sa.String(length=80),
               type_=sa.VARCHAR(length=50),
               existing_nullable=False)

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('uq_users_email', type_='unique')
        batch_op.add_column(sa.Column('empresa_id', sa.INTEGER(), nullable=True))

    op.drop_index('ix_alerts_printer_id', table_name='alerts')
    op.drop_index('ix_user_username', table_name='users')
    op.create_index('ix_users_username', 'users', ['username'], unique=False)
    op.drop_index('ix_transfer_tipo', table_name='transfers')
    op.create_index('ix_transfers_tipo', 'transfers', ['tipo'], unique=False)
    op.drop_index('ix_transfer_numero_os', table_name='transfers')
    op.create_index('ix_transfers_numero_os', 'transfers', ['numero_os'], unique=False)
    op.drop_index('ix_company_cnpj', table_name='companies')
    op.create_index('ix_companies_cnpj', 'companies', ['cnpj'], unique=False)
    op.drop_index('ix_part_codigo', table_name='parts')
    op.create_index('ix_parts_codigo', 'parts', ['codigo'], unique=False)

    op.execute("PRAGMA foreign_keys=ON")
