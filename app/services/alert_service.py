import logging

from db import safe_commit

log = logging.getLogger(__name__)
from datetime import datetime, timedelta

from app.models import Alert, Printer


class AlertService:
    def __init__(self, session):
        self.session = session

    def listar_todos(self, apenas_pendentes=False):
        query = self.session.query(Alert).order_by(Alert.created_at.desc())
        if apenas_pendentes:
            query = query.filter(Alert.resolvido == False)
        return query.all()

    def listar_por_impressora(self, printer_id):
        return self.session.query(Alert).filter(
            Alert.printer_id == printer_id
        ).order_by(Alert.created_at.desc()).all()

    def buscar_por_id(self, alert_id):
        return self.session.query(Alert).filter(Alert.id == alert_id).first()

    def criar(self, printer_id, tipo, titulo, descricao="", data_alerta=None):
        alerta = Alert(
            printer_id=printer_id,
            tipo=tipo,
            titulo=titulo,
            descricao=descricao,
            data_alerta=data_alerta or datetime.now(),
        )
        self.session.add(alerta)
        safe_commit(self.session)
        return alerta

    def resolver(self, alerta, user_id=None):
        alerta.resolvido = True
        alerta.resolvido_em = datetime.now()
        alerta.resolvido_por = user_id
        safe_commit(self.session)

    def excluir(self, alerta):
        self.session.delete(alerta)
        safe_commit(self.session)

    def contar_pendentes(self):
        return self.session.query(Alert).filter(Alert.resolvido == False).count()

    def gerar_alertas_revisao(self, dias_limite=30):
        hoje = datetime.now()
        limite = hoje + timedelta(days=dias_limite)
        printers = self.session.query(Printer).filter(
            Printer.proxima_revisao <= limite
        ).all()
        criados = 0
        for p in printers:
            if not p.proxima_revisao:
                continue
            existente = self.session.query(Alert).filter(
                Alert.printer_id == p.id,
                Alert.tipo == "revisao",
                Alert.resolvido == False
            ).first()
            if existente:
                continue
            self.criar(
                printer_id=p.id,
                tipo="revisao",
                titulo=f"Revisão próxima: {p.patrimonio}",
                descricao=f"Impressora {p.modelo} ({p.patrimonio}) precisa de revisão até {p.proxima_revisao.strftime('%d/%m/%Y')}",
                data_alerta=p.proxima_revisao,
            )
            criados += 1
        return criados

    def verificar_estoque_baixo(self):
        from app.models import Part
        from sqlalchemy import or_
        partes = self.session.query(Part).filter(
            or_(
                Part.quantidade_estoque <= 0,
                Part.quantidade_estoque <= Part.estoque_minimo,
            )
        ).all()
        criados = 0
        for peca in partes:
            existente = self.session.query(Alert).filter(
                Alert.tipo == "estoque",
                Alert.resolvido == False,
                Alert.titulo.like(f"%{peca.nome}%"),
            ).first()
            if existente:
                continue
            printer = self.session.query(Printer).filter(
                Printer.modelo.ilike(f"%{peca.modelo_compativel}%")
            ).first()
            printer_id = printer.id if printer else "unknown"
            self.criar(
                printer_id=printer_id,
                tipo="estoque",
                titulo=f"Estoque baixo: {peca.nome}",
                descricao=f"Peça {peca.nome} (cód. {peca.codigo}) tem apenas {peca.quantidade_estoque} unidade(s) — mínimo é {peca.estoque_minimo}.",
            )
            criados += 1
        return criados

