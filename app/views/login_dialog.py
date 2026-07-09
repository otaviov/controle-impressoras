from __future__ import annotations

from app.models.base import utcnow
from datetime import datetime as dt, timedelta
from pathlib import Path
from typing import Any

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QKeySequence, QMouseEvent, QShortcut
from PySide6.QtWidgets import QDialog, QFrame, QLabel, QLineEdit, QPushButton, QSizePolicy, QVBoxLayout

from app.models import LoginHistory, User
from app.utils.effects import sombra_glow
from app.utils.security import verify_password
from db import close_session, get_session

MAX_TENTATIVAS: int = 5
BLOQUEIO_MINUTOS: int = 5
_attempts: dict[str, list[dt]] = {}


def _limpar_attempts_velhos() -> None:
    agora: dt = utcnow()
    limite: dt = agora - timedelta(minutes=BLOQUEIO_MINUTOS)
    for usuario in list(_attempts.keys()):
        _attempts[usuario] = [t for t in _attempts[usuario] if t > limite]
        if not _attempts[usuario]:
            del _attempts[usuario]


def _esta_bloqueado(username: str) -> bool:
    _limpar_attempts_velhos()
    return len(_attempts.get(username, [])) >= MAX_TENTATIVAS


def _registrar_tentativa(username: str) -> None:
    _attempts.setdefault(username, []).append(utcnow())


def _resetar_tentativas(username: str) -> None:
    _attempts.pop(username, None)


