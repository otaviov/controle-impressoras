from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt


class CardWidget(QFrame):
    def __init__(self, icon, titulo, valor_inicial="0", cor="#89b4fa", callback=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background-color: #0f3460; border-radius: 12px; "
            f"border: 1px solid #533483; padding: 18px; }} "
            f"QFrame:hover {{ border-color: {cor}; }}"
        )
        self.setMinimumHeight(130)

        if callback:
            self.setCursor(Qt.PointingHandCursor)
            self.mousePressEvent = lambda event: callback()

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 28px; background: transparent;")
        layout.addWidget(icon_label)

        self.valor_label = QLabel(valor_inicial)
        self.valor_label.setStyleSheet(
            f"color: {cor}; font-size: 30px; font-weight: bold; background: transparent;"
        )
        self.valor_label.setObjectName("cardValue")
        layout.addWidget(self.valor_label)

        title_label = QLabel(titulo)
        title_label.setStyleSheet("color: #a0a0b0; font-size: 12px; background: transparent;")
        layout.addWidget(title_label)

    def atualizar_valor(self, valor):
        self.valor_label.setText(str(valor))


class CardMiniWidget(QFrame):
    def __init__(self, icon, titulo, valor_inicial="0", cor="#89b4fa", parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background-color: #0f3460; border-radius: 10px; "
            f"border: 1px solid #533483; padding: 12px; }} "
            f"QFrame:hover {{ border-color: {cor}; }}"
        )
        self.setMinimumHeight(80)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px; background: transparent;")
        header.addWidget(icon_label)
        header.addStretch()

        self.valor_label = QLabel(valor_inicial)
        self.valor_label.setStyleSheet(
            f"color: {cor}; font-size: 22px; font-weight: bold; background: transparent;"
        )
        self.valor_label.setObjectName("miniValue")
        header.addWidget(self.valor_label)
        layout.addLayout(header)

        title_label = QLabel(titulo)
        title_label.setStyleSheet("color: #a0a0b0; font-size: 10px; background: transparent;")
        layout.addWidget(title_label)

    def atualizar_valor(self, valor):
        self.valor_label.setText(str(valor))


class CardMiniClicavel(CardMiniWidget):
    def __init__(self, icon, titulo, valor_inicial, cor, ao_clicar=None, parent=None):
        super().__init__(icon, titulo, valor_inicial, cor, parent)
        self.setCursor(Qt.PointingHandCursor)
        if ao_clicar:
            self.mousePressEvent = lambda event: ao_clicar()
