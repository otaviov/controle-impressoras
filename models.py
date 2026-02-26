from __future__ import annotations
from datetime import datetime
import random
import string
from sqlalchemy import String, Text, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase):
    pass
class Printer(Base):
    __tablename__ = "printers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patrimonio: Mapped[str] = mapped_column (String(80), unique=True, nullable=False)
    modelo: Mapped[str] = mapped_column(String(80), default="")
    serial: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(String(30), default="Operacional")
    local_atual: Mapped[str] = mapped_column(String(120), default="")
    observacao: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # ligação com impressora
    printer_id: Mapped[str] = mapped_column(String(36), index=True)
    # tipo do evento: "MANUTENCAO" ou "MOVIMENTACAO"
    kind: Mapped[str] = mapped_column(String(30))
    # registro automático no sistema
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # data/hora do evento (manual ou automático)
    event_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # descrição do que foi feito
    notes: Mapped[str] = mapped_column(Text, default="")
    # peças trocadas (opcional)
    parts_used: Mapped[str] = mapped_column(Text, default="")
    # movimentação (opcionais)
    from_location: Mapped[str] = mapped_column(String(120), default="")
    to_location: Mapped[str] = mapped_column(String(120), default="")
def simple_uuid() -> str:
    chars = string.ascii_lowercase + string.digits
    parts = [8, 4, 4, 4, 12]
    return "-".join("".join(random.choice(chars) for _ in range(n)) for n in parts)