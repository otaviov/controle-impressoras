from __future__ import annotations

import logging
import sqlite3
import sys
import traceback
import types

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import (QApplication, QComboBox, QDateEdit,
                                QDateTimeEdit, QMessageBox, QTimeEdit,
                                QStyleFactory)

from alembic.command import upgrade as alembic_upgrade
from alembic.config import Config as AlembicConfig
from app.utils.logger import setup_logging
from config import BUNDLE_DIR, DB_PATH
from db import ENGINE, SessionFactory, close_session, get_session

setup_logging()
log: logging.Logger = logging.getLogger(__name__)
log.info("DB: %s", DB_PATH)

_alembic_cfg = AlembicConfig(BUNDLE_DIR / "alembic.ini")
_alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{DB_PATH}")

try:
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"
    )
    precisa_migrar = cursor.fetchone() is None
    conn.close()
    if precisa_migrar:
        log.info("DB sem alembic_version — aplicando migrations completas")
except Exception:
    log.exception("Falha ao verificar alembic_version")

alembic_upgrade(_alembic_cfg, "head")

from app.utils.security import hash_password


def _criar_admin_padrao() -> None:
    try:
        from app.models.user import User
        session = SessionFactory()
        existe = session.query(User).first()
        if existe:
            session.close()
            return
        admin = User(
            nome="Administrador",
            email="admin@controleimpressoras.local",
            username="admin",
            senha_hash=hash_password("admin123"),
            perfil="admin",
            ativo=True,
        )
        session.add(admin)
        session.commit()
        log.info("Usuário admin padrão criado (admin / admin123)")
        session.close()
    except Exception:
        log.exception("Falha ao criar admin padrão")


_criar_admin_padrao()

def _excepthook(tipo: type, valor: BaseException, tb: types.TracebackType | None) -> None:
    msg = "".join(traceback.format_exception(tipo, valor, tb))
    log.critical("Exceção não tratada:\n%s", msg)
    try:
        QMessageBox.critical(None, "Erro Inesperado",
            f"Ocorreu um erro inesperado:\n\n{valor}\n\n"
            "Verifique o log para mais detalhes.")
    except Exception:
        pass

sys.excepthook = _excepthook

class _NoWheelFilter(QObject):
    _TYPES = (QComboBox, QDateEdit, QDateTimeEdit, QTimeEdit)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if isinstance(obj, self._TYPES) and event.type() == QEvent.Wheel:
            return True
        return super().eventFilter(obj, event)

def main() -> None:
    app = QApplication(sys.argv)
    app.installEventFilter(_NoWheelFilter(app))
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setApplicationName("Controle de Impressoras Pro")

    import os
    _theme_path = os.path.join(str(BUNDLE_DIR), "themes", "dark_premium.qss")
    if os.path.exists(_theme_path):
        with open(_theme_path, "r", encoding="utf-8") as _f:
            app.setStyleSheet(_f.read())

    from app.views.login_dialog import LoginDialog
    login = LoginDialog()
    if login.exec() != LoginDialog.Accepted:
        sys.exit(0)

    user = login.authenticated_user

    session = get_session()
    try:
        from app.views.main_window import MainWindow
        window = MainWindow(session, user)
        window.showMaximized()
        exit_code = app.exec()
    finally:
        close_session(session)

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
