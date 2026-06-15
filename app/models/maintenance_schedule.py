from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.printer import Printer


class MaintenanceSchedule(Base):
    __tablename__ = "maintenance_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    printer_id: Mapped[str] = mapped_column(String(36), ForeignKey("printers.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    intervalo_dias: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    intervalo_paginas: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    contador_inicial: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    contador_atual: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ultima_geracao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    proxima_geracao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    proxima_meta_paginas: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dias_aviso: Mapped[int] = mapped_column(Integer, default=7)
    observacao: Mapped[str] = mapped_column(Text, default="")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    printer: Mapped[Printer] = relationship("Printer", back_populates="maintenance_schedules")

    def __repr__(self) -> str:
        return f"<MaintenanceSchedule id={self.id} printer={self.printer_id} tipo={self.tipo}>"
