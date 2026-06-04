from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR: Path = Path(__file__).parent
DB_PATH: Path = Path(os.getenv("DB_PATH", str(BASE_DIR / "app.db")))

BACKUP_DIR: Path = BASE_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
