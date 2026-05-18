from datetime import datetime, timedelta
from sqlalchemy import func
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
        self.session.commit()
        return alerta

    def resolver(self, alerta, user_id=None):
        alerta.resolvido = True
        alerta.resolvido_em = datetime.now()
        alerta.resolvido_por = user_id
        self.session.commit()

    def excluir(self, alerta):
        self.session.delete(alerta)
        self.session.commit()

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
