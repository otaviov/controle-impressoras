from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton)
from PySide6.QtCore import Qt
from datetime import datetime as dt
import os
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from app.views.styles.theme import ESTILO_TITULO_PAGINA, ESTILO_BOTAO_SUCESSO
from app.views.relatorio_dialog import RelatorioDialog


BG = '#1e1e2e'
CARD = '#313244'
BORDA = '#585b70'
TEXTO = '#cdd6f4'
AZUL = '#89b4fa'
VERDE = '#a6e3a1'
AMARELO = '#f9e2af'
ROXO = '#cba6f7'
CINZA = '#6c7086'


class ReportsPage(QWidget):
    def __init__(self, session, printer_service, activity_service, parent=None):
        super().__init__(parent)
        self._session = session
        self._printer_service = printer_service
        self._activity_service = activity_service

        self.canvas_status = None
        self.canvas_modelos = None
        self.canvas_atividades = None
        self.canvas_pecas = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        header = QHBoxLayout()
        titulo = QLabel("📈 Relatórios e Gráficos")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        header.addWidget(titulo)
        header.addStretch()
        layout.addLayout(header)

        self.btn_relatorio = QPushButton("📊  Gerar Relatório Personalizado")
        self.btn_relatorio.setMinimumHeight(56)
        self.btn_relatorio.setCursor(Qt.PointingHandCursor)
        self.btn_relatorio.setStyleSheet(f"""
            QPushButton {{
                background-color: {ROXO}; color: #1e1e2e;
                border: none; border-radius: 12px;
                padding: 16px 24px; font-size: 15px; font-weight: 700;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: #b4befe;
            }}
        """)
        self.btn_relatorio.clicked.connect(self._abrir_relatorio)
        layout.addWidget(self.btn_relatorio)

        self.grid = QGridLayout()
        self.grid.setSpacing(16)
        layout.addLayout(self.grid)

    def recarregar(self):
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self.canvas_status = self._criar_grafico_pizza()
        self.canvas_modelos = self._criar_grafico_barras()
        self.canvas_atividades = self._criar_grafico_linhas()
        self.canvas_pecas = self._criar_grafico_barras_horiz()

        CANVAS_STYLE = f"""
            QWidget {{
                background-color: {CARD};
                border-radius: 12px;
                border: 1px solid {BORDA};
            }}
        """

        for canvas in [self.canvas_status, self.canvas_modelos, self.canvas_atividades, self.canvas_pecas]:
            canvas.setStyleSheet(CANVAS_STYLE)

        self.grid.addWidget(self.canvas_status, 0, 0)
        self.grid.addWidget(self.canvas_modelos, 0, 1)
        self.grid.addWidget(self.canvas_atividades, 1, 0)
        self.grid.addWidget(self.canvas_pecas, 1, 1)

    def _estilo_ax(self, ax, titulo, cor_titulo=AMARELO):
        ax.set_title(titulo, color=cor_titulo, fontsize=12, fontweight='bold')
        ax.tick_params(colors=CINZA)
        ax.spines['bottom'].set_color(BORDA)
        ax.spines['left'].set_color(BORDA)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.xaxis.label.set_color(CINZA)
        ax.yaxis.label.set_color(CINZA)

    def _criar_grafico_pizza(self):
        fig = Figure(facecolor=BG)
        ax = fig.add_subplot(111)
        ax.set_facecolor(BG)

        dados = self._printer_service.agrupar_por_status()
        if dados:
            labels = [d[0] for d in dados]
            valores = [d[1] for d in dados]
            cores = [AMARELO, AZUL, VERDE, ROXO, '#f0883e', '#f38ba8', CINZA]
            ax.pie(valores, labels=labels, autopct='%1.1f%%', startangle=90,
                   colors=cores[:len(valores)], textprops={'color': TEXTO, 'fontsize': 9})
        else:
            ax.text(0.5, 0.5, 'Sem dados', ha='center', va='center', color=CINZA, fontsize=12)

        self._estilo_ax(ax, 'Impressoras por Status')
        canvas = FigureCanvas(fig)
        return canvas

    def _criar_grafico_barras(self):
        fig = Figure(facecolor=BG)
        ax = fig.add_subplot(111)
        ax.set_facecolor(BG)

        dados = self._printer_service.top_modelos(5)
        if dados:
            labels = [d[0] if d[0] else 'N/A' for d in dados]
            valores = [d[1] for d in dados]
            ax.barh(labels[::-1], valores[::-1], color=AZUL, edgecolor=BORDA)
        else:
            ax.text(0.5, 0.5, 'Sem dados', ha='center', va='center', color=CINZA, fontsize=12)
            ax.set_xlim(0, 1)

        self._estilo_ax(ax, 'Top 5 Modelos')
        canvas = FigureCanvas(fig)
        return canvas

    def _criar_grafico_linhas(self):
        fig = Figure(facecolor=BG)
        ax = fig.add_subplot(111)
        ax.set_facecolor(BG)

        dados = self._activity_service.contar_ultimos_6_meses()
        if dados and dados.get('labels'):
            meses = dados['labels']
            manut = dados['manut']
            mov = dados['mov']
            ax.plot(meses, manut, marker='o', color=AMARELO, label='Manutenção', linewidth=2)
            ax.plot(meses, mov, marker='s', color=AZUL, label='Movimentação', linewidth=2)
            ax.legend(frameon=False, labelcolor=TEXTO)
        else:
            ax.text(0.5, 0.5, 'Sem dados', ha='center', va='center', color=CINZA, fontsize=12)
            ax.set_xlim(0, 1)

        self._estilo_ax(ax, 'Atividades por Mês (últimos 6 meses)')
        canvas = FigureCanvas(fig)
        return canvas

    def _criar_grafico_barras_horiz(self):
        fig = Figure(facecolor=BG)
        ax = fig.add_subplot(111)
        ax.set_facecolor(BG)

        dados = self._activity_service.top_pecas_trocadas(8)
        if dados:
            labels = [d[0] for d in dados]
            valores = [d[1] for d in dados]
            ax.barh(labels[::-1], valores[::-1], color=VERDE, edgecolor=BORDA)
        else:
            ax.text(0.5, 0.5, 'Sem dados', ha='center', va='center', color=CINZA, fontsize=12)
            ax.set_xlim(0, 1)

        self._estilo_ax(ax, 'Peças Mais Trocadas')
        canvas = FigureCanvas(fig)
        return canvas

    def _abrir_relatorio(self):
        dialogo = RelatorioDialog(self._session, self)
        dialogo.exec()
