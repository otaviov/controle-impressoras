from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QMessageBox)
from PySide6.QtCore import Qt
from datetime import datetime as dt
import os
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from app.views.styles.theme import COR, ESTILO_TITULO_PAGINA, ESTILO_BOTAO_SUCESSO
from app.views.relatorio_dialog import RelatorioDialog
from app.services.relatorio_service import RelatorioService
from models import Printer, Activity


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
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        titulo = QLabel("\U0001f4c8 Relat\u00f3rios e Gr\u00e1ficos")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        header.addWidget(titulo)
        header.addStretch()

        self.btn_relatorio = QPushButton("\U0001f4ca Gerar Relat\u00f3rio Personalizado")
        self.btn_relatorio.setStyleSheet("""
            QPushButton {
                background-color: #cba6f7; color: #1a1a2e;
                border: none; border-radius: 8px;
                padding: 15px; font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #bb96e7; }
        """)
        self.btn_relatorio.clicked.connect(self._abrir_relatorio)
        header.addWidget(self.btn_relatorio)

        layout.addLayout(header)

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

        CANVAS_STYLE = """
            QWidget {
                background-color: #0f3460;
                border-radius: 10px;
                border: 1px solid #533483;
            }
        """

        for canvas in [self.canvas_status, self.canvas_modelos, self.canvas_atividades, self.canvas_pecas]:
            canvas.setStyleSheet(CANVAS_STYLE)

        self.grid.addWidget(self.canvas_status, 0, 0)
        self.grid.addWidget(self.canvas_modelos, 0, 1)
        self.grid.addWidget(self.canvas_atividades, 1, 0)
        self.grid.addWidget(self.canvas_pecas, 1, 1)

    def _criar_grafico_pizza(self):
        fig = Figure(facecolor='#1a1a2e')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1a1a2e')

        dados = self._printer_service.agrupar_por_status()
        if dados:
            labels = [d[0] for d in dados]
            valores = [d[1] for d in dados]
            cores = ['#e94560', '#89b4fa', '#a6e3a1', '#f9e2af', '#cba6f7', '#f38ba8', '#6b7280']
            ax.pie(valores, labels=labels, autopct='%1.1f%%', startangle=90,
                   colors=cores[:len(valores)], textprops={'color': 'white', 'fontsize': 9})
        else:
            ax.text(0.5, 0.5, 'Sem dados', ha='center', va='center', color='white', fontsize=12)

        ax.set_title('Impressoras por Status', color='#e94560', fontsize=12, fontweight='bold')
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('#533483')
        ax.spines['left'].set_color('#533483')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        canvas = FigureCanvas(fig)
        return canvas

    def _criar_grafico_barras(self):
        fig = Figure(facecolor='#1a1a2e')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1a1a2e')

        dados = self._printer_service.top_modelos(5)
        if dados:
            labels = [d[0] if d[0] else 'N/A' for d in dados]
            valores = [d[1] for d in dados]
            ax.barh(labels[::-1], valores[::-1], color='#89b4fa', edgecolor='#533483')
        else:
            ax.text(0.5, 0.5, 'Sem dados', ha='center', va='center', color='white', fontsize=12)
            ax.set_xlim(0, 1)

        ax.set_title('Top 5 Modelos', color='#e94560', fontsize=12, fontweight='bold')
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('#533483')
        ax.spines['left'].set_color('#533483')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        canvas = FigureCanvas(fig)
        return canvas

    def _criar_grafico_linhas(self):
        fig = Figure(facecolor='#1a1a2e')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1a1a2e')

        dados = self._activity_service.contar_ultimos_6_meses()
        if dados and dados.get('labels'):
            meses = dados['labels']
            manut = dados['manut']
            mov = dados['mov']
            ax.plot(meses, manut, marker='o', color='#e94560', label='Manuten\u00e7\u00e3o', linewidth=2)
            ax.plot(meses, mov, marker='s', color='#89b4fa', label='Movimenta\u00e7\u00e3o', linewidth=2)
            ax.legend(frameon=False, labelcolor='white')
        else:
            ax.text(0.5, 0.5, 'Sem dados', ha='center', va='center', color='white', fontsize=12)
            ax.set_xlim(0, 1)

        ax.set_title('Atividades por M\u00eas (\u00faltimos 6 meses)', color='#e94560', fontsize=12, fontweight='bold')
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('#533483')
        ax.spines['left'].set_color('#533483')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        canvas = FigureCanvas(fig)
        return canvas

    def _criar_grafico_barras_horiz(self):
        fig = Figure(facecolor='#1a1a2e')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1a1a2e')

        dados = self._activity_service.top_pecas_trocadas(8)
        if dados:
            labels = [d[0] for d in dados]
            valores = [d[1] for d in dados]
            ax.barh(labels[::-1], valores[::-1], color='#a6e3a1', edgecolor='#533483')
        else:
            ax.text(0.5, 0.5, 'Sem dados', ha='center', va='center', color='white', fontsize=12)
            ax.set_xlim(0, 1)

        ax.set_title('Pe\u00e7as Mais Trocadas', color='#e94560', fontsize=12, fontweight='bold')
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('#533483')
        ax.spines['left'].set_color('#533483')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        canvas = FigureCanvas(fig)
        return canvas

    def _abrir_relatorio(self):
        dialogo = RelatorioDialog(self._session, self)
        dialogo.exec()
