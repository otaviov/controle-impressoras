from app.models import Printer, Activity
from app.views.styles.theme import STATUS_MANUTENCAO, STATUS_OPERACIONAL


class DashboardService:
    def __init__(self, session):
        self.session = session

    def resumo(self):
        status_counts_raw = (
            self.session.query(Printer.status, Printer.id)
            .all()
        )
        status_counts = {}
        for s, _ in status_counts_raw:
            status_counts[s] = status_counts.get(s, 0) + 1

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
