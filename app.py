import sys
from PySide6.QtWidgets import QApplication
from db import ENGINE, get_session
from models import Base
from ui import MainWindow

def main():
    # Cria tabelas
    Base.metadata.create_all(ENGINE)
    app = QApplication(sys.argv)
    session = get_session()
    win = MainWindow(session)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
