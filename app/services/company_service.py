from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from db import safe_commit
from sqlalchemy.orm import Session

from app.models import Company
from app.utils.sanitize import sanitizar

if TYPE_CHECKING:
    from app.services.audit_service import AuditService

log = logging.getLogger(__name__)


class CompanyService:
    def __init__(self, session: Session, audit_service: Optional[AuditService] = None, user_id: Optional[int] = None) -> None:
        self.session: Session = session
        self.audit_service: Optional[AuditService] = audit_service
        self.user_id: Optional[int] = user_id

    def listar_todas(self, limite: Optional[int] = None, offset: Optional[int] = None) -> list[Company]:
        query = self.session.query(Company).filter(Company.deleted_at == None).order_by(Company.nome)
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_por_nome(self, nome: str) -> Optional[Company]:
        return self.session.query(Company).filter(Company.deleted_at == None, Company.nome == nome).first()

    def criar(self, nome: str, cnpj: str = "", telefone: str = "", email: str = "", tipo: str = "Cliente", endereco: str = "", cidade: str = "", uf: str = "", observacao: str = "") -> Company:
        empresa = Company(
            nome=sanitizar(nome, "Company", "nome"),
            cnpj=sanitizar(cnpj, "Company", "cnpj"),
            telefone=sanitizar(telefone, "Company", "telefone"),
            email=sanitizar(email, "Company", "email"),
            tipo=sanitizar(tipo, "Company", "tipo"),
            endereco=sanitizar(endereco, "Company", "endereco"),
            cidade=sanitizar(cidade, "Company", "cidade"),
            uf=sanitizar(uf, "Company", "uf"),
            observacao=sanitizar(observacao, "Company", "observacao"),
        )
        self.session.add(empresa)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "criar", tabela_alvo="companies", registro_id=empresa.id, dados_depois=empresa)
        return empresa

    def atualizar(self, empresa: Company, **kwargs: Any) -> None:
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

    def excluir(self, empresa: Company) -> None:
        if self.audit_service:
            self.audit_service.log(self.user_id, "excluir", tabela_alvo="companies", registro_id=empresa.id, dados_antes=empresa)
        empresa.deleted_at = datetime.utcnow()
        safe_commit(self.session)

    def listar_nomes(self) -> list[str]:
        return [emp.nome for emp in self.listar_todas()]

    def contar_todas(self) -> int:
        return self.session.query(Company).filter(Company.deleted_at == None).count()

    def listar_excluidos(self, limite: int = 50) -> list[Company]:
        return self.session.query(Company).filter(
            Company.deleted_at != None
        ).order_by(Company.deleted_at.desc()).limit(limite).all()

    def restaurar(self, obj: Company) -> None:
        obj.deleted_at = None
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "restaurar", tabela_alvo="companies", registro_id=obj.id)

