from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from db import safe_commit
from sqlalchemy.orm import Session

from app.models import Part
from app.utils.sanitize import sanitizar

if TYPE_CHECKING:
    from app.services.audit_service import AuditService

log = logging.getLogger(__name__)


class PartService:
    def __init__(self, session: Session, audit_service: Optional[AuditService] = None, user_id: Optional[int] = None) -> None:
        self.session: Session = session
        self.audit_service: Optional[AuditService] = audit_service
        self.user_id: Optional[int] = user_id

    def listar_todas(self, filtro: Optional[str] = None, limite: Optional[int] = None, offset: Optional[int] = None) -> list[Part]:
        query = self.session.query(Part).filter(Part.deleted_at == None)
        if filtro:
            f = f"%{filtro}%"
            query = query.filter(
                Part.nome.like(f) | Part.codigo.like(f) | Part.modelo_compativel.like(f)
            )
        query = query.order_by(Part.nome)
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_por_codigo(self, codigo: str) -> Optional[Part]:
        return self.session.query(Part).filter(Part.codigo == codigo).first()

    def buscar_por_nome(self, nome: str) -> Optional[Part]:
        return self.session.query(Part).filter(Part.nome == nome).first()

    def buscar_por_id(self, part_id: int) -> Optional[Part]:
        return self.session.query(Part).filter(Part.deleted_at == None, Part.id == part_id).first()

    def criar(self, codigo: str, nome: str, descricao: str = "", modelo_compativel: str = "", quantidade: int = 0, estoque_minimo: int = 1) -> Part:
        peca = Part(
            codigo=sanitizar(codigo, "Part", "codigo"),
            nome=sanitizar(nome, "Part", "nome"),
            descricao=sanitizar(descricao),
            modelo_compativel=sanitizar(modelo_compativel, "Part", "modelo_compativel"),
            quantidade_estoque=quantidade,
            estoque_minimo=estoque_minimo,
            preco_unitario=0.0
        )
        self.session.add(peca)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "criar", tabela_alvo="parts", registro_id=peca.id, dados_depois=peca)
        return peca

    def atualizar(self, peca: Part, **kwargs: Any) -> None:
        if self.audit_service:
            dados_antes = {chave: getattr(peca, chave, None) for chave in kwargs}
        for chave, valor in kwargs.items():
            if hasattr(peca, chave):
                if isinstance(valor, str):
                    valor = sanitizar(valor, "Part", chave)
                setattr(peca, chave, valor)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "atualizar", tabela_alvo="parts", registro_id=peca.id, dados_antes=dados_antes, dados_depois=peca)

    def excluir(self, peca: Part) -> None:
        if self.audit_service:
            self.audit_service.log(self.user_id, "excluir", tabela_alvo="parts", registro_id=peca.id, dados_antes=peca)
        peca.deleted_at = datetime.utcnow()
        safe_commit(self.session)

    def contar(self, filtro: Optional[str] = None) -> int:
        query = self.session.query(Part).filter(Part.deleted_at == None)
        if filtro:
            f = f"%{filtro}%"
            query = query.filter(
                Part.nome.like(f) | Part.codigo.like(f) | Part.modelo_compativel.like(f)
            )
        return query.count()

    def gerar_codigo(self) -> str:
        count = self.contar()
        return f"PEC{count + 1:04d}"

    def listar_excluidos(self, limite: int = 50) -> list[Part]:
        return self.session.query(Part).filter(
            Part.deleted_at != None
        ).order_by(Part.deleted_at.desc()).limit(limite).all()

    def restaurar(self, obj: Part) -> None:
        obj.deleted_at = None
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "restaurar", tabela_alvo="parts", registro_id=obj.id)