class LoginDialog(QDialog):
    authenticated_user: dict[str, Any] | None
    drag_pos: QPoint | None
    animation: QPropertyAnimation
    user_input: QLineEdit
    senha_input: QLineEdit
    error_label: QLabel

    def __init__(self) -> None:
        super().__init__()
        self.authenticated_user = None
        self.drag_pos = None
        self.init_ui()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_pos = None

    def init_ui(self) -> None:
        self.setWindowTitle("Controle de Impressoras Pro")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setObjectName("loginDialog")
        self.setStyleSheet("""
            #loginDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0a0f, stop:1 #14141f);
                border-radius: 20px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(0)

        # CARD INTERNO
        card = QFrame()
        card.setStyleSheet("""
            #loginCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #14141f, stop:1 #1a1a28);
                border-radius: 16px;
                border: 1px solid #2a2a3e;
            }
        """)
        card.setObjectName("loginCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 26, 28, 22)
        card_layout.setSpacing(7)
        card_layout.setAlignment(Qt.AlignCenter)

        # Logo
        from PySide6.QtGui import QPixmap
        from config import BUNDLE_DIR
        logo_path = BUNDLE_DIR / "logo.png"
        if not logo_path.exists():
            logo_path = Path(__file__).parent.parent.parent / "1.PNG"
        if not logo_path.exists():
            logo_path = Path(__file__).parent.parent.parent / "1.png"
        if logo_path.exists():
            logo_lbl = QLabel()
            pix = QPixmap(str(logo_path)).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setAlignment(Qt.AlignCenter)
            logo_lbl.setStyleSheet("background: transparent; border: none;")
            card_layout.addWidget(logo_lbl)
        else:
            icon = QLabel("🖨️")
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet("font-size: 44px; background: transparent; border: none;")
            card_layout.addWidget(icon)

        # TÍTULO
        title = QLabel("Impressoras\nBrasil Toner")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #e8e8f0; font-size: 20px; font-weight: 700;"
            " background: transparent; letter-spacing: -0.5px; line-height: 1.3;"
        )
        card_layout.addWidget(title)

        sub = QLabel("Faça login para continuar")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #94949f; font-size: 11px; background: transparent; margin-top: -4px;")
        card_layout.addWidget(sub)

        card_layout.addSpacing(18)

        # USUÁRIO
        lbl_user = QLabel("Usuário")
        lbl_user.setStyleSheet("color: #717182; font-size: 10px; font-weight: 600; background: transparent; text-transform: uppercase; letter-spacing: 0.8px;")
        card_layout.addWidget(lbl_user)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Digite seu usuário")
        self.user_input.setMinimumHeight(44)
        self.user_input.setStyleSheet(self._input_style())
        card_layout.addWidget(self.user_input)

        card_layout.addSpacing(6)

        # SENHA
        lbl_senha = QLabel("Senha")
        lbl_senha.setStyleSheet("color: #717182; font-size: 10px; font-weight: 600; background: transparent; text-transform: uppercase; letter-spacing: 0.8px;")
        card_layout.addWidget(lbl_senha)

        self.senha_input = QLineEdit()
        self.senha_input.setPlaceholderText("Digite sua senha")
        self.senha_input.setEchoMode(QLineEdit.Password)
        self.senha_input.setMinimumHeight(44)
        self.senha_input.setStyleSheet(self._input_style())
        self.senha_input.setFocus()
        card_layout.addWidget(self.senha_input)

        # ERRO
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("color: #ef4444; font-size: 11px; background: transparent; min-height: 16px;")
        card_layout.addWidget(self.error_label)

        # BOTÃO ENTRAR
        btn = QPushButton("ENTRAR")
        btn.setMinimumHeight(44)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: #6366f1;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 1px;
                margin-top: 4px;
            }
            QPushButton:hover { background: #4f46e5; }
            QPushButton:pressed { background: #4338ca; }
        """)
        btn.clicked.connect(self.fazer_login)
        QShortcut(QKeySequence("Return"), self).activated.connect(self.fazer_login)
        QShortcut(QKeySequence("Enter"), self).activated.connect(self.fazer_login)
        card_layout.addWidget(btn)

        # FECHAR
        close_btn = QPushButton("Sair")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #717182;
                border: none;
                font-size: 12px;
                padding: 4px;
                font-weight: 500;
            }
            QPushButton:hover { color: #ef4444; }
        """)
        close_btn.clicked.connect(self.reject)
        card_layout.addWidget(close_btn)

        # VERSÃO
        from app import __version__
        ver = QLabel(f"v{__version__} — Desenvolvido por Otávio Oliveira")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color: #3a3a50; font-size: 9px; background: transparent;")
        card_layout.addWidget(ver)

        main_layout.addWidget(card)

        sombra_glow(card, cor="#6366f1", blur=60)
        self.animar_entrada()

    def _input_style(self) -> str:
        return """
            QLineEdit {
                background-color: #1e1e2e;
                color: #e8e8f0;
                border: 1px solid #2a2a3e;
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 13px;
            }
            QLineEdit:hover { border-color: #3a3a50; }
            QLineEdit:focus { border-color: #6366f1; background-color: #1e1e2e; }
        """

    def animar_entrada(self) -> None:
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(400)
        self.animation.setEasingCurve(QEasingCurve.OutBack)

        screen = self.screen().geometry()
        final_x: int = (screen.width() - self.width()) // 2
        final_y: int = (screen.height() - self.height()) // 2

        self.animation.setStartValue(QPoint(final_x, final_y - 60))
        self.animation.setEndValue(QPoint(final_x, final_y))
        self.animation.start()

    def fazer_login(self) -> None:
        username: str = self.user_input.text().strip()
        senha: str = self.senha_input.text()

        if not username or not senha:
            self.mostrar_erro("Preencha todos os campos!")
            return

        if _esta_bloqueado(username):
            self.mostrar_erro(f"Muitas tentativas! Aguarde {BLOQUEIO_MINUTOS} min.")
            return

        session = get_session()
        try:
            user: User | None = session.query(User).filter(User.username == username).first()

            if not user:
                _registrar_tentativa(username)
                self.mostrar_erro("Usuário não encontrado!")
                return

            if not user.ativo:
                _registrar_tentativa(username)
                self.mostrar_erro("Usuário desativado!")
                return

            if not verify_password(senha, user.senha_hash):
                _registrar_tentativa(username)
                restam: int = MAX_TENTATIVAS - len(_attempts.get(username, []))
                self.mostrar_erro(f"Senha incorreta! ({restam} tentativa(s) restante(s))")
                return

            _resetar_tentativas(username)
            user.ultimo_login = utcnow()
            login_history = LoginHistory(user_id=user.id, login_at=utcnow())
            session.add(login_history)
            session.commit()

            self.authenticated_user = {
                "id": user.id,
                "nome": user.nome,
                "username": user.username,
                "perfil": user.perfil,
                "login_history_id": login_history.id,
            }

            self.accept()

        except Exception as e:
            session.rollback()
            self.mostrar_erro(f"Erro: {str(e)}")
        finally:
            close_session(session)

    def mostrar_erro(self, mensagem: str) -> None:
        self.error_label.setText(mensagem)
        QTimer.singleShot(3000, lambda: self.error_label.setText(""))
