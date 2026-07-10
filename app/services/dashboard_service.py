from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Activity, Alert, Printer
from app.utils.cache import cached
from app.utils.constants import STATUS_MANUTENCAO, STATUS_OPERACIONAL


class DashboardService:
    def __init__(self, session: Session) -> None:
        self.session: Session = session

    @cached(ttl=30, namespace="dashboard")
    def resumo(self) -> dict[str, int]:
        status_counts_raw = self.session.query(Printer.status, func.count(Printer.id)).group_by(Printer.status).all()
        status_counts = dict(status_counts_raw)
        total = sum(status_counts.values())
        em_manutencao = sum(status_counts.get(s, 0) for s in STATUS_MANUTENCAO)
        operacionais = sum(status_counts.get(s, 0) for s in STATUS_OPERACIONAL)
        total_atividades = self.session.query(Activity).filter(Activity.deleted_at == None).count()
        return {
            "total_impressoras": total,
            "em_manutencao": em_manutencao,
            "operacionais": operacionais,
            "total_atividades": total_atividades,
        }

    @cached(ttl=30, namespace="dashboard")
    def dados_grafico_pizza(self) -> tuple[list[str], list[int]]:
        rows = self.session.query(Printer.status, func.count(Printer.id)).group_by(Printer.status).all()
        labels = [r[0] or "Sem status" for r in rows]
        valores = [r[1] for r in rows]
        return labels, valores

    @cached(ttl=60, namespace="dashboard")
    def dados_grafico_atividades(self, meses: int = 6) -> tuple[list[str], list[int]]:
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

    @cached(ttl=60, namespace="dashboard")
    def dados_grafico_alertas(self, dias: int = 30) -> tuple[list[str], list[int]]:
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
