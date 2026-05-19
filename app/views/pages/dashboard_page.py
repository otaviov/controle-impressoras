from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.utils.helpers import formatar_data
from app.views.styles.theme import (
    ESTILO_SUBTITULO,
    ESTILO_TITULO_PAGINA,
    STATUS_CORES,
    STATUS_MANUTENCAO,
    STATUS_OPERACIONAL,
)
from app.views.widgets.card_widget import CardWidget
from app.views.widgets.chart_widget import BarChart, LineChart, PizzaChart


class DashboardPage(QWidget):
    signal_trocar_pagina = Signal(int)

    def __init__(self, session, printer_service, activity_service, dashboard_service, parent=None):
        super().__init__(parent)
        self.session = session
        self.printer_service = printer_service
        self.activity_service = activity_service
        self.dashboard_service = dashboard_service

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setSpacing(16)
        titulo = QLabel("📊 Dashboard")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        header.addWidget(titulo)
        header.addStretch()
        self.lbl_atualizacao = QLabel("")
        self.lbl_atualizacao.setStyleSheet("color: #475569; font-size: 11px; background: transparent;")
        header.addWidget(self.lbl_atualizacao)
        layout.addLayout(header)

        subtitulo = QLabel("Visão geral do sistema de controle de impressoras")
        subtitulo.setStyleSheet(ESTILO_SUBTITULO)
        layout.addWidget(subtitulo)

        layout.addSpacing(24)

        cards = QHBoxLayout()
        cards.setSpacing(14)

        self.card_total = CardWidget("🖨️", "Total Impressoras", "0", estilo="azul",
            callback=lambda: self.signal_trocar_pagina.emit(1))
        self.card_manut = CardWidget("⚠️", "Em Manutenção", "0", estilo="amarelo",
            callback=lambda: self.ao_clicar_status("manutencao"))
        self.card_op = CardWidget("✅", "Operacionais", "0", estilo="verde",
            callback=lambda: self.ao_clicar_status("operacional"))
        self.card_os = CardWidget("📋", "Atividades", "0", estilo="roxo",
            callback=lambda: self.signal_trocar_pagina.emit(2))

        cards.addWidget(self.card_total)
        cards.addWidget(self.card_manut)
        cards.addWidget(self.card_op)
        cards.addWidget(self.card_os)
        layout.addLayout(cards)

        layout.addSpacing(24)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(14)

        self.chart_pizza = PizzaChart("Status das Impressoras", width=4, height=3)
        self.chart_barras = BarChart("Atividades por Mês", width=4, height=3)

        charts_row.addWidget(self.chart_pizza, 1)
        charts_row.addWidget(self.chart_barras, 1)
        layout.addLayout(charts_row)

        layout.addSpacing(14)

        self.chart_linha = LineChart("Alertas (últimos 30 dias)", width=8.2, height=2.5)
        layout.addWidget(self.chart_linha)

        layout.addStretch(1)

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def recarregar(self):
        dados = self.dashboard_service.resumo()
        self.card_total.atualizar_valor(dados.get("total_impressoras", 0))
        self.card_manut.atualizar_valor(dados.get("em_manutencao", 0))
        self.card_op.atualizar_valor(dados.get("operacionais", 0))
        self.card_os.atualizar_valor(dados.get("total_atividades", 0))
        self.lbl_atualizacao.setText(f"Atualizado: {datetime.now():%H:%M:%S}")

        try:
            labels_pizza, valores_pizza = self.dashboard_service.dados_grafico_pizza()
            self.chart_pizza.atualizar(labels_pizza, valores_pizza)

            labels_barras, valores_barras = self.dashboard_service.dados_grafico_atividades()
            self.chart_barras.atualizar(labels_barras, valores_barras)

            labels_linha, valores_linha = self.dashboard_service.dados_grafico_alertas()
            self.chart_linha.atualizar(labels_linha, valores_linha)
        except Exception:
            import traceback; traceback.print_exc()

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
                background-color: #14141f;
                border: 1px solid #2a2a3e;
                border-radius: 16px;
            }
            QLabel {
                color: #e8e8f0; font-size: 18px; font-weight: 700;
                background: transparent; padding: 16px 20px 0 20px;
            }
            QTableWidget {
                background-color: #14141f; color: #e8e8f0;
                border: 1px solid #2a2a3e; border-radius: 10px;
                gridline-color: #1e1e2e; font-size: 13px;
            }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #1e1e2e; }
            QTableWidget::item:hover { background-color: #1a1a28; }
            QHeaderView::section {
                background-color: #14141f; color: #717182;
                font-weight: 700; padding: 10px; border: none;
                border-bottom: 1px solid #2a2a3e;
            }
            QPushButton {
                background-color: transparent; color: #717182;
                border: 1px solid #2a2a3e; border-radius: 8px;
                padding: 10px 30px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1e1e2e; color: #e8e8f0;
                border-color: #6366f1;
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

            cor_status = STATUS_CORES.get(p.status, "#94949f")
            badge = BadgeWidget(p.status, cor_status)
            tabela.setCellWidget(i, 2, badge)

            tabela.setItem(i, 3, QTableWidgetItem(p.local_atual or "-"))

            ultima = self.activity_service.buscar_ultima_manutencao(p.id)
            rev = formatar_data(ultima.event_at) if ultima and ultima.event_at else "Nunca"
            tabela.setItem(i, 4, QTableWidgetItem(rev))

        tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tabela.verticalHeader().setVisible(False)
        tabela.verticalHeader().setDefaultSectionSize(44)
        for i in range(tabela.columnCount()):
            tabela.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

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
