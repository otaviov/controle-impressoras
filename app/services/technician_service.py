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
        self.session.commit()
        return t

    def atualizar(self, tecnico, **kwargs):
        for chave, valor in kwargs.items():
            if hasattr(tecnico, chave):
                setattr(tecnico, chave, valor)
        self.session.commit()

    def excluir(self, tecnico):
        self.session.delete(tecnico)
        self.session.commit()

    def nomes_exibicao(self):
        return [t.nome_exibicao for t in self.listar_ativos()]
