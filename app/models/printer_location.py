from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.printer import Printer


class PrinterLocation(Base):
    __tablename__ = "printer_locations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    printer_id: Mapped[str] = mapped_column(String(36), ForeignKey("printers.id"), nullable=False, index=True)
    local: Mapped[str] = mapped_column(String(120), default="")
    data: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    observacao: Mapped[str] = mapped_column(Text, default="")
    activity_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("activities.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    printer: Mapped[Printer] = relationship(back_populates="location_history")
    activity: Mapped[Optional[Activity]] = relationship(back_populates="location_records")
