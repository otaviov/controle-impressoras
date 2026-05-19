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
    _cor_rgba,
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
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        header = QVBoxLayout()
        header.setSpacing(4)
        titulo = QLabel("Dashboard")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        header.addWidget(titulo)
        subtitulo = QLabel("Visão geral do sistema de controle de impressoras")
        subtitulo.setStyleSheet(ESTILO_SUBTITULO)
        header.addWidget(subtitulo)
        self.lbl_atualizacao = QLabel("")
        self.lbl_atualizacao.setStyleSheet("color: #475569; font-size: 11px; background: transparent;")
        header.addWidget(self.lbl_atualizacao)
        layout.addLayout(header)

        cards = QHBoxLayout()
        cards.setSpacing(16)

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

        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        chart_pizza_card = QWidget()
        chart_pizza_card.setStyleSheet("background: rgba(20,20,31,0.5); border: 1px solid rgba(42,42,62,0.5); border-radius: 12px;")
        cp_layout = QVBoxLayout(chart_pizza_card)
        cp_layout.setContentsMargins(0, 0, 0, 0)
        cp_layout.setSpacing(0)
        cp_header = QLabel("Status das Impressoras")
        cp_header.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #e8e8f0; "
            "padding: 16px 20px; border-bottom: 1px solid rgba(42,42,62,0.5); "
            "background: transparent;"
        )
        cp_layout.addWidget(cp_header)
        self.chart_pizza = PizzaChart("", width=4, height=3)
        self.chart_pizza.setStyleSheet("background: transparent; border: none;")
        cp_layout.addWidget(self.chart_pizza)

        chart_bar_card = QWidget()
        chart_bar_card.setStyleSheet("background: rgba(20,20,31,0.5); border: 1px solid rgba(42,42,62,0.5); border-radius: 12px;")
        cb_layout = QVBoxLayout(chart_bar_card)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        cb_layout.setSpacing(0)
        cb_header = QLabel("Atividades por Mês")
        cb_header.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #e8e8f0; "
            "padding: 16px 20px; border-bottom: 1px solid rgba(42,42,62,0.5); "
            "background: transparent;"
        )
        cb_layout.addWidget(cb_header)
        self.chart_barras = BarChart("", width=4, height=3)
        self.chart_barras.setStyleSheet("background: transparent; border: none;")
        cb_layout.addWidget(self.chart_barras)

        charts_row.addWidget(chart_pizza_card, 1)
        charts_row.addWidget(chart_bar_card, 1)
        layout.addLayout(charts_row)

        linha_card = QWidget()
        linha_card.setStyleSheet("background: rgba(20,20,31,0.5); border: 1px solid rgba(42,42,62,0.5); border-radius: 12px;")
        cl_layout = QVBoxLayout(linha_card)
        cl_layout.setContentsMargins(0, 0, 0, 0)
        cl_layout.setSpacing(0)
        cl_header = QLabel("Alertas (últimos 30 dias)")
        cl_header.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #e8e8f0; "
            "padding: 16px 20px; border-bottom: 1px solid rgba(42,42,62,0.5); "
            "background: transparent;"
        )
        cl_layout.addWidget(cl_header)
        self.chart_linha = LineChart("", width=8.2, height=2.5)
        self.chart_linha.setStyleSheet("background: transparent; border: none;")
        cl_layout.addWidget(self.chart_linha)
        layout.addWidget(linha_card)

        atv_card = QWidget()
        atv_card.setStyleSheet("background: rgba(20,20,31,0.5); border: 1px solid rgba(42,42,62,0.5); border-radius: 12px;")
        atv_layout = QVBoxLayout(atv_card)
        atv_layout.setContentsMargins(0, 0, 0, 0)
        atv_layout.setSpacing(0)
        atv_header = QLabel("Atividades Recentes")
        atv_header.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #e8e8f0; "
            "padding: 16px 20px; border-bottom: 1px solid rgba(42,42,62,0.5); "
            "background: transparent;"
        )
        atv_layout.addWidget(atv_header)

        self.atv_container = QVBoxLayout()
        self.atv_container.setContentsMargins(20, 12, 20, 12)
        self.atv_container.setSpacing(0)
        atv_layout.addLayout(self.atv_container)
        layout.addWidget(atv_card)

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

        self._preencher_atividades()

    def _preencher_atividades(self):
        while self.atv_container.count():
            item = self.atv_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            recentes = self.activity_service.listar(limite=5)
        except Exception:
            recentes = []

        if not recentes:
            lbl = QLabel("Nenhuma atividade recente")
            lbl.setStyleSheet("color: #717182; font-size: 12px; padding: 16px 0; background: transparent;")
            self.atv_container.addWidget(lbl)
            return

        for i, atv in enumerate(recentes):
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 10, 0, 10)
            row_layout.setSpacing(12)

            if i < len(recentes) - 1:
                row.setStyleSheet(f"background: transparent; border-bottom: 1px solid {_cor_rgba('#2a2a3e', 0.30)};")

            cor_dot = "#6366f1"
            if atv.kind == "MANUTENCAO":
                cor_dot = "#f97316"
            elif atv.kind == "MOVIMENTACAO":
                cor_dot = "#3b82f6"

            dot = QLabel()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(
                f"background-color: {cor_dot}; border-radius: 4px; border: none; "
                f"margin-top: 4px;"
            )
            row_layout.addWidget(dot, alignment=Qt.AlignTop)

            texto_layout = QVBoxLayout()
            texto_layout.setSpacing(2)

            printer_info = ""
            if atv.printer_id:
                try:
                    p = self.printer_service.buscar_por_id(atv.printer_id)
                    if p:
                        printer_info = f" - {p.patrimonio}"
                except Exception:
                    pass

            action = QLabel(f"{atv.notes or atv.kind or 'Atividade'}{printer_info}")
            action.setStyleSheet(
                "font-size: 13px; font-weight: 500; color: #e8e8f0; "
                "background: transparent; border: none;"
            )
            action.setWordWrap(True)
            texto_layout.addWidget(action)

            data_str = formatar_data(atv.event_at) if atv.event_at else ""
            if data_str:
                data_lbl = QLabel(data_str)
                data_lbl.setStyleSheet(
                    "font-size: 11px; color: #717182; background: transparent; border: none;"
                )
                texto_layout.addWidget(data_lbl)

            row_layout.addLayout(texto_layout)
            row_layout.addStretch()

            self.atv_container.addWidget(row)

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
                background-color: rgba(20,20,31,0.5); color: #e8e8f0;
                border: 1px solid rgba(42,42,62,0.5); border-radius: 10px;
                gridline-color: transparent; font-size: 13px;
            }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid rgba(42,42,62,0.3); }
            QTableWidget::item:hover { background-color: rgba(30,30,46,0.5); }
            QHeaderView::section {
                background-color: transparent; color: #717182;
                font-weight: 700; padding: 10px; border: none;
                border-bottom: 1px solid rgba(42,42,62,0.5);
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
