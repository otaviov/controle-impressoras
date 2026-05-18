import sys
from PySide6.QtWidgets import QApplication

from config import DB_PATH
from db import get_session

print(f"DB: {DB_PATH}")

def main():
    app = QApplication(sys.argv)
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
    from app.views.main_window import MainWindow
    window = MainWindow(session, user)
    window.showMaximized()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
