import logging
import sys

from PySide6.QtWidgets import QApplication, QStyleFactory

from app.models.base import Base
from app.utils.logger import setup_logging
from config import DB_PATH
from db import ENGINE, close_session, get_session

setup_logging()
log = logging.getLogger(__name__)
log.info("DB: %s", DB_PATH)

Base.metadata.create_all(ENGINE)

def main():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setApplicationName("Controle de Impressoras Pro")

    import os
    _theme_path = os.path.join(os.path.dirname(__file__), "themes", "dark_premium.qss")
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
