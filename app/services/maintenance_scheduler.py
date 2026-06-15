from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy.orm import Session, selectinload

from app.models import Activity, MaintenanceSchedule, Printer
from app.utils.sanitize import sanitizar
from db import safe_commit

if TYPE_CHECKING:
    from app.services.alert_service import AlertService
    from app.services.activity_service import ActivityService
    from app.services.audit_service import AuditService

log = logging.getLogger(__name__)

PERIODOS_OPCOES: list[tuple[str, int]] = [
    ("Mensal (30 dias)", 30),
    ("Bimestral (60 dias)", 60),
    ("Trimestral (90 dias)", 90),
    ("Semestral (180 dias)", 180),
    ("Anual (365 dias)", 365),
]

PAGINAS_OPCOES: list[int] = [5000, 10000, 15000, 20000, 50000]

DIAS_AVISO_OPCOES: list[int] = [1, 3, 5, 7, 14, 30]


class MaintenanceScheduler:
    def __init__(
        self,
        session: Session,
        activity_service: Optional[ActivityService] = None,
        alert_service: Optional[AlertService] = None,
        audit_service: Optional[AuditService] = None,
        user_id: Optional[int] = None,
    ) -> None:
        self.session = session
        self.activity_service = activity_service
        self.alert_service = alert_service
        self.audit_service = audit_service
        self.user_id = user_id

    # ── CRUD ──────────────────────────────────────────────────────

    def listar_todos_ativos(self) -> list[MaintenanceSchedule]:
        return (
            self.session.query(MaintenanceSchedule)
            .filter(MaintenanceSchedule.ativo == True)
            .options(selectinload(MaintenanceSchedule.printer))
            .order_by(MaintenanceSchedule.proxima_geracao.asc().nullslast())
            .all()
        )

    def listar_por_printer(self, printer_id: str) -> list[MaintenanceSchedule]:
        return (
            self.session.query(MaintenanceSchedule)
            .filter(MaintenanceSchedule.printer_id == printer_id)
            .all()
        )

    def buscar_por_id(self, schedule_id: int) -> Optional[MaintenanceSchedule]:
        return (
            self.session.query(MaintenanceSchedule)
            .options(selectinload(MaintenanceSchedule.printer))
            .filter(MaintenanceSchedule.id == schedule_id)
            .first()
        )

    def agendar_periodo(
        self,
        printer_id: str,
        intervalo_dias: int,
        dias_aviso: int = 7,
        observacao: str = "",
    ) -> MaintenanceSchedule:
        schedule = MaintenanceSchedule(
            printer_id=printer_id,
            tipo="periodo",
            intervalo_dias=intervalo_dias,
            dias_aviso=dias_aviso,
            observacao=sanitizar(observacao),
            ativo=True,
        )
        self._recalcular_proxima(schedule)
        self.session.add(schedule)
        safe_commit(self.session)
        return schedule

    def agendar_paginas(
        self,
        printer_id: str,
        intervalo_paginas: int,
        contador_inicial: int = 0,
        dias_aviso: int = 7,
        observacao: str = "",
    ) -> MaintenanceSchedule:
        schedule = MaintenanceSchedule(
            printer_id=printer_id,
            tipo="paginas",
            intervalo_paginas=intervalo_paginas,
            contador_inicial=contador_inicial,
            contador_atual=contador_inicial,
            proxima_meta_paginas=contador_inicial + intervalo_paginas,
            dias_aviso=dias_aviso,
            observacao=sanitizar(observacao),
            ativo=True,
        )
        self.session.add(schedule)
        safe_commit(self.session)
        return schedule

    def atualizar(
        self,
        schedule_id: int,
        **kwargs: Any,
    ) -> Optional[MaintenanceSchedule]:
        schedule = self.buscar_por_id(schedule_id)
        if not schedule:
            return None
        for chave, valor in kwargs.items():
            if hasattr(schedule, chave):
                setattr(schedule, chave, valor)
        if "intervalo_dias" in kwargs or "dias_aviso" in kwargs:
            self._recalcular_proxima(schedule)
        schedule.updated_at = datetime.now()
        safe_commit(self.session)
        return schedule

    def cancelar(self, schedule_id: int) -> None:
        schedule = self.buscar_por_id(schedule_id)
        if schedule:
            schedule.ativo = False
            safe_commit(self.session)

    def reativar(self, schedule_id: int) -> None:
        schedule = self.buscar_por_id(schedule_id)
        if schedule:
            schedule.ativo = True
            self._recalcular_proxima(schedule)
            safe_commit(self.session)

    def deletar(self, schedule_id: int) -> None:
        schedule = self.buscar_por_id(schedule_id)
        if schedule:
            self.session.delete(schedule)
            safe_commit(self.session)

    # ── Verificação de vencimentos ────────────────────────────────

    def verificar_vencimentos(self) -> dict[str, int]:
        """Executa a verificação de todos os agendamentos ativos.
        Retorna contadores de: alertas_criados, os_geradas.
        """
        hoje = datetime.now()
        resultado = {"alertas_criados": 0, "os_geradas": 0}

        schedules = self.listar_todos_ativos()
        for sch in schedules:
            sch.updated_at = datetime.now()

            if sch.tipo == "periodo":
                res = self._verificar_periodo(sch, hoje)
            else:
                res = self._verificar_paginas(sch, hoje)

            resultado["alertas_criados"] += res.get("alertas", 0)
            resultado["os_geradas"] += res.get("os", 0)

        safe_commit(self.session)
        return resultado

    def _verificar_periodo(
        self, schedule: MaintenanceSchedule, hoje: datetime
    ) -> dict[str, int]:
        res = {"alertas": 0, "os": 0}
        if not schedule.proxima_geracao:
            self._recalcular_proxima(schedule)
            return res

        dias_restantes = (schedule.proxima_geracao - hoje).total_seconds() / 86400

        if dias_restantes <= schedule.dias_aviso and dias_restantes > 0:
            self._criar_alerta_aviso(schedule)
            res["alertas"] += 1

        if dias_restantes <= 0:
            self._gerar_os(schedule)
            res["os"] += 1
            res["alertas"] += self._resolver_alertas_pendentes(schedule)
            self._recalcular_proxima(schedule)

        return res

    def _verificar_paginas(
        self, schedule: MaintenanceSchedule, hoje: datetime
    ) -> dict[str, int]:
        res = {"alertas": 0, "os": 0}
        if schedule.proxima_meta_paginas is None:
            return res

        contador = schedule.contador_atual or 0
        meta = schedule.proxima_meta_paginas
        paginas_restantes = meta - contador

        if 0 < paginas_restantes <= 5000:
            self._criar_alerta_aviso(schedule, paginas_restantes)
            res["alertas"] += 1

        if contador >= meta:
            self._gerar_os(schedule)
            res["os"] += 1
            res["alertas"] += self._resolver_alertas_pendentes(schedule)
            schedule.proxima_meta_paginas = contador + (schedule.intervalo_paginas or 0)

        return res

    # ── Geração de OS ─────────────────────────────────────────────

    def _gerar_os(self, schedule: MaintenanceSchedule) -> None:
        if not self.activity_service:
            log.warning("activity_service não configurado — OS não gerada")
            return

        printer = schedule.printer
        if not printer:
            return

        atividade = self.activity_service.criar(
            printer_id=printer.id,
            kind="MANUTENCAO",
            notes=f"Manutenção programada — {printer.patrimonio}",
            status_atividade="Aberta",
            urgencia="Normal",
        )
        schedule.ultima_geracao = datetime.now()

        if self.audit_service:
            self.audit_service.log(
                self.user_id,
                "criar",
                tabela_alvo="activities",
                registro_id=atividade.id,
                dados_depois=atividade,
            )

        log.info("OS #%s gerada para impressora %s", atividade.id, printer.patrimonio)

    # ── Alertas ───────────────────────────────────────────────────

    def _criar_alerta_aviso(
        self, schedule: MaintenanceSchedule, paginas_restantes: Optional[int] = None
    ) -> None:
        if not self.alert_service:
            return
        printer = schedule.printer
        if not printer:
            return

        if paginas_restantes is not None:
            titulo = f"Manutenção por páginas: {printer.patrimonio}"
            desc = (
                f"Impressora {printer.modelo} ({printer.patrimonio}) — "
                f"{paginas_restantes} páginas restantes para a manutenção."
            )
        else:
            titulo = f"Manutenção periódica próxima: {printer.patrimonio}"
            desc = (
                f"Impressora {printer.modelo} ({printer.patrimonio}) — "
                f"revisão programada para "
                f"{schedule.proxima_geracao.strftime('%d/%m/%Y')}."
            )

        from app.models import Alert

        ja_existe = (
            self.session.query(Alert)
            .filter(
                Alert.printer_id == printer.id,
                Alert.tipo == "revisao",
                Alert.resolvido == False,
                Alert.titulo.like(f"%{titulo}%"),
            )
            .first()
        )
        if ja_existe:
            return

        self.alert_service.criar(
            printer_id=printer.id,
            tipo="revisao",
            titulo=titulo,
            descricao=desc,
            data_agendada=schedule.proxima_geracao,
        )

    def _resolver_alertas_pendentes(self, schedule: MaintenanceSchedule) -> int:
        if not self.alert_service:
            return 0
        from app.models import Alert

        alerts = (
            self.session.query(Alert)
            .filter(
                Alert.printer_id == schedule.printer_id,
                Alert.tipo == "revisao",
                Alert.resolvido == False,
            )
            .all()
        )
        for a in alerts:
            self.alert_service.resolver(a, user_id=self.user_id)
        return len(alerts)

    # ── Cálculo de datas futuras ──────────────────────────────────

    def _recalcular_proxima(self, schedule: MaintenanceSchedule) -> None:
        if schedule.tipo == "periodo":
            if schedule.ultima_geracao:
                base = schedule.ultima_geracao
            else:
                base = datetime.now()
            dias = schedule.intervalo_dias or 30
            schedule.proxima_geracao = base + timedelta(days=dias)

    # ── Eventos para calendário ───────────────────────────────────

    def listar_eventos(
        self, inicio: datetime, fim: datetime
    ) -> list[dict[str, Any]]:
        schedules = (
            self.session.query(MaintenanceSchedule)
            .filter(MaintenanceSchedule.ativo == True)
            .options(selectinload(MaintenanceSchedule.printer))
            .all()
        )
        eventos: list[dict[str, any]] = []
        for sch in schedules:
            printer = sch.printer
            if not printer or not sch.proxima_geracao:
                continue
            if inicio <= sch.proxima_geracao <= fim:
                eventos.append(
                    {
                        "data": sch.proxima_geracao,
                        "printer_id": printer.id,
                        "printer_patrimonio": printer.patrimonio,
                        "printer_modelo": printer.modelo or "",
                        "tipo": sch.tipo,
                        "intervalo_dias": sch.intervalo_dias,
                        "intervalo_paginas": sch.intervalo_paginas,
                        "dias_aviso": sch.dias_aviso,
                        "ultima_geracao": sch.ultima_geracao,
                        "observacao": sch.observacao,
                        "schedule_id": sch.id,
                    }
                )
        return eventos

    # ── Atualização do contador de páginas ────────────────────────

    def atualizar_contador_paginas(
        self, schedule_id: int, novo_contador: int
    ) -> None:
        schedule = self.buscar_por_id(schedule_id)
        if schedule:
            schedule.contador_atual = novo_contador
            safe_commit(self.session)
