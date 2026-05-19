from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget


class ToastManager:
    _container = None

    @classmethod
    def instalar(cls, parent: QWidget):
        if cls._container is None:
            cls._container = _ToastContainer(parent)

    @classmethod
    def mostrar(cls, mensagem: str, tipo: str = "info", duracao: int = 4000, persistente: bool = False):
        if cls._container:
            cls._container.adicionar(mensagem, tipo, duracao, persistente)

    @classmethod
    def info(cls, mensagem: str, persistente: bool = False):
        cls.mostrar(mensagem, "info", persistente=persistente)

    @classmethod
    def sucesso(cls, mensagem: str, persistente: bool = False):
        cls.mostrar(mensagem, "sucesso", persistente=persistente)

    @classmethod
    def aviso(cls, mensagem: str, persistente: bool = False):
        cls.mostrar(mensagem, "aviso", persistente=persistente)

    @classmethod
    def erro(cls, mensagem: str, persistente: bool = False):
        cls.mostrar(mensagem, "erro", persistente=persistente)

    @classmethod
    def limpar_persistentes(cls):
        if cls._container:
            cls._container._limpar_persistentes()

    @classmethod
    def atualizar_status(cls, pendentes: int):
        cls.limpar_persistentes()
        if pendentes:
            cls.aviso(f"{pendentes} alerta(s) pendente(s)", persistente=True)
        else:
            cls.sucesso("Nenhum alerta pendente")


CORES_TOAST = {
    "info": {"bg": "#1e1e3a", "borda": "#a78bfa", "icone": "ℹ"},
    "sucesso": {"bg": "#0a2e1a", "borda": "#34d399", "icone": "✓"},
    "aviso": {"bg": "#2e2a0a", "borda": "#fbbf24", "icone": "⚠"},
    "erro": {"bg": "#2e0a0a", "borda": "#f87171", "icone": "✕"},
}


class _ToastContainer(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._toasts = []
        self._margem = 20
        self._espaco = 8
        self.setFixedWidth(360)
        self._reposicionar_container()
        self.show()

    def _reposicionar_container(self):
        p = self.parent()
        if p:
            self.move(p.width() - self.width() - self._margem, 10)
            self.raise_()

    def adicionar(self, mensagem, tipo, duracao, persistente=False):
        toast = _Toast(self, mensagem, tipo, duracao, persistente)
        self._toasts.append(toast)
        toast.mostrar()
        self._reposicionar_toasts()

    def remover(self, toast):
        if toast in self._toasts:
            self._toasts.remove(toast)
            toast.deleteLater()
        self._reposicionar_toasts()

    def _limpar_persistentes(self):
        for t in list(self._toasts):
            if t._persistente:
                self._toasts.remove(t)
                t.deleteLater()

    def _reposicionar_toasts(self):
        y = 0
        for t in self._toasts:
            if t.isVisible():
                t.move(0, y)
                y += t.height() + self._espaco
        self.setFixedHeight(y if y > 0 else 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposicionar_container()


class _Toast(QFrame):
    def __init__(self, container, mensagem, tipo, duracao, persistente=False):
        super().__init__(container)
        self._container = container
        self._duracao = duracao
        self._persistente = persistente
        cor = CORES_TOAST.get(tipo, CORES_TOAST["info"])

        self.setFixedWidth(340)
        self.setStyleSheet(f"""
            _Toast {{
                background-color: {cor['bg']};
                border: 1px solid {cor['borda']};
                border-radius: 10px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        lbl_icone = QLabel(cor["icone"])
        lbl_icone.setStyleSheet(f"font-size: 16px; color: {cor['borda']}; background: transparent;")
        lbl_icone.setFixedWidth(20)
        layout.addWidget(lbl_icone)

        lbl_msg = QLabel(mensagem)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("color: #e2e8f0; font-size: 12px; background: transparent;")
        layout.addWidget(lbl_msg, 1)

        btn_fechar = QPushButton("X")
        btn_fechar.setFixedSize(24, 24)
        btn_fechar.setCursor(Qt.PointingHandCursor)
        btn_fechar.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.08); color: #94a3b8; border: none; border-radius: 12px; font-size: 11px; font-weight: 700; }"
            " QPushButton:hover { background: rgba(248,113,113,0.3); color: #f87171; }"
        )
        btn_fechar.clicked.connect(self.fechar)
        layout.addWidget(btn_fechar)

        self._anim_entrada = None
        self._anim_saida = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.fechar)

    def mostrar(self):
        self.adjustSize()
        self._container._reposicionar_container()

        idx = len(self._container._toasts) - 1
        y = idx * (self.height() + self._container._espaco)
        self.move(360, y)
        self.show()

        self._anim_entrada = QPropertyAnimation(self, b"pos")
        self._anim_entrada.setDuration(300)
        self._anim_entrada.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_entrada.setStartValue(QPoint(360, y))
        self._anim_entrada.setEndValue(QPoint(0, y))
        self._anim_entrada.start()

        self._container.setFixedHeight(y + self.height())

        if not self._persistente:
            self._timer.start(self._duracao)

    def fechar(self):
        self._timer.stop()
        self._anim_saida = QPropertyAnimation(self, b"pos")
        self._anim_saida.setDuration(250)
        self._anim_saida.setEasingCurve(QEasingCurve.InCubic)
        self._anim_saida.setStartValue(self.pos())
        self._anim_saida.setEndValue(QPoint(360, self.pos().y()))
        self._anim_saida.finished.connect(self._finalizar)
        self._anim_saida.start()

    def _finalizar(self):
        self._container.remover(self)
