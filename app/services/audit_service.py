import logging

from db import safe_commit

log = logging.getLogger(__name__)
import json

from app.models import AuditLog


class AuditService:
    def __init__(self, session):
        self.session = session

    def log(self, user_id, acao, tabela_alvo="", registro_id="",
            ip_address="", dados_antes=None, dados_depois=None):
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

    def listar(self, limite=100):
        return self.session.query(AuditLog).order_by(
            AuditLog.created_at.desc()
        ).limit(limite).all()

    def listar_por_tabela(self, tabela, limite=50):
        return self.session.query(AuditLog).filter(
            AuditLog.tabela_alvo == tabela
        ).order_by(AuditLog.created_at.desc()).limit(limite).all()

    def listar_por_usuario(self, user_id, limite=50):
        return self.session.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.created_at.desc()).limit(limite).all()

