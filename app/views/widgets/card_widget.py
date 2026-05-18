from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt


GRADIENTES_BORDA = {
    "azul": "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #3b82f6,stop:1 #7c3aed);",
    "verde": "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #10b981,stop:1 #3b82f6);",
    "amarelo": "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #f59e0b,stop:1 #ef4444);",
    "roxo": "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #8b5cf6,stop:1 #e94560);",
}


class CardWidget(QFrame):
    def __init__(self, icon, titulo, valor_inicial="0", cor="#cba6f7", gradiente="roxo", callback=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background-color: #0d0d1a; border-radius: 12px; "
            f"border: 1px solid #1e1e30; padding: 16px; padding-top: 20px; }} "
            f"QFrame:hover {{ border-color: {cor}; }}"
        )
        self.setMinimumHeight(130)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        borda = QFrame()
        borda.setFixedHeight(3)
        estilo_borda = GRADIENTES_BORDA.get(gradiente, GRADIENTES_BORDA["roxo"])
        borda.setStyleSheet(
            f"QFrame {{ border: none; border-radius: 2px; {estilo_borda} position: absolute; top: 0; left: 0; right: 0; }}"
        )
        borda.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(borda)

        conteudo = QVBoxLayout()
        conteudo.setSpacing(6)
        conteudo.setContentsMargins(4, 10, 4, 2)

        if callback:
            self.setCursor(Qt.PointingHandCursor)
            self.mousePressEvent = lambda event: callback()

        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(
            f"font-size: 18px; background: transparent; "
            f"min-width: 34px; min-height: 34px; max-width: 34px; max-height: 34px; "
            f"border-radius: 8px; background-color: {cor}15; qproperty-alignment: AlignCenter;"
        )
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        header.addWidget(icon_label)
        header.addStretch()
        conteudo.addLayout(header)

        self.valor_label = QLabel(valor_inicial)
        self.valor_label.setStyleSheet(
            f"color: {cor}; font-size: 28px; font-weight: 700; background: transparent;"
        )
        self.valor_label.setObjectName("cardValue")
        self.valor_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        conteudo.addWidget(self.valor_label)

        title_label = QLabel(titulo)
        title_label.setStyleSheet("color: #4a4a6a; font-size: 11px; background: transparent; font-weight: 500; letter-spacing: 0.2px;")
        title_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        conteudo.addWidget(title_label)

        layout.addLayout(conteudo)

    def atualizar_valor(self, valor):
        self.valor_label.setText(str(valor))


class CardMiniWidget(QFrame):
    def __init__(self, icon, titulo, valor_inicial="0", cor="#cba6f7", parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background-color: #313244; border-radius: 12px; "
            f"border: 1px solid #585b70; padding: 14px; }} "
            f"QFrame:hover {{ border-color: {cor}; background-color: #45475a; }}"
        )
        self.setMinimumHeight(90)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px; background: transparent;")
        icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        header.addWidget(icon_label)
        header.addStretch()

        self.valor_label = QLabel(valor_inicial)
        self.valor_label.setStyleSheet(
            f"color: {cor}; font-size: 24px; font-weight: 700; background: transparent;"
        )
        self.valor_label.setObjectName("miniValue")
        self.valor_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        header.addWidget(self.valor_label)
        layout.addLayout(header)

        title_label = QLabel(titulo)
        title_label.setStyleSheet("color: #6c7086; font-size: 10px; background: transparent; font-weight: 500;")
        title_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(title_label)

    def atualizar_valor(self, valor):
        self.valor_label.setText(str(valor))


class CardMiniClicavel(CardMiniWidget):
    def __init__(self, icon, titulo, valor_inicial, cor, ao_clicar=None, parent=None):
        super().__init__(icon, titulo, valor_inicial, cor, parent)
        self.setCursor(Qt.PointingHandCursor)
        if ao_clicar:
            self.mousePressEvent = lambda event: ao_clicar()
