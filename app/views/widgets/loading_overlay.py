from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class LoadingOverlay(QWidget):
    def __init__(self, parent=None, text="Carregando..."):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background-color: rgba(10, 10, 18, 180);")
        self.hide()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.spinner = QLabel()
        self.spinner.setAlignment(Qt.AlignCenter)
        self.spinner.setFixedSize(40, 40)
        self.spinner.setStyleSheet(
            "background: transparent; font-size: 24px;"
            " border: 3px solid #2e2e4a;"
            " border-top: 3px solid #a78bfa;"
            " border-radius: 20px;"
        )
        layout.addWidget(self.spinner)

        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(
            "color: #a78bfa; font-size: 15px; font-weight: 600;"
            " background: transparent; padding: 8px;"
        )
        layout.addWidget(self.label)

        self._angulo = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotacionar)

    def _rotacionar(self):
        self._angulo = (self._angulo + 30) % 360
        self.spinner.setStyleSheet(
            "background: transparent; font-size: 24px;"
            " border: 3px solid #2e2e4a;"
            " border-top: 3px solid #a78bfa;"
            " border-radius: 20px;"
            " border-top-color: #a78bfa;"
        )

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
