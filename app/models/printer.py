from __future__ import annotations
from datetime import datetime
import random
import string
from sqlalchemy import String, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def simple_uid() -> str:
    chars = string.ascii_lowercase + string.digits
    parts = [8, 4, 4, 4, 12]
    return "-".join("".join(random.choice(chars) for _ in range(n)) for n in parts)


class Printer(Base):
    __tablename__ = "printers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patrimonio: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    modelo: Mapped[str] = mapped_column(String(80), default="")
    serial: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(String(30), default="Operacional")
    local_atual: Mapped[str] = mapped_column(String(120), default="")

    marca: Mapped[str] = mapped_column(String(80), default="")
    tipo: Mapped[str] = mapped_column(String(20), default="")
    ip_rede: Mapped[str] = mapped_column(String(15), default="")
    mac_address: Mapped[str] = mapped_column(String(17), default="")
    empresa_id: Mapped[int] = mapped_column(Integer, nullable=True)
    proxima_revisao: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    tecnico: Mapped[str] = mapped_column(String(120), default="")

    pecas_faltantes: Mapped[str] = mapped_column(Text, nullable=True)
    observacao: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
