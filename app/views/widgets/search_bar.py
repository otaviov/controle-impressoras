from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit
from PySide6.QtCore import Qt


class SearchBar(QFrame):
    def __init__(self, placeholder="Buscar...", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #313244;
                border: 1px solid #585b70;
                border-radius: 10px;
            }
            QFrame:focus-within { border-color: #cba6f7; }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(8)

        icon = QLabel("🔍")
        icon.setStyleSheet("font-size: 14px; background: transparent; color: #6c7086;")
        layout.addWidget(icon)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setMinimumHeight(40)
        self.input.setStyleSheet("""
            QLineEdit {
                background: transparent; color: #cdd6f4;
                border: none; font-size: 11pt;
            }
            QLineEdit::placeholder { color: #585b70; }
        """)
        layout.addWidget(self.input)

    def textChanged(self):
        return self.input.textChanged

    def texto(self):
        return self.input.text()

    def limpar(self):
        self.input.clear()
