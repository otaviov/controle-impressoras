from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, utcnow

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.part_movement import PartMovement
    from app.models.part_reservation import PartReservation
    from app.models.purchase_requisition import PurchaseRequisition


class Part(Base, SoftDeleteMixin):
    __tablename__ = "parts"
    __table_args__ = (Index("ix_part_codigo", "codigo"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), default="")
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, default="")
    quantidade_estoque: Mapped[int] = mapped_column(Integer, default=0)
    estoque_minimo: Mapped[int] = mapped_column(Integer, default=1)
    preco_unitario: Mapped[float] = mapped_column(Float, default=0.0)
    modelo_compativel: Mapped[str] = mapped_column(String(200), default="")
    marca: Mapped[str] = mapped_column(String(100), default="")
    categoria: Mapped[str] = mapped_column(String(100), default="")
    fornecedor: Mapped[str] = mapped_column(String(150), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    alerts: Mapped[list[Alert]] = relationship(back_populates="part")
    movements: Mapped[list[PartMovement]] = relationship(back_populates="part", cascade="all, delete-orphan")
    reservations: Mapped[list[PartReservation]] = relationship(back_populates="part", cascade="all, delete-orphan")
    purchase_requisitions: Mapped[list[PurchaseRequisition]] = relationship(back_populates="part", cascade="all, delete-orphan")


