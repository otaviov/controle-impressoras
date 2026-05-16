from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from app.views.styles.theme import ESTILO_TABELA


class TabelaPadrao(QTableWidget):
    def __init__(self, colunas, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(colunas))
        self.setHorizontalHeaderLabels(colunas)
        self.setStyleSheet(ESTILO_TABELA)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)

    def redimensionar(self):
        self.resizeColumnsToContents()

    def item_colorido(self, texto, cor_hex):
        item = QTableWidgetItem(texto)
        item.setForeground(QColor(cor_hex))
        return item

    def item_centralizado(self, texto):
        item = QTableWidgetItem(texto)
        item.setTextAlignment(Qt.AlignCenter)
        return item

    def limpar(self):
        self.setRowCount(0)
