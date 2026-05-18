from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Transfer(Base):
    __tablename__ = "transfers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    printer_id: Mapped[str] = mapped_column(String(36), default="")
    numero_os: Mapped[str] = mapped_column(String(50), default="")
    tipo: Mapped[str] = mapped_column(String(20), default="saida")
    from_company_id: Mapped[int] = mapped_column(Integer, nullable=True)
    to_company_id: Mapped[int] = mapped_column(Integer, nullable=True)
    responsavel_entrega: Mapped[str] = mapped_column(String(120), default="")
    responsavel_recebimento: Mapped[str] = mapped_column(String(120), default="")
    data_saida: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    data_retorno_prev: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    data_retorno_real: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    observacao: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
