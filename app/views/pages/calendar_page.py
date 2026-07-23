from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from app.models import Activity, Alert, Printer
from app.services.maintenance_scheduler import MaintenanceScheduler
from app.views.widgets.table_widget import tornar_interativa

log = logging.getLogger(__name__)

_DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
_MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]

_STATUS_GRUPOS: dict[str, tuple[str, str, str]] = {
    "Aberta": ("Em Aberto", "#60a5fa", "⏱"),
    "Aguardando Peça": ("Em Aberto", "#60a5fa", "⏱"),
    "Aguardando Aprovação": ("Em Aberto", "#60a5fa", "⏱"),
    "Técnico Designado": ("Em Progresso", "#f59e0b", "🔄"),
    "Em Deslocamento": ("Em Progresso", "#f59e0b", "🔄"),
    "Em Manutenção": ("Em Progresso", "#f59e0b", "🔄"),
    "Em Atendimento": ("Em Progresso", "#f59e0b", "🔄"),
    "Concluido": ("Concluído", "#34d399", "✅"),
    "Verificada": ("Concluído", "#34d399", "✅"),
}
_STATUS_AGENDADO = ("Em Aberto", "#60a5fa", "⏱")
_STATUS_ATRASADO = ("Atrasada", "#f38ba8", "⚠")


