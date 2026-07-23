from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QEvent, QObject
from PySide6.QtGui import QColor, QMouseEvent
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QSizePolicy, QTableWidget, QTableWidgetItem

from app.views.styles.theme import ESTILO_TABELA
from app.views.widgets.badge_widget import BadgeWidget


class _InteractiveHeaderView(QHeaderView):
    """Header que começa com Stretch e troca pra Interactive no primeiro arrasto."""

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self._user_resized = False

    def resetar(self) -> None:
        self._user_resized = False
        for i in range(self.count()):
            self.setSectionResizeMode(i, QHeaderView.Stretch)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self._user_resized and event.button() == Qt.LeftButton:
            idx = self.logicalIndexAt(event.pos())
            if idx >= 0:
                self._user_resized = True
                for i in range(self.count()):
                    self.setSectionResizeMode(i, QHeaderView.Interactive)
        super().mousePressEvent(event)


class TabelaPadrao(QTableWidget):
    def __init__(self, colunas: list[str], parent: Optional[QTableWidget] = None) -> None:
        super().__init__(parent)
        self.setColumnCount(len(colunas))
        self.setHorizontalHeaderLabels(colunas)
        self.setStyleSheet(ESTILO_TABELA)
        header = _InteractiveHeaderView()
        header.setDefaultSectionSize(120)
        for i in range(len(colunas)):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        self.setHorizontalHeader(header)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        header = self.horizontalHeader()
        if isinstance(header, _InteractiveHeaderView):
            header.resetar()

    def redimensionar(self) -> None:
        self.verticalHeader().setDefaultSectionSize(44)

    def item_colorido(self, texto: str, cor_hex: str) -> QTableWidgetItem:
        item = QTableWidgetItem(texto)
        item.setForeground(QColor(cor_hex))
        return item

    def item_centralizado(self, texto: str) -> QTableWidgetItem:
        item = QTableWidgetItem(texto)
        item.setTextAlignment(Qt.AlignCenter)
        return item

    def badge_item(self, texto: str, cor: str) -> BadgeWidget:
        badge = BadgeWidget(texto, cor)
        return badge

    def definir_badge(self, row: int, col: int, texto: str, cor: str) -> None:
        badge = BadgeWidget(texto, cor)
        self.setCellWidget(row, col, badge)

    def limpar(self) -> None:
        self.setRowCount(0)


def tornar_interativa(tabela: QTableWidget) -> None:
    """Converte qualquer QTableWidget para ter colunas arrastáveis com reset ao mostrar a tela."""
    header = _InteractiveHeaderView()
    header.setDefaultSectionSize(120)
    n = tabela.columnCount()
    for i in range(n):
        header.setSectionResizeMode(i, QHeaderView.Stretch)
    tabela.setHorizontalHeader(header)
    original_show = tabela.showEvent

    def _show_event(event):
        original_show(event)
        header.resetar()

    tabela.showEvent = _show_event
