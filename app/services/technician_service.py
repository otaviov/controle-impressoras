import logging

from db import safe_commit

log = logging.getLogger(__name__)
from app.models import Technician


class TechnicianService:
    def __init__(self, session, audit_service=None, user_id=None):
        self.session = session
        self.audit_service = audit_service
        self.user_id = user_id

    def listar_todos(self, limite=None, offset=None):
        query = self.session.query(Technician).order_by(Technician.nome_completo)
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def listar_ativos(self, limite=None, offset=None):
        query = self.session.query(Technician).filter(
            Technician.ativo == True
        ).order_by(Technician.nome_exibicao)
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_por_id(self, tecnico_id):
        return self.session.query(Technician).filter(
            Technician.id == tecnico_id
        ).first()

    def buscar_por_nome(self, nome):
        return self.session.query(Technician).filter(
            Technician.nome_completo == nome
        ).first()

    def criar(self, nome_completo, nome_exibicao="", telefone="", email=""):
        t = Technician(
            nome_completo=nome_completo,
            nome_exibicao=nome_exibicao or nome_completo.split()[0],
            telefone=telefone,
            email=email
        )
        self.session.add(t)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "criar", tabela_alvo="technicians", registro_id=t.id, dados_depois=t)
        return t

    def atualizar(self, tecnico, **kwargs):
        if self.audit_service:
            dados_antes = {chave: getattr(tecnico, chave, None) for chave in kwargs}
        for chave, valor in kwargs.items():
            if hasattr(tecnico, chave):
                setattr(tecnico, chave, valor)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "atualizar", tabela_alvo="technicians", registro_id=tecnico.id, dados_antes=dados_antes, dados_depois=tecnico)

    def excluir(self, tecnico):
        if self.audit_service:
            self.audit_service.log(self.user_id, "excluir", tabela_alvo="technicians", registro_id=tecnico.id, dados_antes=tecnico)
        self.session.delete(tecnico)
        safe_commit(self.session)

    def nomes_exibicao(self):
        return [t.nome_exibicao for t in self.listar_ativos()]

