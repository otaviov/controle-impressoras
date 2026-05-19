from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.printer import Printer
    from app.models.transfer import Transfer


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(18), default="")
    endereco: Mapped[str] = mapped_column(String(255), default="")
    cidade: Mapped[str] = mapped_column(String(100), default="")
    uf: Mapped[str] = mapped_column(String(2), default="")
    telefone: Mapped[str] = mapped_column(String(20), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    tipo: Mapped[str] = mapped_column(String(20), default="cliente")
    observacao: Mapped[Optional[str]] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    printers: Mapped[List[Printer]] = relationship(back_populates="company")
    activities_from: Mapped[List[Activity]] = relationship(back_populates="from_company", foreign_keys="Activity.from_company_id")
    activities_to: Mapped[List[Activity]] = relationship(back_populates="to_company", foreign_keys="Activity.to_company_id")
    transfers_from: Mapped[List[Transfer]] = relationship(back_populates="from_company", foreign_keys="Transfer.from_company_id")
    transfers_to: Mapped[List[Transfer]] = relationship(back_populates="to_company", foreign_keys="Transfer.to_company_id")


