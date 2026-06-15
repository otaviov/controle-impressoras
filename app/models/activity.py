from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, utcnow

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.printer import Printer
    from app.models.technician import Technician


class Activity(Base, SoftDeleteMixin):
    __tablename__ = "activities"
    __table_args__ = (
        Index("ix_activity_kind", "kind"),
        Index("ix_activity_numero_recibo", "numero_recibo"),
        Index("ix_activity_status", "status_atividade"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    printer_id: Mapped[str] = mapped_column(String(36), ForeignKey("printers.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))

    from_company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True)
    to_company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True)
    numero_recibo: Mapped[str] = mapped_column(String(50), default="")
    responsavel: Mapped[str] = mapped_column(String(120), default="")
    tecnico_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("technicians.id"), nullable=True)
    custo_servico: Mapped[float] = mapped_column(Float, default=0.0)
    status_atividade: Mapped[str] = mapped_column(String(30), default="Aberta")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    event_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    inicio_atendimento: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fim_atendimento: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    parts_used: Mapped[str] = mapped_column(Text, default="")
    from_location: Mapped[str] = mapped_column(String(120), default="")
    to_location: Mapped[str] = mapped_column(String(120), default="")
    procedimentos: Mapped[str] = mapped_column(Text, default="")
    urgencia: Mapped[str] = mapped_column(String(20), default="Normal")
    sintoma_relatado: Mapped[str] = mapped_column(Text, default="")
    diagnostico_tecnico: Mapped[str] = mapped_column(Text, default="")
    solucao_aplicada: Mapped[str] = mapped_column(Text, default="")
    os_vinculada_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("activities.id"), nullable=True, index=True)

    printer: Mapped[Printer] = relationship(back_populates="activities")
    from_company: Mapped[Optional[Company]] = relationship(back_populates="activities_from", foreign_keys=[from_company_id])
    to_company: Mapped[Optional[Company]] = relationship(back_populates="activities_to", foreign_keys=[to_company_id])
    technician: Mapped[Optional[Technician]] = relationship(back_populates="activities")
    os_vinculada: Mapped[Optional[Activity]] = relationship("Activity", remote_side="Activity.id", back_populates="oses_filhas")
    oses_filhas: Mapped[list[Activity]] = relationship("Activity", back_populates="os_vinculada")


