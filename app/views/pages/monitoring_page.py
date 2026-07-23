from __future__ import annotations

import logging
from datetime import datetime as dt
from typing import Any

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from app.services.snmp_service import SnmpMonitorService
from app.views.styles.theme import (
    ESTILO_BOTAO_PRIMARIO,
    ESTILO_BOTAO_SECUNDARIO,
    ESTILO_BOTAO_SUCESSO,
    ESTILO_INPUT,
    ESTILO_LABEL_CAMPO,
    ESTILO_SUBTITULO,
    ESTILO_TITULO_PAGINA,
    configurar_combo,
)
from app.views.widgets.table_widget import TabelaPadrao

log = logging.getLogger(__name__)


class MonitoringPage(QWidget):
    def __init__(self, session: Session, monitor_service: SnmpMonitorService | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        self.monitor_service = monitor_service or SnmpMonitorService(session)
        self.config = self.monitor_service.config

        self._timer: QTimer | None = None
        self._em_execucao = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        header.setSpacing(10)
        
        icone_label = QLabel()
        pixmap = QPixmap("anexos/monitoramento_icon.png") 
        if not pixmap.isNull():
            pixmap_redimensionado = pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icone_label.setPixmap(pixmap_redimensionado)
        icone_label.setStyleSheet("background: transparent; border: none;")

        titulo_col = QVBoxLayout()
        titulo_col.setSpacing(2)
        titulo = QLabel("Monitoramento de Rede")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        titulo_col.addWidget(titulo)
        sub = QLabel("Monitore status, toner e páginas das impressoras via rede")
        sub.setStyleSheet(ESTILO_SUBTITULO)
        titulo_col.addWidget(sub)
        
        header.addWidget(icone_label)
        header.addLayout(titulo_col)
        header.addStretch()

        self.btn_alternar = QPushButton("▶ Iniciar")
        self.btn_alternar.setCursor(Qt.PointingHandCursor)
        self.btn_alternar.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
        self.btn_alternar.clicked.connect(self._alternar)
        header.addWidget(self.btn_alternar)

        self.btn_verificar_agora = QPushButton("🔄 Verificar Agora")
        self.btn_verificar_agora.setCursor(Qt.PointingHandCursor)
        self.btn_verificar_agora.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        self.btn_verificar_agora.clicked.connect(self._verificar_agora)
        header.addWidget(self.btn_verificar_agora)
        layout.addLayout(header)

        # Stats bar
        stats_bar = QHBoxLayout()
        stats_bar.setSpacing(20)

        self._stats_online = self._stat_card("🟢 Online", "0")
        self._stats_offline = self._stat_card("🔴 Offline", "0")
        self._stats_toner = self._stat_card("🟡 Toner Baixo", "0")
        self._stats_total = self._stat_card("📊 Total", "0")

        stats_bar.addWidget(self._stats_online)
        stats_bar.addWidget(self._stats_offline)
        stats_bar.addWidget(self._stats_toner)
        stats_bar.addWidget(self._stats_total)
        layout.addLayout(stats_bar)

        # ── Config ───────────────────────────────────────────
        config_frame = QFrame()
        config_frame.setStyleSheet(
            "QFrame { background: rgba(14,14,22,0.6); border: 1px solid #2a2a3e;"
            " border-radius: 8px; }"
        )
        config_layout = QVBoxLayout(config_frame)
        config_layout.setContentsMargins(16, 12, 16, 12)
        config_layout.setSpacing(8)

        config_label = QLabel("CONFIGURAÇÕES DE MONITORAMENTO")
        config_label.setStyleSheet("color: #6366f1; font-size: 9px; font-weight: 700; letter-spacing: 1.2px; background: transparent;")
        config_layout.addWidget(config_label)

        config_grid = QHBoxLayout()
        config_grid.setSpacing(16)

        config_grid.addWidget(self._config_field("Intervalo (s)", self._criar_spinner(self.config.interval_seconds, 30, 3600, self._salvar_intervalo)))
        config_grid.addWidget(self._config_field("Timeout (ms)", self._criar_spinner(self.config.ping_timeout_ms, 500, 10000, self._salvar_timeout)))
        config_grid.addWidget(self._config_field("Tentativas", self._criar_spinner(self.config.ping_retries, 1, 5, self._salvar_retries)))
        config_grid.addWidget(self._config_field("SNMP Community", self._criar_combo(["public", "private", "internal"], self.config.snmp_community, self._salvar_community)))
        config_layout.addLayout(config_grid)

        layout.addWidget(config_frame)

        # ── Tabela ───────────────────────────────────────────
        colunas = ["Patrimônio", "Modelo", "IP", "Status", "Ping (ms)", "Toner", "Última Verificação"]
        self.tabela = TabelaPadrao(colunas)
        self.tabela.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabela)

        self._atualizar_tabela()

        # Auto-start se habilitado
        if self.config.enabled:
            self._iniciar()

    # ── Helpers ─────────────────────────────────────────────

    def _stat_card(self, titulo: str, valor: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: rgba(14,14,22,0.6); border: 1px solid #2a2a3e;"
            " border-radius: 10px; }"
        )
        card.setMinimumWidth(140)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 12, 16, 12)
        c_layout.setSpacing(4)
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("color: #717182; font-size: 11px; font-weight: 600; background: transparent;")
        c_layout.addWidget(lbl_titulo)
        lbl_valor = QLabel(valor)
        lbl_valor.setStyleSheet("color: #e8e8f0; font-size: 24px; font-weight: 700; background: transparent;")
        c_layout.addWidget(lbl_valor)
        return card

    def _config_field(self, label: str, widget: QWidget) -> QFrame:
        frame = QFrame()
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #94949f; font-size: 10px; font-weight: 600; background: transparent;")
        lay.addWidget(lbl)
        lay.addWidget(widget)
        return frame

    def _criar_spinner(self, valor: int, minimo: int, maximo: int, callback) -> QSpinBox:
        sp = QSpinBox()
        sp.setValue(valor)
        sp.setRange(minimo, maximo)
        sp.setStyleSheet(ESTILO_INPUT)
        sp.valueChanged.connect(callback)
        return sp

    def _criar_combo(self, items: list[str], current: str, callback) -> QComboBox:
        cb = QComboBox()
        configurar_combo(cb)
        cb.addItems(items)
        cb.setCurrentText(current)
        cb.currentTextChanged.connect(callback)
        return cb

    # ── Config salvar ───────────────────────────────────────

    def _salvar_intervalo(self, val: int) -> None:
        self.config.interval_seconds = val
        self.config.salvar()
        if self._timer:
            self._timer.setInterval(val * 1000)

    def _salvar_timeout(self, val: int) -> None:
        self.config.ping_timeout_ms = val
        self.config.salvar()

    def _salvar_retries(self, val: int) -> None:
        self.config.ping_retries = val
        self.config.salvar()

    def _salvar_community(self, val: str) -> None:
        self.config.snmp_community = val
        self.config.salvar()

    # ── Controle do timer ───────────────────────────────────

    def _alternar(self) -> None:
        if self._timer and self._timer.isActive():
            self._parar()
        else:
            self._iniciar()

    def _iniciar(self) -> None:
        self.config.enabled = True
        self.config.salvar()
        self.btn_alternar.setText("⏸ Pausar")
        self.btn_alternar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._verificar_agora)
        self._timer.start(self.config.interval_seconds * 1000)
        log.info("Monitoramento iniciado (intervalo=%ds)", self.config.interval_seconds)
        self._verificar_agora()

    def _parar(self) -> None:
        self.config.enabled = False
        self.config.salvar()
        if self._timer:
            self._timer.stop()
        self.btn_alternar.setText("▶ Iniciar")
        self.btn_alternar.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
        log.info("Monitoramento pausado")

    def _verificar_agora(self) -> None:
        if self._em_execucao:
            return
        self._em_execucao = True
        self.btn_verificar_agora.setEnabled(False)
        self.btn_verificar_agora.setText("🔄 Verificando...")
        try:
            self.monitor_service.verificar_todas()
            self._atualizar_tabela()
        except Exception as e:
            log.exception("Erro na verificacao de rede")
        finally:
            self._em_execucao = False
            self.btn_verificar_agora.setEnabled(True)
            self.btn_verificar_agora.setText("🔄 Verificar Agora")

    # ── Tabela ──────────────────────────────────────────────

    def _atualizar_tabela(self) -> None:
        from app.models.printer import Printer
        impressoras = self.session.query(Printer).all()
        online = offline = toner_baixo = 0

        self.tabela.setRowCount(len(impressoras))
        for i, p in enumerate(impressoras):
            status = self.monitor_service.ultima_leitura(p.id)

            self.tabela.setItem(i, 0, QTableWidgetItem(p.patrimonio or "—"))
            self.tabela.setItem(i, 1, QTableWidgetItem(p.modelo or "—"))
            host = p.ip_rede or "—"
            self.tabela.setItem(i, 2, QTableWidgetItem(host))

            if status:
                if status.is_online:
                    online += 1
                    status_text = "🟢 Online"
                    status_cor = "#a6e3a1"
                else:
                    offline += 1
                    status_text = "🔴 Offline"
                    status_cor = "#f38ba8"

                if status.toner_level is not None and status.toner_max:
                    pct = (status.toner_level / status.toner_max) * 100
                    if pct < self.config.toner_warn_percent:
                        toner_baixo += 1

                toner_txt = f"{status.toner_level or '—'}/{status.toner_max or '—'}" if status.toner_level is not None else "—"

                ping_txt = f"{status.ping_ms:.0f}ms" if status.ping_ms is not None else "—"
                ultima_txt = status.timestamp.strftime("%d/%m %H:%M") if status.timestamp else "—"
            else:
                status_text = "⚪ Desconhecido"
                status_cor = "#717182"
                toner_txt = "—"
                ping_txt = "—"
                ultima_txt = "—"

            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor(status_cor))
            self.tabela.setItem(i, 3, status_item)
            self.tabela.setItem(i, 4, QTableWidgetItem(ping_txt))
            self.tabela.setItem(i, 5, QTableWidgetItem(toner_txt))
            self.tabela.setItem(i, 6, QTableWidgetItem(ultima_txt))

        self.tabela.redimensionar()

        self._stats_online.findChildren(QLabel)[1].setText(str(online))
        self._stats_offline.findChildren(QLabel)[1].setText(str(offline))
        self._stats_toner.findChildren(QLabel)[1].setText(str(toner_baixo))
        self._stats_total.findChildren(QLabel)[1].setText(str(len(impressoras)))

    def recarregar(self) -> None:
        self._atualizar_tabela()
