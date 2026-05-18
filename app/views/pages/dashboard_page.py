from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog, QPushButton, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from app.views.styles.theme import COR, ESTILO_TITULO_PAGINA, ESTILO_SUBTITULO, STATUS_MANUTENCAO, STATUS_OPERACIONAL, STATUS_CORES
from app.views.widgets.card_widget import CardWidget
from app.utils.helpers import formatar_data


class DashboardPage(QWidget):
    signal_trocar_pagina = Signal(int)

    def __init__(self, session, printer_service, activity_service, dashboard_service, parent=None):
        super().__init__(parent)
        self.session = session
        self.printer_service = printer_service
        self.activity_service = activity_service
        self.dashboard_service = dashboard_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(0)

        # ── Header ──────────────────────────────────────────────
        header_layout = QHBoxLayout()
        titulo = QLabel("📊 Dashboard")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        header_layout.addWidget(titulo)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        subtitulo = QLabel("Visão geral do sistema de controle de impressoras")
        subtitulo.setStyleSheet(ESTILO_SUBTITULO)
        layout.addWidget(subtitulo)

        layout.addSpacing(20)

        # ── Cards ───────────────────────────────────────────────
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.card_total = CardWidget("🖨️", "Total Impressoras", "0", "#89b4fa",
            gradiente="azul",
            callback=lambda: self.signal_trocar_pagina.emit(1))
        self.card_manut = CardWidget("⚠️", "Em Manutenção", "0", "#f9e2af",
            gradiente="amarelo",
            callback=lambda: self.ao_clicar_status("manutencao"))
        self.card_op = CardWidget("✅", "Operacionais", "0", "#a6e3a1",
            gradiente="verde",
            callback=lambda: self.ao_clicar_status("operacional"))
        self.card_os = CardWidget("📋", "Atividades", "0", "#cba6f7",
            gradiente="roxo",
            callback=lambda: self.signal_trocar_pagina.emit(2))

        cards_layout.addWidget(self.card_total)
        cards_layout.addWidget(self.card_manut)
        cards_layout.addWidget(self.card_op)
        cards_layout.addWidget(self.card_os)
        layout.addLayout(cards_layout)

        layout.addStretch()

    def recarregar(self):
        dados = self.dashboard_service.resumo()
        self.card_total.atualizar_valor(dados.get("total_impressoras", 0))
        self.card_manut.atualizar_valor(dados.get("em_manutencao", 0))
        self.card_op.atualizar_valor(dados.get("operacionais", 0))
        self.card_os.atualizar_valor(dados.get("total_atividades", 0))

    def ao_clicar_status(self, tipo):
        if tipo == "manutencao":
            titulo = "⚠️ Impressoras em Manutenção"
            status_list = STATUS_MANUTENCAO
        elif tipo == "operacional":
            titulo = "✅ Impressoras Operacionais"
            status_list = STATUS_OPERACIONAL
        else:
            return

        impressoras = self.printer_service.buscar_por_status(status_list)

        dialog = QDialog(self)
        dialog.setWindowTitle(titulo)
        dialog.setMinimumSize(800, 520)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                border: 1px solid #585b70;
                border-radius: 16px;
            }
            QLabel {
                color: #cdd6f4; font-size: 18px; font-weight: 700;
                background: transparent; padding: 16px 20px 0 20px;
            }
            QTableWidget {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #585b70; border-radius: 10px;
                gridline-color: #45475a; font-size: 13px;
            }
            QTableWidget::item { padding: 8px; }
            QHeaderView::section {
                background-color: #1e1e2e; color: #6c7086;
                font-weight: 700; padding: 10px; border: none;
                border-bottom: 1px solid #45475a;
            }
            QPushButton {
                background-color: #45475a; color: #a6adc8;
                border: 1px solid #585b70; border-radius: 8px;
                padding: 10px 30px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover {
                background-color: #585b70; color: #cdd6f4;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(12)

        lbl_titulo = QLabel(f"{titulo}  ·  {len(impressoras)} encontrada(s)")
        layout.addWidget(lbl_titulo)

        tabela = QTableWidget()
        tabela.setColumnCount(5)
        tabela.setHorizontalHeaderLabels(["Patrimônio", "Modelo", "Status", "Local Atual", "Última Revisão"])
        tabela.setRowCount(len(impressoras))

        from app.views.widgets.badge_widget import BadgeWidget
        for i, p in enumerate(impressoras):
            tabela.setItem(i, 0, QTableWidgetItem(p.patrimonio))
            tabela.setItem(i, 1, QTableWidgetItem(p.modelo))

            cor_status = STATUS_CORES.get(p.status, "#6c7086")
            badge = BadgeWidget(p.status, cor_status)
            tabela.setCellWidget(i, 2, badge)

            tabela.setItem(i, 3, QTableWidgetItem(p.local_atual or "-"))

            ultima = self.activity_service.buscar_ultima_manutencao(p.id)
            rev = formatar_data(ultima.event_at) if ultima and ultima.event_at else "Nunca"
            tabela.setItem(i, 4, QTableWidgetItem(rev))

        tabela.horizontalHeader().setStretchLastSection(True)
        tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tabela.verticalHeader().setVisible(False)
        tabela.resizeColumnsToContents()
        tabela.resizeRowsToContents()
        tabela.verticalHeader().setDefaultSectionSize(32)

        def ao_duplo_clique(row, col):
            self.signal_trocar_pagina.emit(1)
            dialog.accept()

        tabela.cellDoubleClicked.connect(ao_duplo_clique)
        layout.addWidget(tabela)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setCursor(Qt.PointingHandCursor)
        btn_fechar.clicked.connect(dialog.accept)
        layout.addWidget(btn_fechar, alignment=Qt.AlignCenter)

        dialog.exec()
