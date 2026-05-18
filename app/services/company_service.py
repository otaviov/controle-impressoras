from app.models import Company


class CompanyService:
    def __init__(self, session):
        self.session = session

    def listar_todas(self):
        return self.session.query(Company).order_by(Company.nome).all()

    def buscar_por_nome(self, nome):
        return self.session.query(Company).filter(Company.nome == nome).first()

    def criar(self, nome, cnpj="", telefone="", email="", tipo="Cliente"):
        empresa = Company(
            nome=nome, cnpj=cnpj,
            telefone=telefone, email=email,
            tipo=tipo
        )
        self.session.add(empresa)
        self.session.commit()
        return empresa

    def atualizar(self, empresa, **kwargs):
        for chave, valor in kwargs.items():
            if hasattr(empresa, chave):
                setattr(empresa, chave, valor)
        self.session.commit()

    def excluir(self, empresa):
        self.session.delete(empresa)
        self.session.commit()

    def listar_nomes(self):
        return [emp.nome for emp in self.listar_todas()]
