from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class BadgeWidget(QWidget):
    def __init__(self, texto, cor=None, parent=None):
        super().__init__(parent)
        if cor is None:
            cor = "#6366f1"

        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setStyleSheet("background: transparent; border: none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        dot = QLabel()
        dot.setFixedSize(7, 7)
        dot.setStyleSheet(
            f"background-color: {cor}; border-radius: 4px; border: none;"
        )
        layout.addWidget(dot)

        label = QLabel(texto)
        label.setStyleSheet(
            f"color: {cor}; font-size: 11px; font-weight: 600; "
            f"background: transparent; border: none; padding: 0;"
        )
        layout.addWidget(label)
