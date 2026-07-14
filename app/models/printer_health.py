from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.models.base import Base


class PrinterHealth(Base):
    __tablename__ = "printer_health"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    printer_id: str = Column(String(36), ForeignKey("printers.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp: datetime = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    is_online: bool = Column(Integer, default=False, nullable=False)

    ping_ms: Optional[float] = Column(Float, nullable=True)

    toner_level: Optional[int] = Column(Integer, nullable=True)
    toner_max: Optional[int] = Column(Integer, nullable=True)
    drum_life: Optional[int] = Column(Integer, nullable=True)
    drum_max: Optional[int] = Column(Integer, nullable=True)
    page_count: Optional[int] = Column(Integer, nullable=True)

    error_code: Optional[str] = Column(String(50), nullable=True)
    error_message: Optional[str] = Column(String(255), nullable=True)
    raw_data: Optional[str] = Column(Text, nullable=True)

    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
