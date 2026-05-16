from models import Part


class PartService:
    def __init__(self, session):
        self.session = session

    def listar_todas(self):
        return self.session.query(Part).order_by(Part.nome).all()

    def buscar_por_codigo(self, codigo):
        return self.session.query(Part).filter(Part.codigo == codigo).first()

    def buscar_por_nome(self, nome):
        return self.session.query(Part).filter(Part.nome == nome).first()

    def criar(self, codigo, nome, descricao="", modelo_compativel="", quantidade=0):
        peca = Part(
            codigo=codigo,
            nome=nome,
            descricao=descricao,
            modelo_compativel=modelo_compativel,
            quantidade_estoque=quantidade,
            preco_unitario=0.0
        )
        self.session.add(peca)
        self.session.commit()
        return peca

    def atualizar(self, peca, **kwargs):
        for chave, valor in kwargs.items():
            if hasattr(peca, chave):
                setattr(peca, chave, valor)
        self.session.commit()

    def excluir(self, peca):
        self.session.delete(peca)
        self.session.commit()

    def contar(self):
        return self.session.query(Part).count()

    def gerar_codigo(self):
        count = self.contar()
        return f"PEC{count + 1:04d}"
