from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit
from PySide6.QtCore import Qt


class SearchBar(QFrame):
    def __init__(self, placeholder="Buscar...", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #0d0d1a;
                border: 1px solid #1e1e30;
                border-radius: 10px;
            }
            QFrame:focus-within { border-color: #7c3aed; }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        icon = QLabel("🔍")
        icon.setStyleSheet("font-size: 13px; background: transparent; color: #3a3a5a;")
        layout.addWidget(icon)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setMinimumHeight(38)
        self.input.setStyleSheet("""
            QLineEdit {
                background: transparent; color: #c4c4e0;
                border: none; font-size: 11pt;
            }
            QLineEdit::placeholder { color: #2a2a42; }
        """)
        layout.addWidget(self.input)

    def textChanged(self):
        return self.input.textChanged

    def texto(self):
        return self.input.text()

    def limpar(self):
        self.input.clear()
