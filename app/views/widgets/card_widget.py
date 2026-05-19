from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from app.utils.effects import sombra_card

ESTILOS_CARD = {
    "azul": {
        "card": "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 rgba(99,102,241,0.10),stop:1 rgba(79,70,229,0.05)); border: 1px solid rgba(99,102,241,0.20);",
        "icon_bg": "background: rgba(99,102,241,0.20);",
        "icon_color": "#6366f1",
    },
    "verde": {
        "card": "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 rgba(16,185,129,0.10),stop:1 rgba(5,150,105,0.05)); border: 1px solid rgba(16,185,129,0.20);",
        "icon_bg": "background: rgba(16,185,129,0.20);",
        "icon_color": "#10b981",
    },
    "amarelo": {
        "card": "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 rgba(249,115,22,0.10),stop:1 rgba(217,119,6,0.05)); border: 1px solid rgba(249,115,22,0.20);",
        "icon_bg": "background: rgba(249,115,22,0.20);",
        "icon_color": "#f97316",
    },
    "rosa": {
        "card": "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 rgba(236,72,153,0.10),stop:1 rgba(225,29,72,0.05)); border: 1px solid rgba(236,72,153,0.20);",
        "icon_bg": "background: rgba(236,72,153,0.20);",
        "icon_color": "#ec4899",
    },
    "roxo": {
        "card": "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 rgba(139,92,246,0.10),stop:1 rgba(124,58,237,0.05)); border: 1px solid rgba(139,92,246,0.20);",
        "icon_bg": "background: rgba(139,92,246,0.20);",
        "icon_color": "#8b5cf6",
    },
    "blue": {
        "card": "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 rgba(59,130,246,0.10),stop:1 rgba(37,99,235,0.05)); border: 1px solid rgba(59,130,246,0.20);",
        "icon_bg": "background: rgba(59,130,246,0.20);",
        "icon_color": "#3b82f6",
    },
}


class CardWidget(QFrame):
    def __init__(self, icon, titulo, valor_inicial="0", estilo="azul", callback=None, parent=None):
        super().__init__(parent)
        e = ESTILOS_CARD.get(estilo, ESTILOS_CARD["azul"])
        sombra_card(self)

        self.setStyleSheet(
            f"QFrame#cardFrame {{ border-radius: 12px; padding: 20px; {e['card']} }} "
            f"QFrame#cardFrame:hover {{ border-color: {e['icon_color']} !important; }}"
        )
        self.setObjectName("cardFrame")
        self.setMinimumHeight(130)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(12)

        icon_label = QLabel(icon)
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(
            f"QLabel {{ {e['icon_bg']} border-radius: 12px; "
            f"font-size: 22px; color: {e['icon_color']}; "
            f"border: none; }}"
        )
        icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        header.addWidget(icon_label)
        header.addStretch()
        layout.addLayout(header)

        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet(
            "font-size: 13px; color: #94949f; background: transparent; border: none;"
        )
        layout.addWidget(titulo_label)

        self.valor_label = QLabel(valor_inicial)
        self.valor_label.setStyleSheet(
            f"font-size: 30px; font-weight: 700; color: #e8e8f0; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self.valor_label)

        layout.addStretch()

        if callback:
            self.setCursor(Qt.PointingHandCursor)
            self.mousePressEvent = lambda event: callback()

    def atualizar_valor(self, valor):
        self.valor_label.setText(str(valor))


def _rgba(hex_color, alpha=1.0):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


class CardMiniWidget(QFrame):
    def __init__(self, icon, titulo, valor_inicial="0", cor="#6366f1", parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame#miniCard {{ background-color: rgba(20,20,31,0.5); "
            f"border: 1px solid rgba(42,42,62,0.5); border-radius: 12px; padding: 16px; }}"
        )
        self.setObjectName("miniCard")
        self.setMinimumHeight(90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(
            f"background: {_rgba(cor, 0.15)}; border-radius: 8px; "
            f"font-size: 16px; color: {cor}; border: none;"
        )
        icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(icon_label)

        title_label = QLabel(titulo)
        title_label.setStyleSheet(
            "font-size: 11px; color: #94949f; background: transparent; border: none; font-weight: 500;"
        )
        title_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(title_label)

        self.valor_label = QLabel(valor_inicial)
        self.valor_label.setStyleSheet(
            f"font-size: 24px; font-weight: 700; color: {cor}; "
            f"background: transparent; border: none;"
        )
        self.valor_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self.valor_label)

    def atualizar_valor(self, valor):
        self.valor_label.setText(str(valor))


class CardMiniClicavel(CardMiniWidget):
    def __init__(self, icon, titulo, valor_inicial, cor, ao_clicar=None, parent=None):
        super().__init__(icon, titulo, valor_inicial, cor, parent)
        self.setCursor(Qt.PointingHandCursor)
        if ao_clicar:
            self.mousePressEvent = lambda event: ao_clicar()

    def enterEvent(self, event):
        self.setStyleSheet(
            f"QFrame#miniCard {{ background-color: rgba(30,30,46,0.6); "
            f"border: 1px solid rgba(42,42,62,0.8); border-radius: 12px; padding: 16px; }}"
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(
            f"QFrame#miniCard {{ background-color: rgba(20,20,31,0.5); "
            f"border: 1px solid rgba(42,42,62,0.5); border-radius: 12px; padding: 16px; }}"
        )
        super().leaveEvent(event)
