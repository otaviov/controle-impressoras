import logging
from datetime import datetime

from db import safe_commit

log = logging.getLogger(__name__)
from app.models import Company
from app.utils.sanitize import sanitizar


class CompanyService:
    def __init__(self, session, audit_service=None, user_id=None):
        self.session = session
        self.audit_service = audit_service
        self.user_id = user_id

    def listar_todas(self, limite=None, offset=None):
        query = self.session.query(Company).filter(Company.deleted_at == None).order_by(Company.nome)
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_por_nome(self, nome):
        return self.session.query(Company).filter(Company.deleted_at == None, Company.nome == nome).first()

    def criar(self, nome, cnpj="", telefone="", email="", tipo="Cliente"):
        empresa = Company(
            nome=sanitizar(nome, "Company", "nome"),
            cnpj=sanitizar(cnpj, "Company", "cnpj"),
            telefone=sanitizar(telefone, "Company", "telefone"),
            email=sanitizar(email, "Company", "email"),
            tipo=sanitizar(tipo, "Company", "tipo"),
        )
        self.session.add(empresa)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "criar", tabela_alvo="companies", registro_id=empresa.id, dados_depois=empresa)
        return empresa

    def atualizar(self, empresa, **kwargs):
        if self.audit_service:
            dados_antes = {chave: getattr(empresa, chave, None) for chave in kwargs}
        for chave, valor in kwargs.items():
            if hasattr(empresa, chave):
                if isinstance(valor, str):
                    valor = sanitizar(valor, "Company", chave)
                setattr(empresa, chave, valor)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "atualizar", tabela_alvo="companies", registro_id=empresa.id, dados_antes=dados_antes, dados_depois=empresa)

    def excluir(self, empresa):
        if self.audit_service:
            self.audit_service.log(self.user_id, "excluir", tabela_alvo="companies", registro_id=empresa.id, dados_antes=empresa)
        empresa.deleted_at = datetime.utcnow()
        safe_commit(self.session)

    def listar_nomes(self):
        return [emp.nome for emp in self.listar_todas()]

    def contar_todas(self):
        return self.session.query(Company).filter(Company.deleted_at == None).count()

    def listar_excluidos(self, limite=50):
        return self.session.query(Company).filter(
            Company.deleted_at != None
        ).order_by(Company.deleted_at.desc()).limit(limite).all()

    def restaurar(self, obj):
        obj.deleted_at = None
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "restaurar", tabela_alvo="companies", registro_id=obj.id)

