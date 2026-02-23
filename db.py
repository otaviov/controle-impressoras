from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_db_path() -> Path:
    base = Path.home() / "AppData" / "Local" / "ControleImpressoras"
    base.mkdir(parents=True, exist_ok=True)
    return base / "app.db"

DB_PATH = get_db_path()
ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=ENGINE)

def get_session():
    return SessionLocal()
