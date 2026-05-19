from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


def _rgba(hex_color, alpha=1.0):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


class BadgeWidget(QWidget):
    def __init__(self, texto, cor=None, parent=None):
        super().__init__(parent)
        if cor is None:
            cor = "#6366f1"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 10, 4)
        layout.setSpacing(6)

        dot = QLabel()
        dot.setFixedSize(7, 7)
        dot.setStyleSheet(
            f"background-color: {cor}; border-radius: 4px; border: none;"
        )
        layout.addWidget(dot)

        label = QLabel(texto)
        label.setStyleSheet(
            f"color: {cor}; font-size: 11px; font-weight: 600; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(label)

        total_w = 8 + 7 + 6 + len(texto) * 7 + 10
        self.setStyleSheet(
            f"background-color: {_rgba(cor, 0.12)}; border: 1px solid {_rgba(cor, 0.25)}; "
            f"border-radius: 6px; min-width: {total_w}px;"
        )
