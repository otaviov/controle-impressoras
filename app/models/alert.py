from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    printer_id: Mapped[str] = mapped_column(String(36), index=True)
    tipo: Mapped[str] = mapped_column(String(20), default="revisao")
    titulo: Mapped[str] = mapped_column(String(200), default="")
    descricao: Mapped[str] = mapped_column(Text, default="")
    data_alerta: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    resolvido: Mapped[bool] = mapped_column(Boolean, default=False)
    resolvido_em: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    resolvido_por: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
