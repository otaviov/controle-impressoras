from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from db import safe_commit
from sqlalchemy.orm import Session

from app.models import LoginHistory
from app.models.base import utcnow


class LoginHistoryService:
    def __init__(self, session: Session) -> None:
        self.session: Session = session

    def registrar_login(self, user_id: int, ip_address: str = "") -> LoginHistory:
        sessao = LoginHistory(user_id=user_id, ip_address=ip_address)
        self.session.add(sessao)
        safe_commit(self.session)
        return sessao

    def registrar_logout(self, user_id: int) -> Optional[LoginHistory]:
        sessao = self.session.query(LoginHistory).filter(
            LoginHistory.user_id == user_id,
            LoginHistory.logout_at.is_(None)
        ).order_by(LoginHistory.login_at.desc()).first()
        if sessao:
            sessao.logout_at = utcnow()
            safe_commit(self.session)
        return sessao

    def listar_por_usuario(self, user_id: int, limite: int = 50) -> list[LoginHistory]:
        return self.session.query(LoginHistory).filter(
            LoginHistory.user_id == user_id
        ).order_by(LoginHistory.login_at.desc()).limit(limite).all()

    def listar_todos(self, limite: int = 100) -> list[LoginHistory]:
        return self.session.query(LoginHistory).order_by(
            LoginHistory.login_at.desc()
        ).limit(limite).all()

    def ultimo_login(self, user_id: int) -> Optional[LoginHistory]:
        return self.session.query(LoginHistory).filter(
            LoginHistory.user_id == user_id
        ).order_by(LoginHistory.login_at.desc()).first()

    def tempo_medio_sessao(self, user_id: int) -> Any:
        from sqlalchemy import func
        result = self.session.query(
            func.avg(LoginHistory.logout_at - LoginHistory.login_at)
        ).filter(
            LoginHistory.user_id == user_id,
            LoginHistory.logout_at.isnot(None)
        ).scalar()
        return result
