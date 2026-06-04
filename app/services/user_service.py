from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from db import safe_commit
from sqlalchemy.orm import Session

from app.models import User
from app.utils.sanitize import sanitizar
from app.utils.security import hash_password

if TYPE_CHECKING:
    from app.services.audit_service import AuditService

log = logging.getLogger(__name__)


class UserService:
    def __init__(self, session: Session, audit_service: Optional[AuditService] = None, user_id: Optional[int] = None) -> None:
        self.session: Session = session
        self.audit_service: Optional[AuditService] = audit_service
        self.user_id: Optional[int] = user_id

    def listar_todos(self, limite: Optional[int] = None, offset: Optional[int] = None) -> list[User]:
        query = self.session.query(User).filter(User.deleted_at == None).order_by(User.nome)
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_por_id(self, user_id: int) -> Optional[User]:
        return self.session.query(User).filter(User.deleted_at == None, User.id == user_id).first()

    def buscar_por_username_ou_email(self, valor: str) -> Optional[User]:
        return self.session.query(User).filter(
            User.deleted_at == None, (User.email == valor) | (User.username == valor)
        ).first()

    def verificar_existente(self, email: str, username: str) -> Optional[User]:
        return self.session.query(User).filter(
            User.deleted_at == None, (User.email == email) | (User.username == username)
        ).first()

    def criar(self, nome: str, username: str, email: str, senha: str, perfil: str = "visualizador") -> User:
        u = User(
            nome=sanitizar(nome, "User", "nome"),
            username=sanitizar(username, "User", "username"),
            email=sanitizar(email, "User", "email"),
            senha_hash=hash_password(senha),
            perfil=sanitizar(perfil, "User", "perfil"),
            ativo=True
        )
        self.session.add(u)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "criar", tabela_alvo="users", registro_id=u.id, dados_depois=u)
        return u

    def atualizar(self, user: User, **kwargs: Any) -> None:
        if self.audit_service:
            dados_antes = {chave: getattr(user, chave, None) for chave in kwargs}
        senha = kwargs.pop("senha", None)
        if senha:
            user.senha_hash = hash_password(senha)
        for chave, valor in kwargs.items():
            if hasattr(user, chave):
                if isinstance(valor, str):
                    valor = sanitizar(valor, "User", chave)
                setattr(user, chave, valor)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "atualizar", tabela_alvo="users", registro_id=user.id, dados_antes=dados_antes, dados_depois=user)

    def contar_todos(self) -> int:
        return self.session.query(User).filter(User.deleted_at == None).count()

    def listar_excluidos(self, limite: int = 50) -> list[User]:
        return self.session.query(User).filter(
            User.deleted_at != None
        ).order_by(User.deleted_at.desc()).limit(limite).all()

    def restaurar(self, obj: User) -> None:
        obj.deleted_at = None
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "restaurar", tabela_alvo="users", registro_id=obj.id)

