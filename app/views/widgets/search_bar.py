from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit


class SearchBar(QFrame):
    def __init__(self, placeholder="Buscar...", glass=False, parent=None):
        super().__init__(parent)
        self._glass = glass
        self._padrao = "rgba(20,20,31,0.5)" if glass else "#1e1e2e"
        self._borda = "rgba(42,42,62,0.5)" if glass else "#2a2a3e"

        self.setStyleSheet(
            f"QFrame#searchFrame {{ background: {self._padrao}; "
            f"border: 1px solid {self._borda}; border-radius: 10px; }}"
        )
        self.setObjectName("searchFrame")
        min_h = 48 if glass else 40
        self.setMinimumHeight(min_h)
        self.setMaximumHeight(min_h)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(8)

        icon = QLabel("\U0001F50D")
        icon.setStyleSheet("font-size: 14px; background: transparent; color: #94949f;")
        layout.addWidget(icon)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setStyleSheet(
            "QLineEdit { background: transparent; color: #e8e8f0; "
            "border: none; font-size: 11pt; }"
            "QLineEdit::placeholder { color: #717182; }"
        )
        layout.addWidget(self.input)

    def textChanged(self):
        return self.input.textChanged

    def texto(self):
        return self.input.text()

    def limpar(self):
        self.input.clear()
