import logging
from datetime import datetime

from db import safe_commit

log = logging.getLogger(__name__)
from app.models import Technician
from app.utils.sanitize import sanitizar


class TechnicianService:
    def __init__(self, session, audit_service=None, user_id=None):
        self.session = session
        self.audit_service = audit_service
        self.user_id = user_id

    def listar_todos(self, limite=None, offset=None):
        query = self.session.query(Technician).filter(Technician.deleted_at == None).order_by(Technician.nome_completo)
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def listar_ativos(self, limite=None, offset=None):
        query = self.session.query(Technician).filter(Technician.deleted_at == None).filter(
            Technician.ativo == True
        ).order_by(Technician.nome_exibicao)
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_por_id(self, tecnico_id):
        return self.session.query(Technician).filter(
            Technician.deleted_at == None, Technician.id == tecnico_id
        ).first()

    def buscar_por_nome(self, nome):
        return self.session.query(Technician).filter(
            Technician.deleted_at == None, Technician.nome_completo == nome
        ).first()

    def criar(self, nome_completo, nome_exibicao="", telefone="", email=""):
        t = Technician(
            nome_completo=sanitizar(nome_completo, "Technician", "nome_completo"),
            nome_exibicao=sanitizar(nome_exibicao or nome_completo.split()[0], "Technician", "nome_exibicao"),
            telefone=sanitizar(telefone, "Technician", "telefone"),
            email=sanitizar(email, "Technician", "email"),
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
                if isinstance(valor, str):
                    valor = sanitizar(valor, "Technician", chave)
                setattr(tecnico, chave, valor)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "atualizar", tabela_alvo="technicians", registro_id=tecnico.id, dados_antes=dados_antes, dados_depois=tecnico)

    def excluir(self, tecnico):
        if self.audit_service:
            self.audit_service.log(self.user_id, "excluir", tabela_alvo="technicians", registro_id=tecnico.id, dados_antes=tecnico)
        tecnico.deleted_at = datetime.utcnow()
        safe_commit(self.session)

    def nomes_exibicao(self):
        return [t.nome_exibicao for t in self.listar_ativos()]

    def contar_todos(self):
        return self.session.query(Technician).filter(Technician.deleted_at == None).count()

    def listar_excluidos(self, limite=50):
        return self.session.query(Technician).filter(
            Technician.deleted_at != None
        ).order_by(Technician.deleted_at.desc()).limit(limite).all()

    def restaurar(self, obj):
        obj.deleted_at = None
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "restaurar", tabela_alvo="technicians", registro_id=obj.id)

