# ============================================
# app.py - Controle de Impressoras Pro v2.0
# ============================================
import sys
from PySide6.QtWidgets import QApplication

from config import DB_PATH
from db import get_session

print(f"📁 Banco: {DB_PATH}")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Controle de Impressoras Pro")
    
    # Tela de Login
    from app.views.login_dialog import LoginDialog
    
    login = LoginDialog()
    if login.exec() != LoginDialog.Accepted:
        sys.exit(0)
    
    user = login.authenticated_user
    
    # Abre janela principal
    session = get_session()
    from app.views.main_window import MainWindow
    
    window = MainWindow(session, user)
    window.showMaximized()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()