from datetime import datetime, timedelta

from sqlalchemy import func

from app.models import Activity, Alert, Printer
from app.views.styles.theme import STATUS_MANUTENCAO, STATUS_OPERACIONAL


class DashboardService:
    def __init__(self, session):
        self.session = session

    def resumo(self):
        status_counts_raw = self.session.query(Printer.status, func.count(Printer.id)).group_by(Printer.status).all()
        status_counts = dict(status_counts_raw)
        total = sum(status_counts.values())
        em_manutencao = sum(status_counts.get(s, 0) for s in STATUS_MANUTENCAO)
        operacionais = sum(status_counts.get(s, 0) for s in STATUS_OPERACIONAL)
        total_atividades = self.session.query(Activity).count()
        return {
            "total_impressoras": total,
            "em_manutencao": em_manutencao,
            "operacionais": operacionais,
            "total_atividades": total_atividades,
        }

    def dados_grafico_pizza(self):
        rows = self.session.query(Printer.status, func.count(Printer.id)).group_by(Printer.status).all()
        labels = [r[0] or "Sem status" for r in rows]
        valores = [r[1] for r in rows]
        return labels, valores

    def dados_grafico_atividades(self, meses=6):
        hoje = datetime.now()
        inicio = hoje.replace(day=1) - timedelta(days=meses * 30)
        rows = (
            self.session.query(
                func.strftime("%Y-%m", Activity.event_at),
                func.count(Activity.id),
            )
            .filter(Activity.event_at >= inicio)
            .group_by(func.strftime("%Y-%m", Activity.event_at))
            .order_by(func.strftime("%Y-%m", Activity.event_at))
            .all()
        )
        meses_labels = []
        valores = []
        for r in rows:
            meses_labels.append(r[0])
            valores.append(r[1])
        return meses_labels, valores

    def dados_grafico_alertas(self, dias=30):
        inicio = datetime.now() - timedelta(days=dias)
        rows = (
            self.session.query(
                func.strftime("%Y-%m-%d", Alert.created_at),
                func.count(Alert.id),
            )
            .filter(Alert.created_at >= inicio)
            .group_by(func.strftime("%Y-%m-%d", Alert.created_at))
            .order_by(func.strftime("%Y-%m-%d", Alert.created_at))
            .all()
        )
        dias_labels = []
        criados = []
        for r in rows:
            dias_labels.append(r[0])
            criados.append(r[1])
        return dias_labels, criados
