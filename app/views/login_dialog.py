
import sqlite3
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QMouseEvent

from app.utils.security import verify_password


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.authenticated_user = None
        self.db_path = self._get_db_path()
        self.drag_pos = None  # arrasta a janela
        self.init_ui()
    
    def _get_db_path(self):
        return Path(__file__).parent.parent.parent / "app.db"
    
    # ARRASTA A JANELA 
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_pos = None
    
    def init_ui(self):
        self.setWindowTitle("Controle de Impressoras Pro")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.FramelessWindowHint)
        # Força fundo transparente pra ver as bordas arredondadas
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # FUNDO EXTERNO COM BORDAS ARREDONDADAS E GRADIENTE
        self.setStyleSheet("""
            #loginDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:1 #16213e);
                border-radius: 20px;
            }
        """)
        self.setObjectName("loginDialog")
        
        # Layout principal (preenche tudo)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(0)
        
        # CARD INTERNO
        card = QFrame()
        card.setStyleSheet("""
            #loginCard {
                background-color: #0f3460;
                border-radius: 14px;
                border: 1px solid #533483;
            }
        """)
        card.setObjectName("loginCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 22, 28, 22)
        card_layout.setSpacing(7)
        card_layout.setAlignment(Qt.AlignCenter)
        
        # ÍCONE
        icon = QLabel("🖨️")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 40px; background: transparent; border: none;")
        card_layout.addWidget(icon)
        
        # TITULO 
        title = QLabel("Impressoras Brasil Toner")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #e94560; font-size: 19px; font-weight: bold; background: transparent;")
        card_layout.addWidget(title)
        
        # SUB
        sub = QLabel("Faça login para continuar")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #a0a0b0; font-size: 11px; background: transparent;")
        card_layout.addWidget(sub)
        
        card_layout.addSpacing(14)
        
        # USUARIO 
        lbl_user = QLabel("Usuario")
        lbl_user.setStyleSheet("color: #c0c0d0; font-size: 10px; font-weight: bold; background: transparent;")
        card_layout.addWidget(lbl_user)
        
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Digite seu usuário")
        self.user_input.setText("admin")
        self.user_input.setMinimumHeight(42)
        self.user_input.setStyleSheet(self._input_style())
        card_layout.addWidget(self.user_input)
        
        card_layout.addSpacing(6)
        
        # SENHA
        lbl_senha = QLabel("Senha")
        lbl_senha.setStyleSheet("color: #c0c0d0; font-size: 10px; font-weight: bold; background: transparent;")
        card_layout.addWidget(lbl_senha)
        
        self.senha_input = QLineEdit()
        self.senha_input.setPlaceholderText("Digite sua senha")
        self.senha_input.setEchoMode(QLineEdit.Password)
        self.senha_input.setMinimumHeight(42)
        self.senha_input.setStyleSheet(self._input_style())
        self.senha_input.setFocus()
        card_layout.addWidget(self.senha_input)
        
        # ERRO
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("color: #ff6b6b; font-size: 11px; background: transparent; min-height: 16px;")
        card_layout.addWidget(self.error_label)
        
        # BOTAO ENTRAR
        btn = QPushButton("ENTRAR")
        btn.setMinimumHeight(42)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #e94560;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
                margin-top: 3px;
            }
            QPushButton:hover { background-color: #d63850; }
            QPushButton:pressed { background-color: #c02d43; }
        """)
        btn.clicked.connect(self.fazer_login)
        card_layout.addWidget(btn)
        
        # FECHAR
        close_btn = QPushButton("✕ Fechar")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #a0a0b0;
                border: none;
                font-size: 13px;
                padding: 4px;
            }
            QPushButton:hover { color: #e94560; }
        """)
        close_btn.clicked.connect(self.reject)
        card_layout.addWidget(close_btn)
        
        # VERSAO
        ver = QLabel("v2.0.0 - Desenvolvido por Otávio Oliveira" )
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color: #5a5a6a; font-size: 9px; background: transparent;")
        card_layout.addWidget(ver)
        
       
        
        # Centraliza o card
        main_layout.addWidget(card)
        
        # Animação de entrada
        self.animar_entrada()
    
    def _input_style(self):
        return """
            QLineEdit {
                background-color: #1a1a2e;
                color: #ffffff;
                border: 2px solid #533483;
                border-radius: 8px;
                padding: 9px 12px;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #e94560; }
        """
    
    def animar_entrada(self):
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(400)
        self.animation.setEasingCurve(QEasingCurve.OutBack)
        
        screen = self.screen().geometry()
        final_x = (screen.width() - self.width()) // 2
        final_y = (screen.height() - self.height()) // 2
        
        self.animation.setStartValue(QPoint(final_x, final_y - 60))
        self.animation.setEndValue(QPoint(final_x, final_y))
        self.animation.start()
    
    def fazer_login(self):
        username = self.user_input.text().strip()
        senha = self.senha_input.text()
        
        if not username or not senha:
            self.mostrar_erro("Preencha todos os campos!")
            return
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, nome, username, senha_hash, perfil, ativo FROM users WHERE username = ?",
                (username,)
            )
            
            user = cursor.fetchone()
            conn.close()
            
            if not user:
                self.mostrar_erro("Usuário não encontrado!")
                return
            
            user_id, nome, user_name, senha_hash, perfil, ativo = user
            
            if not ativo:
                self.mostrar_erro("Usuário desativado!")
                return
            
            if not verify_password(senha, senha_hash):
                self.mostrar_erro("Senha incorreta!")
                return
            
            self.authenticated_user = {
                "id": user_id,
                "nome": nome,
                "username": user_name,
                "perfil": perfil
            }

            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET ultimo_login = datetime('now') WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            
            self.accept()
            
        except Exception as e:
            self.mostrar_erro(f"Erro: {str(e)}")
    
    def mostrar_erro(self, mensagem):
        self.error_label.setText(mensagem)
        QTimer.singleShot(3000, lambda: self.error_label.setText(""))