import logging

from db import safe_commit

log = logging.getLogger(__name__)
from app.models import Technician


class TechnicianService:
    def __init__(self, session):
        self.session = session

    def listar_todos(self):
        return self.session.query(Technician).order_by(Technician.nome_completo).all()

    def listar_ativos(self):
        return self.session.query(Technician).filter(
            Technician.ativo == True
        ).order_by(Technician.nome_exibicao).all()

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
        return t

    def atualizar(self, tecnico, **kwargs):
        for chave, valor in kwargs.items():
            if hasattr(tecnico, chave):
                setattr(tecnico, chave, valor)
        safe_commit(self.session)

    def excluir(self, tecnico):
        self.session.delete(tecnico)
        safe_commit(self.session)

    def nomes_exibicao(self):
        return [t.nome_exibicao for t in self.listar_ativos()]

