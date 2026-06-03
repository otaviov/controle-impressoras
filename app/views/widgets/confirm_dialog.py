from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QFrame,
)

from app.views.styles.theme import (
    COR,
    ESTILO_BOTAO_ERRO,
    ESTILO_BOTAO_SECUNDARIO,
    ESTILO_INPUT,
)

_ESTILO_BOTAO_CONFIRMAR = ESTILO_BOTAO_ERRO + """\
    QPushButton:disabled {
        background: #3a3a50; color: #717182;
        border: 1px solid #2a2a3e; border-radius: 8px;
    }
"""


class ConfirmacaoDigitarDialog(QDialog):
    def __init__(
        self,
        titulo: str,
        mensagem: str,
        parent=None,
        palavra_chave: str = "EXCLUIR",
    ):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(420)
        self.palavra_chave = palavra_chave.upper()
        self.confirmado = False
        self._setup_ui(mensagem)

    def _setup_ui(self, mensagem: str):
        self.setStyleSheet(
            f"QDialog {{ background-color: {COR['fundo_card']}; }}"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QHBoxLayout()
        icon = QLabel("\U000026A0\U0000FE0F")
        icon.setStyleSheet("font-size: 28px; background: transparent;")
        title = QLabel(self.windowTitle())
        title.setStyleSheet(
            f"font-size: 16px; font-weight: 700; color: {COR['erro']};"
            " background: transparent;"
        )
        header.addWidget(icon)
        header.addWidget(title, 1)
        layout.addLayout(header)

        msg = QLabel(mensagem)
        msg.setWordWrap(True)
        msg.setStyleSheet(
            f"color: {COR['texto_sec']}; font-size: 12px;"
            " background: transparent;"
        )
        layout.addWidget(msg)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(
            f"background: {COR['borda']}; max-height: 1px; border: none;"
        )
        layout.addWidget(sep)

        instr = QLabel(
            f'Digite <b style="color:{COR["erro"]};">{self.palavra_chave}</b>'
            " para confirmar:"
        )
        instr.setWordWrap(True)
        instr.setStyleSheet(
            f"color: {COR['texto']}; font-size: 12px; background: transparent;"
        )
        layout.addWidget(instr)

        self.input = QLineEdit()
        self.input.setMaxLength(30)
        self.input.setStyleSheet(ESTILO_INPUT)
        self.input.setPlaceholderText(self.palavra_chave)
        layout.addWidget(self.input)

        botoes = QHBoxLayout()
        botoes.addStretch()

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        self.btn_cancelar.setCursor(Qt.PointingHandCursor)
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_confirmar = QPushButton("Confirmar")
        self.btn_confirmar.setStyleSheet(_ESTILO_BOTAO_CONFIRMAR)
        self.btn_confirmar.setCursor(Qt.PointingHandCursor)
        self.btn_confirmar.setEnabled(False)
        self.btn_confirmar.clicked.connect(self._confirmar)

        botoes.addWidget(self.btn_cancelar)
        botoes.addWidget(self.btn_confirmar)
        layout.addLayout(botoes)

        self.input.textChanged.connect(self._verificar)
        self.input.returnPressed.connect(self._confirmar)

    def _verificar(self, texto: str):
        self.btn_confirmar.setEnabled(texto.strip().upper() == self.palavra_chave)

    def _confirmar(self):
        if not self.btn_confirmar.isEnabled():
            return
        self.confirmado = True
        self.accept()

    @classmethod
    def confirmar(
        cls,
        titulo: str,
        mensagem: str,
        parent=None,
        palavra_chave: str = "EXCLUIR",
    ) -> bool:
        dlg = cls(titulo, mensagem, parent, palavra_chave)
        dlg.exec()
        return dlg.confirmado
