from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from db import safe_commit
from sqlalchemy.orm import Session

from app.models import Technician
from app.utils.sanitize import sanitizar

if TYPE_CHECKING:
    from app.services.audit_service import AuditService

log = logging.getLogger(__name__)


class TechnicianService:
    def __init__(self, session: Session, audit_service: Optional[AuditService] = None, user_id: Optional[int] = None) -> None:
        self.session: Session = session
        self.audit_service: Optional[AuditService] = audit_service
        self.user_id: Optional[int] = user_id

    def listar_todos(self, limite: Optional[int] = None, offset: Optional[int] = None) -> list[Technician]:
        query = self.session.query(Technician).filter(Technician.deleted_at == None).order_by(Technician.nome_completo)
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def listar_ativos(self, limite: Optional[int] = None, offset: Optional[int] = None) -> list[Technician]:
        query = self.session.query(Technician).filter(Technician.deleted_at == None).filter(
            Technician.ativo == True
        ).order_by(Technician.nome_exibicao)
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_por_id(self, tecnico_id: int) -> Optional[Technician]:
        return self.session.query(Technician).filter(
            Technician.deleted_at == None, Technician.id == tecnico_id
        ).first()

    def buscar_por_nome(self, nome: str) -> Optional[Technician]:
        return self.session.query(Technician).filter(
            Technician.deleted_at == None, Technician.nome_completo == nome
        ).first()

    def criar(self, nome_completo: str, nome_exibicao: str = "", telefone: str = "", email: str = "") -> Technician:
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

    def atualizar(self, tecnico: Technician, **kwargs: Any) -> None:
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

    def excluir(self, tecnico: Technician) -> None:
        if self.audit_service:
            self.audit_service.log(self.user_id, "excluir", tabela_alvo="technicians", registro_id=tecnico.id, dados_antes=tecnico)
        tecnico.deleted_at = datetime.utcnow()
        safe_commit(self.session)

    def associar_usuario(self, tecnico_id: int, user_id: int | None) -> None:
        tecnico = self.buscar_por_id(tecnico_id)
        if not tecnico:
            return
        if self.audit_service:
            dados_antes = {"user_id": tecnico.user_id}
        tecnico.user_id = user_id
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "associar_usuario", tabela_alvo="technicians", registro_id=tecnico.id, dados_antes=dados_antes, dados_depois={"user_id": user_id})

    def listar_especialidades(self, tecnico_id: int) -> list[str]:
        from app.models.technician_specialty import TechnicianSpecialty
        registros = self.session.query(TechnicianSpecialty).filter(
            TechnicianSpecialty.technician_id == tecnico_id
        ).all()
        return [r.modelo for r in registros]

    def adicionar_especialidades(self, tecnico_id: int, modelos: list[str]) -> None:
        from app.models.technician_specialty import TechnicianSpecialty
        existentes = set(self.listar_especialidades(tecnico_id))
        for modelo in modelos:
            if modelo and modelo not in existentes:
                self.session.add(TechnicianSpecialty(technician_id=tecnico_id, modelo=modelo))
                existentes.add(modelo)
        safe_commit(self.session)

    def remover_especialidades(self, tecnico_id: int, modelos: list[str]) -> None:
        from app.models.technician_specialty import TechnicianSpecialty
        self.session.query(TechnicianSpecialty).filter(
            TechnicianSpecialty.technician_id == tecnico_id,
            TechnicianSpecialty.modelo.in_(modelos),
        ).delete(synchronize_session=False)
        safe_commit(self.session)

    def limpar_especialidades(self, tecnico_id: int) -> None:
        from app.models.technician_specialty import TechnicianSpecialty
        self.session.query(TechnicianSpecialty).filter(
            TechnicianSpecialty.technician_id == tecnico_id
        ).delete(synchronize_session=False)
        safe_commit(self.session)

    def nomes_exibicao(self) -> list[str]:
        return [t.nome_exibicao for t in self.listar_ativos()]

    def contar_todos(self) -> int:
        return self.session.query(Technician).filter(Technician.deleted_at == None).count()

    def listar_excluidos(self, limite: int = 50) -> list[Technician]:
        return self.session.query(Technician).filter(
            Technician.deleted_at != None
        ).order_by(Technician.deleted_at.desc()).limit(limite).all()

    def restaurar(self, obj: Technician) -> None:
        obj.deleted_at = None
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "restaurar", tabela_alvo="technicians", registro_id=obj.id)

