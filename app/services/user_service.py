import logging

from db import safe_commit

log = logging.getLogger(__name__)
from app.models import User
from app.utils.security import hash_password


class UserService:
    def __init__(self, session, audit_service=None, user_id=None):
        self.session = session
        self.audit_service = audit_service
        self.user_id = user_id

    def listar_todos(self, limite=None, offset=None):
        query = self.session.query(User).order_by(User.nome)
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_por_id(self, user_id):
        return self.session.query(User).filter(User.id == user_id).first()

    def buscar_por_username_ou_email(self, valor):
        return self.session.query(User).filter(
            (User.email == valor) | (User.username == valor)
        ).first()

    def verificar_existente(self, email, username):
        return self.session.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()

    def criar(self, nome, username, email, senha, perfil="visualizador"):
        u = User(
            nome=nome,
            username=username,
            email=email,
            senha_hash=hash_password(senha),
            perfil=perfil,
            ativo=True
        )
        self.session.add(u)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "criar", tabela_alvo="users", registro_id=u.id, dados_depois=u)
        return u

    def atualizar(self, user, **kwargs):
        if self.audit_service:
            dados_antes = {chave: getattr(user, chave, None) for chave in kwargs}
        senha = kwargs.pop("senha", None)
        if senha:
            user.senha_hash = hash_password(senha)
        for chave, valor in kwargs.items():
            if hasattr(user, chave):
                setattr(user, chave, valor)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "atualizar", tabela_alvo="users", registro_id=user.id, dados_antes=dados_antes, dados_depois=user)

