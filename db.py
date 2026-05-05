from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_db_path() -> Path:
    # USA A MESMA PASTA DO PROJETO
    base = Path(__file__).parent  # E:\controle-impressoras
    return base / "app.db"

DB_PATH = get_db_path()
ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=ENGINE)

def get_session():
    return SessionLocal()