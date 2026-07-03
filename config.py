from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

if getattr(sys, 'frozen', False):
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / "ControleImpressoras")))
    BUNDLE_DIR: Path = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
else:
    DATA_DIR: Path = Path(__file__).parent
    BUNDLE_DIR: Path = Path(__file__).parent

BASE_DIR: Path = BUNDLE_DIR
DB_PATH: Path = Path(os.getenv("DB_PATH", str(DATA_DIR / "app.db")))

BACKUP_DIR: Path = DATA_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

ANEXOS_DIR: Path = DATA_DIR / "anexos"
ANEXOS_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
