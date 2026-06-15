from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QTextCharFormat
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QCalendarWidget,
)

from app.services.maintenance_scheduler import MaintenanceScheduler


class _CalendarEventDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: Any) -> None:
        super().paint(painter, option, index)
        eventos = index.data(Qt.UserRole)
        if eventos:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            cores = {0: "#6366f1", 1: "#f59e0b", 2: "#ef4444"}
            for i in range(min(len(eventos), 3)):
                cor = QColor(cores.get(i, "#6366f1"))
                painter.setBrush(cor)
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(
                    option.rect.left() + 4 + i * 8,
                    option.rect.bottom() - 6,
                    6, 6, 3, 3,
                )
            painter.restore()


class CalendarPage(QWidget):
    signal_trocar_pagina = Signal(str, object)

    def __init__(self, scheduler: MaintenanceScheduler) -> None:
        super().__init__()
        self.scheduler = scheduler
        self._eventos_por_data: dict[str, list[dict[str, Any]]] = {}
        self._inicializar_ui()
        self._carregar_eventos()

    def _inicializar_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        titulo = QLabel("📅 Calendário de Manutenções")
        titulo.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0f0; background: transparent;")
        layout.addWidget(titulo)

        self.calendario = QCalendarWidget()
        self.calendario.setStyleSheet("""
            QCalendarWidget { background-color: #12121e; border: 1px solid #1e1e2e; border-radius: 8px; }
            QCalendarWidget QWidget { background-color: #12121e; color: #cdd6f4; }
            QCalendarWidget QToolButton { color: #cdd6f4; background: transparent; padding: 4px 8px;
                border-radius: 4px; font-weight: 600; }
            QCalendarWidget QToolButton:hover { background-color: #1e1e2e; }
            QCalendarWidget QMenu { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; }
            QCalendarWidget QSpinBox { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; }
        """)
        self.calendario.setGridVisible(False)
        self.calendario.setFirstDayOfWeek(Qt.Monday)
        self.calendario.clicked.connect(self._ao_selecionar_data)
        layout.addWidget(self.calendario)

        self._detalhes_label = QLabel("Selecione uma data para ver os eventos")
        self._detalhes_label.setStyleSheet(
            "font-size: 15px; font-weight: 600; color: #a6adc8; background: transparent; padding: 8px 0;"
        )
        layout.addWidget(self._detalhes_label)

        self._tabela_eventos = QTableWidget()
        self._tabela_eventos.setColumnCount(4)
        self._tabela_eventos.setHorizontalHeaderLabels(["Impressora", "Tipo", "Previsão", "Observação"])
        self._tabela_eventos.setStyleSheet("""
            QTableWidget { background-color: #12121e; border: 1px solid #1e1e2e; border-radius: 8px;
                color: #cdd6f4; gridline-color: #1e1e2e; }
            QTableWidget::item { padding: 6px 12px; }
            QHeaderView::section { background-color: #1e1e2e; color: #a6adc8; font-weight: 600;
                border: none; padding: 8px 12px; }
        """)
        self._tabela_eventos.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabela_eventos.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabela_eventos.verticalHeader().setVisible(False)
        self._tabela_eventos.setAlternatingRowColors(True)
        layout.addWidget(self._tabela_eventos, 1)

    def _carregar_eventos(self) -> None:
        hoje = datetime.now()
        inicio = hoje - timedelta(days=60)
        fim = hoje + timedelta(days=365)
        eventos = self.scheduler.listar_eventos(inicio, fim)

        self._eventos_por_data.clear()
        for ev in eventos:
            data = ev["data"]
            chave = data.strftime("%Y-%m-%d")
            if chave not in self._eventos_por_data:
                self._eventos_por_data[chave] = []
            self._eventos_por_data[chave].append(ev)

        fmt_verde = QTextCharFormat()
        fmt_verde.setBackground(QColor("#1a3a2a"))
        fmt_verde.setForeground(QColor("#a6e3a1"))

        for chave in self._eventos_por_data:
            qdate = QDate.fromString(chave, "yyyy-MM-dd")
            if qdate.isValid():
                self.calendario.setDateTextFormat(qdate, fmt_verde)

    def _ao_selecionar_data(self, qdate: QDate) -> None:
        chave = qdate.toString("yyyy-MM-dd")
        eventos = self._eventos_por_data.get(chave, [])

        if not eventos:
            self._detalhes_label.setText(
                f"Nenhum evento em {qdate.toString('dd/MM/yyyy')}"
            )
            self._tabela_eventos.setRowCount(0)
            return

        self._detalhes_label.setText(
            f"{len(eventos)} evento(s) em {qdate.toString('dd/MM/yyyy')}"
        )
        self._tabela_eventos.setRowCount(len(eventos))

        for i, ev in enumerate(eventos):
            pat = QTableWidgetItem(ev["printer_patrimonio"])
            pat.setTextAlignment(Qt.AlignCenter)

            if ev["tipo"] == "periodo":
                tipo_txt = f"Período ({ev['intervalo_dias']} dias)"
            else:
                tipo_txt = f"Páginas ({ev['intervalo_paginas']:,})"

            tipo_item = QTableWidgetItem(tipo_txt)
            tipo_item.setTextAlignment(Qt.AlignCenter)

            previsao = QTableWidgetItem(
                ev["data"].strftime("%d/%m/%Y") if ev["data"] else "—"
            )
            previsao.setTextAlignment(Qt.AlignCenter)

            obs = ev["observacao"] or "—"

            self._tabela_eventos.setItem(i, 0, pat)
            self._tabela_eventos.setItem(i, 1, tipo_item)
            self._tabela_eventos.setItem(i, 2, previsao)
            self._tabela_eventos.setItem(i, 3, QTableWidgetItem(obs))

        self._tabela_eventos.resizeColumnsToContents()
