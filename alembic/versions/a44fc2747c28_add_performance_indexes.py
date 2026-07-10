"""add performance indexes

Revision ID: a44fc2747c28
Revises: 8a7b6c5d4e3f
Create Date: 2026-07-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a44fc2747c28'
down_revision: Union[str, Sequence[str], None] = '8a7b6c5d4e3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- printers ---
    with op.batch_alter_table("printers", schema=None) as batch_op:
        batch_op.create_index("ix_printers_status", ["status"])
        batch_op.create_index("ix_printers_deleted_at", ["deleted_at"])

    # --- activities ---
    with op.batch_alter_table("activities", schema=None) as batch_op:
        batch_op.create_index("ix_activities_deleted_at", ["deleted_at"])
        batch_op.create_index("ix_activities_event_at", ["event_at"])
        batch_op.create_index("ix_activities_tecnico_id", ["tecnico_id"])
        batch_op.create_index("ix_activities_tecnico_id_event_at", ["tecnico_id", "event_at"])
        batch_op.create_index("ix_activities_printer_id_event_at", ["printer_id", "event_at"])
        batch_op.create_index("ix_activities_status_event_at", ["status_atividade", "event_at"])

    # --- alerts ---
    with op.batch_alter_table("alerts", schema=None) as batch_op:
        batch_op.create_index("ix_alerts_deleted_at", ["deleted_at"])
        batch_op.create_index("ix_alerts_resolvido", ["resolvido"])
        batch_op.create_index("ix_alerts_resolvido_created_at", ["resolvido", "created_at"])
        batch_op.create_index("ix_alerts_tipo_resolvido", ["tipo", "resolvido"])

    # --- companies ---
    with op.batch_alter_table("companies", schema=None) as batch_op:
        batch_op.create_index("ix_companies_deleted_at", ["deleted_at"])

    # --- parts ---
    with op.batch_alter_table("parts", schema=None) as batch_op:
        batch_op.create_index("ix_parts_deleted_at", ["deleted_at"])
        batch_op.create_index("ix_parts_nome", ["nome"])

    # --- technicians ---
    with op.batch_alter_table("technicians", schema=None) as batch_op:
        batch_op.create_index("ix_technicians_deleted_at", ["deleted_at"])

    # --- users ---
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_index("ix_users_deleted_at", ["deleted_at"])

    # --- FK columns sem índice ---
    with op.batch_alter_table("login_history", schema=None) as batch_op:
        batch_op.create_index("ix_login_history_user_id", ["user_id"])

    with op.batch_alter_table("technician_specialties", schema=None) as batch_op:
        batch_op.create_index("ix_technician_specialties_technician_id", ["technician_id"])

    with op.batch_alter_table("printer_locations", schema=None) as batch_op:
        batch_op.create_index("ix_printer_locations_activity_id", ["activity_id"])

    with op.batch_alter_table("attachments", schema=None) as batch_op:
        batch_op.create_index("ix_attachments_uploader_id", ["uploader_id"])

    with op.batch_alter_table("audit_log", schema=None) as batch_op:
        batch_op.create_index("ix_audit_log_user_id", ["user_id"])
        batch_op.create_index("ix_audit_log_created_at", ["created_at"])
        batch_op.create_index("ix_audit_log_tabela_alvo", ["tabela_alvo"])


def downgrade() -> None:
    with op.batch_alter_table("printers", schema=None) as batch_op:
        batch_op.drop_index("ix_printers_status")
        batch_op.drop_index("ix_printers_deleted_at")

    with op.batch_alter_table("activities", schema=None) as batch_op:
        batch_op.drop_index("ix_activities_deleted_at")
        batch_op.drop_index("ix_activities_event_at")
        batch_op.drop_index("ix_activities_tecnico_id")
        batch_op.drop_index("ix_activities_tecnico_id_event_at")
        batch_op.drop_index("ix_activities_printer_id_event_at")
        batch_op.drop_index("ix_activities_status_event_at")

    with op.batch_alter_table("alerts", schema=None) as batch_op:
        batch_op.drop_index("ix_alerts_deleted_at")
        batch_op.drop_index("ix_alerts_resolvido")
        batch_op.drop_index("ix_alerts_resolvido_created_at")
        batch_op.drop_index("ix_alerts_tipo_resolvido")

    with op.batch_alter_table("companies", schema=None) as batch_op:
        batch_op.drop_index("ix_companies_deleted_at")

    with op.batch_alter_table("parts", schema=None) as batch_op:
        batch_op.drop_index("ix_parts_deleted_at")
        batch_op.drop_index("ix_parts_nome")

    with op.batch_alter_table("technicians", schema=None) as batch_op:
        batch_op.drop_index("ix_technicians_deleted_at")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_deleted_at")

    with op.batch_alter_table("login_history", schema=None) as batch_op:
        batch_op.drop_index("ix_login_history_user_id")

    with op.batch_alter_table("technician_specialties", schema=None) as batch_op:
        batch_op.drop_index("ix_technician_specialties_technician_id")

    with op.batch_alter_table("printer_locations", schema=None) as batch_op:
        batch_op.drop_index("ix_printer_locations_activity_id")

    with op.batch_alter_table("attachments", schema=None) as batch_op:
        batch_op.drop_index("ix_attachments_uploader_id")

    with op.batch_alter_table("audit_log", schema=None) as batch_op:
        batch_op.drop_index("ix_audit_log_user_id")
        batch_op.drop_index("ix_audit_log_created_at")
        batch_op.drop_index("ix_audit_log_tabela_alvo")
