from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.printer import Printer
    from app.models.user import User


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    printer_id: Mapped[str] = mapped_column(String(36), ForeignKey("printers.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(20), default="revisao")
    titulo: Mapped[str] = mapped_column(String(200), default="")
    descricao: Mapped[Optional[str]] = mapped_column(Text, default="")
    data_alerta: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolvido: Mapped[bool] = mapped_column(Boolean, default=False)
    resolvido_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolvido_por: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    printer: Mapped[Printer] = relationship(back_populates="alerts")
    resolved_by: Mapped[Optional[User]] = relationship(back_populates="alerts_resolved")


