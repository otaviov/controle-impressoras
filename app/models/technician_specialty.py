from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.technician import Technician


class TechnicianSpecialty(Base):
    __tablename__ = "technician_specialties"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    technician_id: Mapped[int] = mapped_column(Integer, ForeignKey("technicians.id"), nullable=False)
    modelo: Mapped[str] = mapped_column(String(120), nullable=False)

    technician: Mapped[Technician] = relationship(back_populates="specialties")
