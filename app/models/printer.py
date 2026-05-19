from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.alert import Alert
    from app.models.company import Company
    from app.models.transfer import Transfer


class Printer(Base):
    __tablename__ = "printers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patrimonio: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    modelo: Mapped[str] = mapped_column(String(80), default="")
    serial: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(String(30), default="Operacional")
    local_atual: Mapped[str] = mapped_column(String(120), default="")

    marca: Mapped[str] = mapped_column(String(80), default="")
    tipo: Mapped[str] = mapped_column(String(20), default="")
    ip_rede: Mapped[str] = mapped_column(String(15), default="")
    mac_address: Mapped[str] = mapped_column(String(17), default="")
    empresa_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True)
    proxima_revisao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    tecnico: Mapped[str] = mapped_column(String(120), default="")

    pecas_faltantes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observacao: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    company: Mapped[Optional[Company]] = relationship(back_populates="printers")
    activities: Mapped[List[Activity]] = relationship(back_populates="printer")
    transfers: Mapped[List[Transfer]] = relationship(back_populates="printer")
    alerts: Mapped[List[Alert]] = relationship(back_populates="printer")


