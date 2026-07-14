from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.printer_health import PrinterHealth
from app.models.printer import Printer
from app.utils.monitoring_config import MonitoringConfig
from app.utils.network import ping, snmp_get_printer_info

log = logging.getLogger(__name__)


class SnmpMonitorService:
    def __init__(self, session: Session, alert_service=None, notificador=None):
        self.session = session
        self.alert_service = alert_service
        self.notificador = notificador
        self.config = MonitoringConfig.carregar()

    def verificar_impressora(self, printer: Printer) -> PrinterHealth:
        host = self._resolve_host(printer)
        ping_ms = ping(host, timeout_ms=self.config.ping_timeout_ms, retries=self.config.ping_retries)

        health = PrinterHealth(
            printer_id=printer.id,
            timestamp=datetime.utcnow(),
            is_online=ping_ms is not None,
            ping_ms=ping_ms,
        )

        if ping_ms is not None and self._snmp_disponivel():
            info = self._consultar_snmp(host)
            health.toner_level = info.get("toner_level")
            health.toner_max = info.get("toner_max")
            health.drum_life = info.get("drum_life")
            health.drum_max = info.get("drum_max")
            health.page_count = info.get("page_count")
            health.error_code = info.get("error_code")
            health.error_message = info.get("error_message")

        self.session.add(health)
        self.session.commit()
        return health

    def verificar_todas(self) -> list[PrinterHealth]:
        impressoras = self.session.query(Printer).all()
        resultados = []
        for p in impressoras:
            try:
                h = self.verificar_impressora(p)
                resultados.append(h)
            except Exception as e:
                log.exception("Erro ao verificar %s: %s", p.ip or p.hostname, e)
        if self.config.auto_alert_offline or self.config.auto_alert_toner:
            self.gerar_alertas()
        return resultados

    def gerar_alertas(self) -> None:
        if not self.alert_service:
            return
        if self.config.auto_alert_offline:
            self._alertar_offline()
        if self.config.auto_alert_toner:
            self._alertar_toner()

    def _alertar_offline(self) -> None:
        from app.models.alert import Alert
        for printer, _health in self.impressoras_offline():
            ja_tem = self.session.query(Alert).filter(
                Alert.printer_id == printer.id,
                Alert.tipo == "offline",
                Alert.resolvido == False,
                Alert.deleted_at == None,
            ).first()
            if ja_tem:
                continue
            self.alert_service.criar(
                printer_id=printer.id,
                tipo="offline",
                titulo=f"Offline: {printer.patrimonio}",
                descricao=f"Impressora {printer.modelo} ({printer.patrimonio}) não responde ao ping.",
            )
            log.info("Alerta offline criado para %s", printer.patrimonio)

    def _alertar_toner(self) -> None:
        from app.models.alert import Alert
        for printer, _health in self.impressoras_toner_baixo():
            ja_tem = self.session.query(Alert).filter(
                Alert.printer_id == printer.id,
                Alert.tipo == "toner",
                Alert.resolvido == False,
                Alert.deleted_at == None,
            ).first()
            if ja_tem:
                continue
            self.alert_service.criar(
                printer_id=printer.id,
                tipo="toner",
                titulo=f"Toner baixo: {printer.patrimonio}",
                descricao=f"Impressora {printer.modelo} ({printer.patrimonio}) está com nível de toner abaixo de {self.config.toner_warn_percent}%.",
            )
            log.info("Alerta toner criado para %s", printer.patrimonio)

    def _resolve_host(self, printer: Printer) -> str:
        return printer.ip or printer.hostname or "0.0.0.0"

    def _snmp_disponivel(self) -> bool:
        try:
            import pysnmp  # noqa: F401
            return True
        except ImportError:
            return False

    def _consultar_snmp(self, host: str) -> dict:
        if self._snmp_disponivel():
            return snmp_get_printer_info(host, community=self.config.snmp_community)
        return {}

    def ultima_leitura(self, printer_id: str) -> Optional[PrinterHealth]:
        return (
            self.session.query(PrinterHealth)
            .filter(PrinterHealth.printer_id == printer_id)
            .order_by(PrinterHealth.timestamp.desc())
            .first()
        )

    def status_atual(self, printer_id: str) -> Optional[PrinterHealth]:
        threshold = self.config.offline_threshold
        leituras = (
            self.session.query(PrinterHealth)
            .filter(PrinterHealth.printer_id == printer_id)
            .order_by(PrinterHealth.timestamp.desc())
            .limit(threshold)
            .all()
        )
        if not leituras:
            return None
        online_count = sum(1 for l in leituras if l.is_online)
        if online_count == 0:
            if leituras:
                ultima = leituras[0]
                ultima.is_online = False
                return ultima
        return leituras[0] if leituras else None

    def impressoras_offline(self) -> list[tuple[Printer, Optional[PrinterHealth]]]:
        impressoras = self.session.query(Printer).all()
        offline = []
        for p in impressoras:
            status = self.status_atual(p.id)
            if status and not status.is_online:
                offline.append((p, status))
        return offline

    def impressoras_toner_baixo(self) -> list[tuple[Printer, PrinterHealth]]:
        impressoras = self.session.query(Printer).all()
        baixo = []
        for p in impressoras:
            status = self.ultima_leitura(p.id)
            if status and status.toner_level is not None and status.toner_max:
                pct = (status.toner_level / status.toner_max) * 100
                if pct < self.config.toner_warn_percent:
                    baixo.append((p, status))
        return baixo

    def historico(self, printer_id: str, limit: int = 50) -> list[PrinterHealth]:
        return (
            self.session.query(PrinterHealth)
            .filter(PrinterHealth.printer_id == printer_id)
            .order_by(PrinterHealth.timestamp.desc())
            .limit(limit)
            .all()
        )