class _DayCell(QFrame):
    def __init__(self, dia: int, mes_atual: bool, hoje: bool, selecionado: bool,
                 cores_dot: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._callback = None
        self.setFixedSize(64, 44)
        self.setCursor(Qt.PointingHandCursor)

        cor_texto = "#3a3a4e" if not mes_atual else "#e2e8f0"
        if selecionado:
            cor_texto = "#ffffff"

        self.setObjectName("dayCell")

        if selecionado:
            bg = "background: rgba(99,102,241,0.35);"
            borda = "1px solid #6366f1;"
        elif hoje:
            bg = "background: transparent;"
            borda = "1.5px solid #6366f1;"
        else:
            bg = "background: transparent;"
            borda = "1px solid transparent;"

        self.setStyleSheet(
            f"QFrame#dayCell {{ {bg} border: {borda} border-radius: 8px; }}"
            f" QFrame#dayCell:hover {{ background: rgba(99,102,241,0.15); }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 4, 2, 2)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        lbl_dia = QLabel(str(dia))
        lbl_dia.setAlignment(Qt.AlignCenter)
        peso = "700" if (hoje or selecionado) else "600"
        lbl_dia.setStyleSheet(
            f"color: {cor_texto}; font-size: 13px; font-weight: {peso}; background: transparent; border: none;"
        )
        layout.addWidget(lbl_dia)

        if cores_dot:
            dots_row = QHBoxLayout()
            dots_row.setSpacing(3)
            dots_row.setAlignment(Qt.AlignCenter)
            for cor in cores_dot[:3]:
                dot = QLabel()
                dot.setFixedSize(5, 5)
                dot.setStyleSheet(f"background-color: {cor}; border-radius: 2px; border: none;")
                dots_row.addWidget(dot)
            layout.addLayout(dots_row)

    def set_click(self, callback) -> None:
        self._callback = callback

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._callback:
            self._callback()
        super().mousePressEvent(event)


class CalendarPage(QWidget):
    signal_trocar_pagina = Signal(str, object)
    abrir_atividade = Signal(int)
    abrir_impressora = Signal(str)

    def __init__(
        self,
        scheduler: MaintenanceScheduler,
        activity_service: Any = None,
        technician_service: Any = None,
        alert_service: Any = None,
        printer_service: Any = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.scheduler = scheduler
        self.activity_service = activity_service
        self.technician_service = technician_service
        self.alert_service = alert_service
        self.printer_service = printer_service

        hoje = datetime.now()
        self._mes_atual = QDate(hoje.year, hoje.month, 1)
        self._data_selecionada = QDate(hoje.year, hoje.month, hoje.day)
        self._eventos_por_data: dict[str, list[dict[str, Any]]] = {}
        self._eventos_da_tabela: list[dict[str, Any]] = []

        self._inicializar_ui()
        self._recarregar_tudo()

    # UI 
    def _inicializar_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 10)
        header.setSpacing(10)

        # Ícone do Flaticon carregado via arquivo
        icone_label = QLabel()
        pixmap = QPixmap("anexos/calendar_icon.png")
        pixmap_redimensionado = pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icone_label.setPixmap(pixmap_redimensionado)
        icone_label.setStyleSheet("background: transparent; border: none;")

        titulo = QLabel("Calendário de Manutenções")
        titulo.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #e8e8f0; background: transparent; border: none;"
        )
        
        header.addWidget(icone_label)
        header.addWidget(titulo)
        header.addStretch()

        btn_hoje = QPushButton("Hoje")
        btn_hoje.setCursor(Qt.PointingHandCursor)
        btn_hoje.setStyleSheet(
            "QPushButton { background: transparent; color: #e8e8f0; border: 1px solid #2a2a3e;"
            " border-radius: 8px; padding: 6px 16px; font-size: 12px; font-weight: 600; }"
            " QPushButton:hover { background: #1e1e2e; border-color: #6366f1; }"
        )
        btn_hoje.clicked.connect(self._ir_para_hoje)
        header.addWidget(btn_hoje)
        layout.addLayout(header)

        # ── Card Calendário ──
        cal_card = QFrame()
        cal_card.setObjectName("calCard")
        cal_card.setStyleSheet(
            "QFrame#calCard { background-color: #14141f; border: 1px solid #2a2a3e; border-radius: 14px; }"
        )
        cal_layout = QVBoxLayout(cal_card)
        cal_layout.setContentsMargins(16, 12, 16, 14)
        cal_layout.setSpacing(8)

        nav_row = QHBoxLayout()
        btn_prev = QPushButton("<")
        btn_prev.setFixedSize(28, 28)
        btn_prev.setCursor(Qt.PointingHandCursor)
        btn_prev.setStyleSheet(self._estilo_seta())
        btn_prev.clicked.connect(lambda: self._mudar_mes(-1))

        self._lbl_mes = QLabel()
        self._lbl_mes.setAlignment(Qt.AlignCenter)
        self._lbl_mes.setStyleSheet(
            "color: #e8e8f0; font-size: 15px; font-weight: 700; background: transparent; border: none;"
        )

        btn_next = QPushButton(">")
        btn_next.setFixedSize(28, 28)
        btn_next.setCursor(Qt.PointingHandCursor)
        btn_next.setStyleSheet(self._estilo_seta())
        btn_next.clicked.connect(lambda: self._mudar_mes(1))

        nav_row.addStretch()
        nav_row.addWidget(btn_prev)
        nav_row.addWidget(self._lbl_mes)
        nav_row.addWidget(btn_next)
        nav_row.addStretch()
        cal_layout.addLayout(nav_row)

        semana_row = QHBoxLayout()
        semana_row.setSpacing(0)
        for i, dia in enumerate(_DIAS_SEMANA):
            lbl = QLabel(dia)
            lbl.setAlignment(Qt.AlignCenter)
            cor = "#f38ba8" if i >= 5 else "#717182"
            lbl.setStyleSheet(
                f"color: {cor}; font-size: 10px; font-weight: 700; background: transparent; border: none;"
            )
            lbl.setFixedWidth(64)
            semana_row.addWidget(lbl)
        cal_layout.addLayout(semana_row)

        self._grid = QGridLayout()
        self._grid.setSpacing(3)
        cal_layout.addLayout(self._grid)

        layout.addWidget(cal_card)

        # ── Área de Detalhes ──
        detalhes_card = QFrame()
        detalhes_card.setObjectName("detalhesCard")
        detalhes_card.setStyleSheet(
            "QFrame#detalhesCard { background-color: #14141f; border: 1px solid #2a2a3e; border-radius: 12px; }"
        )
        detalhes_layout = QVBoxLayout(detalhes_card)
        detalhes_layout.setContentsMargins(16, 12, 16, 12)
        detalhes_layout.setSpacing(8)

        self._detalhes_label = QLabel("Selecione uma data para ver os eventos")
        self._detalhes_label.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #a6adc8; background: transparent; border: none;"
        )
        detalhes_layout.addWidget(self._detalhes_label)

        self._tabela_eventos = QTableWidget()
        self._tabela_eventos.setColumnCount(5)
        self._tabela_eventos.setHorizontalHeaderLabels(
            ["Impressora", "Tipo", "Previsão", "Status", "Observação"]
        )
        self._tabela_eventos.setStyleSheet("""
            QTableWidget { background-color: transparent; border: none;
                color: #cdd6f4; gridline-color: transparent; font-size: 13px; }
            QTableWidget::item { padding: 8px 10px; border-bottom: 1px solid #1e1e2e; }
            QTableWidget::item:hover { background-color: rgba(99,102,241,0.1); }
            QTableWidget::item:selected { background-color: rgba(99,102,241,0.15); color: #818cf8; }
            QHeaderView::section { background-color: transparent; color: #717182; font-weight: 700;
                border: none; border-bottom: 1px solid #2a2a3e; padding: 8px 10px;
                font-size: 11px; }
        """)
        self._tabela_eventos.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabela_eventos.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabela_eventos.verticalHeader().setVisible(False)
        self._tabela_eventos.verticalHeader().setDefaultSectionSize(42)
        self._tabela_eventos.setShowGrid(False)
        self._tabela_eventos.setFocusPolicy(Qt.NoFocus)
        self._tabela_eventos.setAlternatingRowColors(True)
        
        # Ajusta a política de tamanho para expandir totalmente na horizontal
        self._tabela_eventos.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        tornar_interativa(self._tabela_eventos)

        self._tabela_eventos.doubleClicked.connect(self._ao_duplo_clique)
        detalhes_layout.addWidget(self._tabela_eventos, 1)

        layout.addWidget(detalhes_card, 1)

    def _estilo_seta(self) -> str:
        return (
            "QPushButton { background: transparent; color: #e8e8f0; border: 1px solid #2a2a3e;"
            " border-radius: 6px; font-size: 16px; font-weight: 700; padding: 0; }"
            " QPushButton:hover { background: #1e1e2e; color: #ffffff; border-color: #6366f1; }"
        )

    # ── Navegação ──────────────────────────────────────────────
    def _mudar_mes(self, delta: int) -> None:
        self._mes_atual = self._mes_atual.addMonths(delta)
        self._recarregar_tudo()

    def _ir_para_hoje(self) -> None:
        hoje = datetime.now()
        self._mes_atual = QDate(hoje.year, hoje.month, 1)
        self._data_selecionada = QDate(hoje.year, hoje.month, hoje.day)
        self._recarregar_tudo()

    def recarregar(self) -> None:
        self._recarregar_tudo()

    # ── Dados ──────────────────────────────────────────────────
    def _recarregar_tudo(self) -> None:
        self._carregar_eventos()
        self._montar_grid()
        self._mostrar_eventos_do_dia(self._data_selecionada)

    def _carregar_eventos(self) -> None:
        primeiro_dia_grid = self._mes_atual.addDays(-(self._mes_atual.dayOfWeek() - 1))
        ultimo_dia_grid = primeiro_dia_grid.addDays(41)
        inicio = datetime(primeiro_dia_grid.year(), primeiro_dia_grid.month(), primeiro_dia_grid.day())
        fim = datetime(ultimo_dia_grid.year(), ultimo_dia_grid.month(), ultimo_dia_grid.day(), 23, 59, 59)

        self._eventos_por_data = {}

        # ── Agendamentos avulsos (Printer.proxima_revisao) ──
        if self.printer_service:
            try:
                printers = (
                    self.printer_service.session.query(Printer)
                    .filter(
                        Printer.deleted_at.is_(None),
                        Printer.proxima_revisao >= inicio,
                        Printer.proxima_revisao <= fim,
                    )
                    .all()
                )
                for p in printers:
                    if not p.proxima_revisao:
                        continue
                    chave = p.proxima_revisao.strftime("%Y-%m-%d")
                    atrasado = p.proxima_revisao < datetime.now()
                    status = _STATUS_ATRASADO if atrasado else _STATUS_AGENDADO
                    self._eventos_por_data.setdefault(chave, []).append({
                        "impressora": p.patrimonio,
                        "tipo": "Agendamento",
                        "previsao": p.proxima_revisao,
                        "status_label": status[0],
                        "status_cor": status[1],
                        "status_icone": status[2],
                        "observacao": p.urgencia_prox_manutencao or "-",
                        "activity_id": None,
                        "alert_id": None,
                        "printer_patrimonio": p.patrimonio,
                    })
            except Exception:
                log.warning("Erro ao buscar agendamentos avulsos para calendário", exc_info=True)

        # ── Agendamentos recorrentes ──
        for ev in self.scheduler.listar_eventos(inicio, fim):
            data = ev["data"]
            if not data:
                continue
            atrasado = data < datetime.now()
            status = _STATUS_ATRASADO if atrasado else _STATUS_AGENDADO
            chave = data.strftime("%Y-%m-%d")
            self._eventos_por_data.setdefault(chave, []).append({
                "impressora": ev["printer_patrimonio"],
                "tipo": "Preventiva" if ev["tipo"] == "periodo" else "Preventiva (páginas)",
                "previsao": data,
                "status_label": status[0],
                "status_cor": status[1],
                "status_icone": status[2],
                "observacao": ev.get("observacao") or "-",
                "activity_id": None,
                "alert_id": None,
                "printer_patrimonio": ev["printer_patrimonio"],
            })

        # ── OS de manutenção reais ──
        if self.activity_service:
            try:
                atividades = (
                    self.activity_service.session.query(Activity)
                    .filter(
                        Activity.deleted_at.is_(None),
                        Activity.kind == "MANUTENCAO",
                        Activity.event_at >= inicio,
                        Activity.event_at <= fim,
                    )
                    .all()
                )
                for a in atividades:
                    if not a.event_at:
                        continue
                    chave = a.event_at.strftime("%Y-%m-%d")
                    status = _STATUS_GRUPOS.get(a.status_atividade or "Aberta", _STATUS_AGENDADO)
                    pat = a.printer.patrimonio if a.printer else (a.printer_id or "-")

                    self._eventos_por_data.setdefault(chave, []).append({
                        "impressora": pat,
                        "tipo": "Corretiva",
                        "previsao": a.event_at,
                        "status_label": status[0],
                        "status_cor": status[1],
                        "status_icone": status[2],
                        "observacao": a.notes or "—",
                        "activity_id": a.id,
                        "alert_id": None,
                        "printer_patrimonio": pat,
                    })
            except Exception:
                log.warning("Erro ao buscar atividades para calendário", exc_info=True)

        # ── Alertas agendados ──
        if self.alert_service:
            try:
                alertas = (
                    self.alert_service.session.query(Alert)
                    .filter(
                        Alert.deleted_at.is_(None),
                        Alert.resolvido == False,
                        Alert.data_agendada >= inicio,
                        Alert.data_agendada <= fim,
                    )
                    .all()
                )
                for al in alertas:
                    if not al.data_agendada:
                        continue
                    chave = al.data_agendada.strftime("%Y-%m-%d")
                    atrasado = al.data_agendada < datetime.now()
                    status = _STATUS_ATRASADO if atrasado else _STATUS_AGENDADO
                    pat = al.printer.patrimonio if al.printer else "-"

                    self._eventos_por_data.setdefault(chave, []).append({
                        "impressora": pat,
                        "tipo": al.titulo or "Revisão",
                        "previsao": al.data_agendada,
                        "status_label": status[0],
                        "status_cor": status[1],
                        "status_icone": status[2],
                        "observacao": al.descricao or "-",
                        "activity_id": None,
                        "alert_id": al.id,
                        "printer_patrimonio": pat,
                    })
            except Exception:
                log.warning("Erro ao buscar alertas para calendário", exc_info=True)

    def _montar_grid(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._lbl_mes.setText(
            f"{_MESES_PT[self._mes_atual.month() - 1]} {self._mes_atual.year()}"
        )

        primeiro_dia_grid = self._mes_atual.addDays(-(self._mes_atual.dayOfWeek() - 1))
        qhoje = QDate.currentDate()

        cores_ordem = {"#f38ba8": 0, "#f59e0b": 1, "#60a5fa": 2, "#34d399": 3}

        for i in range(42):
            data = primeiro_dia_grid.addDays(i)
            chave = data.toString("yyyy-MM-dd")
            eventos = self._eventos_por_data.get(chave, [])
            cores = sorted(
                {ev["status_cor"] for ev in eventos},
                key=lambda c: cores_ordem.get(c, 9),
            )

            cell = _DayCell(
                dia=data.day(),
                mes_atual=(data.month() == self._mes_atual.month()),
                hoje=(data == qhoje),
                selecionado=(data == self._data_selecionada),
                cores_dot=cores,
            )
            cell.set_click(lambda d=data: self._selecionar_data(d))
            self._grid.addWidget(cell, i // 7, i % 7)

    def _selecionar_data(self, data: QDate) -> None:
        self._data_selecionada = data
        self._montar_grid()
        self._mostrar_eventos_do_dia(data)

    def _mostrar_eventos_do_dia(self, data: QDate) -> None:
        chave = data.toString("yyyy-MM-dd")
        eventos = self._eventos_por_data.get(chave, [])

        if not eventos:
            self._detalhes_label.setText(f"Nenhum evento em {data.toString('dd/MM/yyyy')}")
            self._tabela_eventos.setRowCount(0)
            self._eventos_da_tabela = []
            return

        self._detalhes_label.setText(
            f"Manutenções para {data.toString('dd/MM/yyyy')} — {len(eventos)} evento(s)"
        )
        eventos = sorted(eventos, key=lambda e: e["previsao"])
        self._eventos_da_tabela = eventos
        self._tabela_eventos.setRowCount(len(eventos))

        for i, ev in enumerate(eventos):
            self._tabela_eventos.setItem(i, 0, self._item(ev["impressora"]))
            self._tabela_eventos.setItem(i, 1, self._item(ev["tipo"]))
            self._tabela_eventos.setItem(i, 2, self._item(ev["previsao"].strftime("%H:%M")))

            status_item = QTableWidgetItem(f"{ev['status_icone']}  {ev['status_label']}")
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(ev["status_cor"]))
            self._tabela_eventos.setItem(i, 3, status_item)

            obs_item = QTableWidgetItem(ev["observacao"])
            self._tabela_eventos.setItem(i, 4, obs_item)

        # Removido o resizeColumnsToContents antigo que forçava encolhimento, 
        # mantendo o Stretch ativo para preencher a largura de ponta a ponta.

    def _ao_duplo_clique(self) -> None:
        row = self._tabela_eventos.currentRow()
        if row < 0 or row >= len(self._eventos_da_tabela):
            return
        ev = self._eventos_da_tabela[row]
        try:
            if ev.get("activity_id"):
                self.abrir_atividade.emit(ev["activity_id"])
            elif ev.get("printer_patrimonio") and ev["printer_patrimonio"] != "-":
                self.abrir_impressora.emit(ev["printer_patrimonio"])
        except Exception:
            log.warning("Erro ao navegar a partir do calendário", exc_info=True)

    def _item(self, texto: str) -> QTableWidgetItem:
        item = QTableWidgetItem(str(texto))
        item.setTextAlignment(Qt.AlignCenter)
        return item