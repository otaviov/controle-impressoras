from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from config import DATA_DIR

log = logging.getLogger(__name__)

MONITORING_CONFIG_PATH: Path = DATA_DIR / "monitoring_config.json"


@dataclass
class MonitoringConfig:
    enabled: bool = False
    interval_seconds: int = 300
    ping_timeout_ms: int = 2000
    ping_retries: int = 2
    snmp_community: str = "public"
    snmp_port: int = 161
    snmp_timeout_s: int = 3
    offline_threshold: int = 3
    toner_warn_percent: int = 15
    auto_alert_offline: bool = True
    auto_alert_toner: bool = True

    @classmethod
    def carregar(cls) -> MonitoringConfig:
        if MONITORING_CONFIG_PATH.exists():
            try:
                dados = json.loads(MONITORING_CONFIG_PATH.read_text("utf-8"))
                return cls(**dados)
            except Exception as e:
                log.warning("Erro ao carregar config de monitoramento: %s", e)
        return cls()

    def salvar(self) -> None:
        MONITORING_CONFIG_PATH.write_text(
            json.dumps(self._asdict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _asdict(self) -> dict:
        return {
            "enabled": self.enabled,
            "interval_seconds": self.interval_seconds,
            "ping_timeout_ms": self.ping_timeout_ms,
            "ping_retries": self.ping_retries,
            "snmp_community": self.snmp_community,
            "snmp_port": self.snmp_port,
            "snmp_timeout_s": self.snmp_timeout_s,
            "offline_threshold": self.offline_threshold,
            "toner_warn_percent": self.toner_warn_percent,
            "auto_alert_offline": self.auto_alert_offline,
            "auto_alert_toner": self.auto_alert_toner,
        }
