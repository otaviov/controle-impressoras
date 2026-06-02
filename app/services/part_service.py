import logging

from db import safe_commit

log = logging.getLogger(__name__)
from app.models import Part


class PartService:
    def __init__(self, session, audit_service=None, user_id=None):
        self.session = session
        self.audit_service = audit_service
        self.user_id = user_id

    def listar_todas(self, limite=None, offset=None):
        query = self.session.query(Part).order_by(Part.nome)
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_por_codigo(self, codigo):
        return self.session.query(Part).filter(Part.codigo == codigo).first()

    def buscar_por_nome(self, nome):
        return self.session.query(Part).filter(Part.nome == nome).first()

    def buscar_por_id(self, part_id):
        return self.session.query(Part).filter(Part.id == part_id).first()

    def criar(self, codigo, nome, descricao="", modelo_compativel="", quantidade=0, estoque_minimo=1):
        peca = Part(
            codigo=codigo,
            nome=nome,
            descricao=descricao,
            modelo_compativel=modelo_compativel,
            quantidade_estoque=quantidade,
            estoque_minimo=estoque_minimo,
            preco_unitario=0.0
        )
        self.session.add(peca)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "criar", tabela_alvo="parts", registro_id=peca.id, dados_depois=peca)
        return peca

    def atualizar(self, peca, **kwargs):
        if self.audit_service:
            dados_antes = {chave: getattr(peca, chave, None) for chave in kwargs}
        for chave, valor in kwargs.items():
            if hasattr(peca, chave):
                setattr(peca, chave, valor)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "atualizar", tabela_alvo="parts", registro_id=peca.id, dados_antes=dados_antes, dados_depois=peca)

    def excluir(self, peca):
        if self.audit_service:
            self.audit_service.log(self.user_id, "excluir", tabela_alvo="parts", registro_id=peca.id, dados_antes=peca)
        self.session.delete(peca)
        safe_commit(self.session)

    def contar(self):
        return self.session.query(Part).count()

    def gerar_codigo(self):
        count = self.contar()
        return f"PEC{count + 1:04d}"

