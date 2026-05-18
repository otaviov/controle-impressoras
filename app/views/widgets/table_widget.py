from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from app.views.styles.theme import ESTILO_TABELA
from app.views.widgets.badge_widget import BadgeWidget


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
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def redimensionar(self):
        self.resizeColumnsToContents()
        self.verticalHeader().setDefaultSectionSize(28)
        self.resizeRowsToContents()
        self.horizontalHeader().setStretchLastSection(True)

    def item_colorido(self, texto, cor_hex):
        item = QTableWidgetItem(texto)
        item.setForeground(QColor(cor_hex))
        return item

    def item_centralizado(self, texto):
        item = QTableWidgetItem(texto)
        item.setTextAlignment(Qt.AlignCenter)
        return item

    def badge_item(self, texto, cor):
        item = QTableWidgetItem()
        item.setData(Qt.DisplayRole, texto)
        badge = BadgeWidget(texto, cor)
        self.setItem(self.rowCount() - 1, 0, item)
        return badge

    def definir_badge(self, row, col, texto, cor):
        badge = BadgeWidget(texto, cor)
        self.setCellWidget(row, col, badge)

    def limpar(self):
        self.setRowCount(0)
