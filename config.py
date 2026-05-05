
from pathlib import Path

# Caminho do banco de dados (MESMA PASTA DO PROJETO)
BASE_DIR = Path(__file__).parent  # E:\controle-impressoras
DB_PATH = BASE_DIR / "app.db"

# Pasta de backups
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

print(f"Database path: {DB_PATH}")
print(f"Backups: {BACKUP_DIR}")

