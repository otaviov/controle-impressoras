"""create printer_health table

Revision ID: b5f6a7c8d9e0
Revises: a44fc2747c28
Create Date: 2026-07-10 18:00:00.000000
"""
from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b5f6a7c8d9e0"
down_revision: str | None = "a44fc2747c28"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "printer_health",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("printer_id", sa.String(36), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("is_online", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("ping_ms", sa.Float(), nullable=True),
        sa.Column("toner_level", sa.Integer(), nullable=True),
        sa.Column("toner_max", sa.Integer(), nullable=True),
        sa.Column("drum_life", sa.Integer(), nullable=True),
        sa.Column("drum_max", sa.Integer(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("error_message", sa.String(255), nullable=True),
        sa.Column("raw_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["printer_id"], ["printers.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_printer_health_printer_id"), "printer_health", ["printer_id"])
    op.create_index(op.f("ix_printer_health_timestamp"), "printer_health", ["timestamp"])
    op.create_index(
        "ix_printer_health_printer_timestamp",
        "printer_health",
        ["printer_id", "timestamp"],
    )


def downgrade() -> None:
    op.drop_index("ix_printer_health_printer_timestamp", table_name="printer_health")
    op.drop_index(op.f("ix_printer_health_timestamp"), table_name="printer_health")
    op.drop_index(op.f("ix_printer_health_printer_id"), table_name="printer_health")
    op.drop_table("printer_health")
