from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget


def _hex_to_qcolor(hex_cor: str, alpha: int = 60) -> QColor:
    h = hex_cor.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return QColor(r, g, b, alpha)
    return QColor(0, 0, 0, alpha)


def sombra_card(widget: QWidget, blur: int = 20, offset: int = 4) -> QGraphicsDropShadowEffect:
    efeito = QGraphicsDropShadowEffect(widget)
    efeito.setBlurRadius(blur)
    efeito.setOffset(0, offset)
    efeito.setColor(_hex_to_qcolor("#000000", 60))
    widget.setGraphicsEffect(efeito)
    return efeito


def sombra_glow(widget: QWidget, cor: str = "#a78bfa", blur: int = 30) -> QGraphicsDropShadowEffect:
    efeito = QGraphicsDropShadowEffect(widget)
    efeito.setBlurRadius(blur)
    efeito.setOffset(0, 0)
    efeito.setColor(_hex_to_qcolor(cor, 40))
    widget.setGraphicsEffect(efeito)
    return efeito
