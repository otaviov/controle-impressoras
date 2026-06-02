from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SpinnerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self._angulo = 0

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(3, 3, -3, -3)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2e2e4a"))
        p.drawPie(rect, 0, 360 * 16)
        p.setBrush(QColor("#a78bfa"))
        p.drawPie(rect, self._angulo * 16, 90 * 16)
        p.end()


class LoadingOverlay(QWidget):
    def __init__(self, parent=None, text="Carregando..."):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background-color: rgba(10, 10, 18, 180);")
        self.hide()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.spinner = SpinnerWidget()
        layout.addWidget(self.spinner, alignment=Qt.AlignCenter)

        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(
            "color: #a78bfa; font-size: 15px; font-weight: 600;"
            " background: transparent; padding: 8px;"
        )
        layout.addWidget(self.label)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotacionar)

    def _rotacionar(self):
        self.spinner._angulo = (self.spinner._angulo + 30) % 360
        self.spinner.update()

    def mostrar(self, text=None):
        if text:
            self.label.setText(text)
        self.setFixedSize(self.parent().size())
        self.raise_()
        self._timer.start(50)
        self.show()

    def ocultar(self):
        self._timer.stop()
        self.hide()

    def resizeEvent(self, event):
        if self.parent():
            self.setFixedSize(self.parent().size())
        super().resizeEvent(event)
