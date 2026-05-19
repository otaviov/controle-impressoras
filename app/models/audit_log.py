from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    acao: Mapped[str] = mapped_column(String(50))
    tabela_alvo: Mapped[str] = mapped_column(String(50), default="")
    registro_id: Mapped[str] = mapped_column(String(50), default="")
    ip_address: Mapped[str] = mapped_column(String(45), default="")
    dados_antes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dados_depois: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped[Optional[User]] = relationship(back_populates="audit_logs")


