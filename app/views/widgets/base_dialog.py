from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton

import app.views.styles.theme as theme


class DialogoBase(QDialog):
    def __init__(self, titulo, parent=None, largura=500, altura=500):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumSize(largura, altura)
        c = theme.COR
        self.setStyleSheet(f"QDialog {{ background-color: {c['fundo']}; }}")

    def botao_salvar(self, texto="💾 Salvar"):
        btn = QPushButton(texto)
        btn.setCursor(Qt.PointingHandCursor)
        c = theme.COR
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {c['azul']},stop:1 {c['azul']}dd);
                color: #ffffff;
                border: none; border-radius: 8px;
                padding: 10px 20px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #93c5fd,stop:1 {c['azul']}); }}
        """)
        return btn

    def botao_excluir(self, texto="🗑️ Excluir"):
        btn = QPushButton(texto)
        btn.setCursor(Qt.PointingHandCursor)
        c = theme.COR
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #f87171,stop:1 #ef4444);
                color: #ffffff;
                border: none; border-radius: 8px;
                padding: 10px 20px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #fca5a5,stop:1 #f87171); }}
        """)
        return btn

    def botao_cancelar(self, texto="Cancelar"):
        c = theme.COR
        btn = QPushButton(texto)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {c['texto_sec']};
                border: 1px solid {c['borda']}; border-radius: 8px;
                padding: 10px 20px; font-size: 13px; font-weight: 500;
            }}
            QPushButton:hover {{ background-color: {c['hover']}; color: {c['texto']}; }}
        """)
        btn.clicked.connect(self.reject)
        return btn

    def botoes_layout(self):
        layout = QHBoxLayout()
        layout.setSpacing(10)
        return layout
