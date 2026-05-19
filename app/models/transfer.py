from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.printer import Printer


class Transfer(Base):
    __tablename__ = "transfers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    printer_id: Mapped[str] = mapped_column(String(36), ForeignKey("printers.id"), default="")
    numero_os: Mapped[str] = mapped_column(String(50), default="")
    tipo: Mapped[str] = mapped_column(String(20), default="saida")
    from_company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True)
    to_company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True)
    responsavel_entrega: Mapped[str] = mapped_column(String(120), default="")
    responsavel_recebimento: Mapped[str] = mapped_column(String(120), default="")
    data_saida: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    data_retorno_prev: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    data_retorno_real: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    observacao: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    printer: Mapped[Printer] = relationship(back_populates="transfers")
    from_company: Mapped[Optional[Company]] = relationship(back_populates="transfers_from", foreign_keys=[from_company_id])
    to_company: Mapped[Optional[Company]] = relationship(back_populates="transfers_to", foreign_keys=[to_company_id])


