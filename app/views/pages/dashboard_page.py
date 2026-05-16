from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog, QPushButton)
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
        layout.setContentsMargins(25, 25, 25, 25)

        titulo = QLabel("📊 Dashboard")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        layout.addWidget(titulo)

        subtitulo = QLabel("Visão geral do sistema")
        subtitulo.setStyleSheet(ESTILO_SUBTITULO)
        layout.addWidget(subtitulo)

        layout.addSpacing(15)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)

        self.card_total = CardWidget("🖨️", "Total Impressoras", "0", COR["azul"], callback=lambda: self.signal_trocar_pagina.emit(1))
        self.card_manut = CardWidget("⚠️", "Em Manutenção", "0", COR["aviso"], callback=lambda: self.ao_clicar_status("manutencao"))
        self.card_op = CardWidget("✅", "Operacionais", "0", COR["sucesso"], callback=lambda: self.ao_clicar_status("operacional"))
        self.card_os = CardWidget("📋", "Atividades", "0", COR["roxo_claro"], callback=lambda: self.signal_trocar_pagina.emit(2))

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
        dialog.setMinimumSize(800, 500)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #e0e0e0; font-size: 18px; font-weight: bold; background: transparent; }
            QTableWidget { background-color: #0f3460; color: #e0e0e0; border: 1px solid #533483; border-radius: 10px; gridline-color: #1a1a3e; font-size: 13px; }
            QTableWidget::item { padding: 8px; }
            QHeaderView::section { background-color: #16213e; color: #89b4fa; font-weight: bold; padding: 10px; border: none; border-bottom: 2px solid #e94560; }
            QPushButton { background-color: #e94560; color: white; border: none; border-radius: 8px; padding: 10px 30px; font-size: 14px; font-weight: bold; }
        """)

        layout = QVBoxLayout(dialog)

        lbl_titulo = QLabel(f"{titulo} ({len(impressoras)})")
        layout.addWidget(lbl_titulo)
        layout.addSpacing(10)

        tabela = QTableWidget()
        tabela.setColumnCount(5)
        tabela.setHorizontalHeaderLabels(["Patrimônio", "Modelo", "Status", "Local Atual", "Última Revisão"])
        tabela.setRowCount(len(impressoras))

        for i, p in enumerate(impressoras):
            tabela.setItem(i, 0, QTableWidgetItem(p.patrimonio))
            tabela.setItem(i, 1, QTableWidgetItem(p.modelo))

            status_item = QTableWidgetItem(p.status)
            cor_status = STATUS_CORES.get(p.status, "#a0a0b0")
            status_item.setForeground(QColor(cor_status))
            tabela.setItem(i, 2, status_item)

            tabela.setItem(i, 3, QTableWidgetItem(p.local_atual or "-"))

            ultima = self.activity_service.buscar_ultima_manutencao(p.id)
            rev = formatar_data(ultima.event_at) if ultima and ultima.event_at else "Nunca"
            tabela.setItem(i, 4, QTableWidgetItem(rev))

        tabela.horizontalHeader().setStretchLastSection(True)
        tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tabela.verticalHeader().setVisible(False)
        tabela.resizeColumnsToContents()

        def ao_duplo_clique(row, col):
            patrimonio = tabela.item(row, 0).text()
            self.signal_trocar_pagina.emit(1)
            dialog.accept()

        tabela.cellDoubleClicked.connect(ao_duplo_clique)
        layout.addWidget(tabela)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setCursor(Qt.PointingHandCursor)
        btn_fechar.clicked.connect(dialog.accept)
        layout.addWidget(btn_fechar, alignment=Qt.AlignCenter)

        dialog.exec()
