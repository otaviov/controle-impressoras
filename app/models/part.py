from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class Part(Base):
    __tablename__ = "parts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), default="")
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, default="")
    quantidade_estoque: Mapped[int] = mapped_column(Integer, default=0)
    estoque_minimo: Mapped[int] = mapped_column(Integer, default=1)
    preco_unitario: Mapped[float] = mapped_column(Float, default=0.0)
    modelo_compativel: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


