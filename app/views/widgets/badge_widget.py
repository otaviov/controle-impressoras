from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class BadgeWidget(QWidget):
    def __init__(self, texto, cor="#89b4fa", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)

        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(
            f"background-color: {cor}; border-radius: 4px; border: none;"
        )
        layout.addWidget(dot)

        label = QLabel(texto)
        label.setStyleSheet(f"color: {cor}; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        layout.addWidget(label)

        layout.addStretch()
