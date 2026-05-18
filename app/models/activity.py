from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    printer_id: Mapped[str] = mapped_column(String(36), index=True)
    kind: Mapped[str] = mapped_column(String(30))

    from_company_id: Mapped[int] = mapped_column(Integer, nullable=True)
    to_company_id: Mapped[int] = mapped_column(Integer, nullable=True)
    numero_recibo: Mapped[str] = mapped_column(String(50), default="")
    tecnico_id: Mapped[int] = mapped_column(Integer, nullable=True)
    custo_servico: Mapped[float] = mapped_column(Float, default=0.0)
    status_atividade: Mapped[str] = mapped_column(String(30), default="concluida")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    event_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[str] = mapped_column(Text, default="")
    parts_used: Mapped[str] = mapped_column(Text, default="")
    from_location: Mapped[str] = mapped_column(String(120), default="")
    to_location: Mapped[str] = mapped_column(String(120), default="")
