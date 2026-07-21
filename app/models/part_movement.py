from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, utcnow

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.part import Part


class PartMovement(Base, SoftDeleteMixin):
    __tablename__ = "part_movements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    part_id: Mapped[int] = mapped_column(Integer, ForeignKey("parts.id"), nullable=False, index=True)
    activity_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("activities.id"), nullable=True, index=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    saldo_anterior: Mapped[int] = mapped_column(Integer, default=0)
    saldo_posterior: Mapped[int] = mapped_column(Integer, default=0)
    observacao: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    part: Mapped[Part] = relationship(back_populates="movements")
    activity: Mapped[Optional[Activity]] = relationship(back_populates="part_movements")
