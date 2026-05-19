from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.activity import Activity


class Technician(Base):
    __tablename__ = "technicians"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    nome_exibicao: Mapped[str] = mapped_column(String(80), default="")
    telefone: Mapped[str] = mapped_column(String(20), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    activities: Mapped[List[Activity]] = relationship(back_populates="technician")


