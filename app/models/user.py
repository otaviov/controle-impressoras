from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.attachment import Attachment
    from app.models.audit_log import AuditLog


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), default="")
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[str] = mapped_column(String(20), default="visualizador")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    ultimo_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    alerts_resolved: Mapped[List[Alert]] = relationship(back_populates="resolved_by")
    audit_logs: Mapped[List[AuditLog]] = relationship(back_populates="user")
    uploads: Mapped[List[Attachment]] = relationship(back_populates="uploader")


