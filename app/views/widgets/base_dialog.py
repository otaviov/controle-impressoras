from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

from app.views.styles.theme import ESTILO_DIALOG, ESTILO_BOTAO_SUCESSO, ESTILO_BOTAO_ERRO


class DialogoBase(QDialog):
    def __init__(self, titulo, parent=None, largura=500, altura=500):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumSize(largura, altura)
        self.setStyleSheet(ESTILO_DIALOG)

    def botao_salvar(self, texto="💾 Salvar"):
        btn = QPushButton(texto)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        return btn

    def botao_excluir(self, texto="🗑️ Excluir"):
        btn = QPushButton(texto)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(ESTILO_BOTAO_ERRO)
        return btn

    def botao_cancelar(self, texto="Cancelar"):
        from app.views.styles.theme import ESTILO_BOTAO_FECHAR
        btn = QPushButton(texto)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn.clicked.connect(self.reject)
        return btn

    def botoes_layout(self):
        layout = QHBoxLayout()
        layout.setSpacing(10)
        return layout
