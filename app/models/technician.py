from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, utcnow

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.technician_specialty import TechnicianSpecialty
    from app.models.user import User


class Technician(Base, SoftDeleteMixin):
    __tablename__ = "technicians"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    nome_exibicao: Mapped[str] = mapped_column(String(80), default="")
    telefone: Mapped[str] = mapped_column(String(20), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    capacidade_diaria: Mapped[int] = mapped_column(Integer, default=5)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    activities: Mapped[List[Activity]] = relationship(back_populates="technician")
    user: Mapped[User | None] = relationship()
    specialties: Mapped[List[TechnicianSpecialty]] = relationship(back_populates="technician", cascade="all, delete-orphan")


