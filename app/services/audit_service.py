from __future__ import annotations

import json
import logging

from typing import Any, Optional

from db import safe_commit
from sqlalchemy.orm import Session

from app.models import AuditLog

log = logging.getLogger(__name__)


class AuditService:
    def __init__(self, session: Session) -> None:
        self.session: Session = session

    def log(self, user_id: Optional[int], acao: str, tabela_alvo: str = "", registro_id: str = "",
            ip_address: str = "", dados_antes: Any = None, dados_depois: Any = None) -> AuditLog:
        def serializar(obj):
            if obj is None:
                return None
            if isinstance(obj, dict):
                return {k: str(v) if hasattr(v, 'isoformat') else v for k, v in obj.items()}
            if hasattr(obj, '__dict__'):
                return {k: str(v) if hasattr(v, 'isoformat') else v
                        for k, v in obj.__dict__.items() if not k.startswith('_')}
            return str(obj)

        registro = AuditLog(
            user_id=user_id,
            acao=acao,
            tabela_alvo=tabela_alvo,
            registro_id=str(registro_id) if registro_id else "",
            ip_address=ip_address,
            dados_antes=json.dumps(serializar(dados_antes), ensure_ascii=False, default=str) if dados_antes else None,
            dados_depois=json.dumps(serializar(dados_depois), ensure_ascii=False, default=str) if dados_depois else None,
        )
        self.session.add(registro)
        safe_commit(self.session)
        return registro

    def listar(self, limite: int = 100) -> list[AuditLog]:
        return self.session.query(AuditLog).order_by(
            AuditLog.created_at.desc()
        ).limit(limite).all()

    def listar_por_tabela(self, tabela: str, limite: int = 50) -> list[AuditLog]:
        return self.session.query(AuditLog).filter(
            AuditLog.tabela_alvo == tabela
        ).order_by(AuditLog.created_at.desc()).limit(limite).all()

    def listar_por_usuario(self, user_id: int, limite: int = 50) -> list[AuditLog]:
        return self.session.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.created_at.desc()).limit(limite).all()

