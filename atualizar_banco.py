import sqlite3
from db import DB_PATH

def atualizar():
    # Conecta diretamente ao arquivo do banco de dados
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    novas_colunas = [
        ("pecas_faltantes", "TEXT"),
        ("tecnico_revisao", "TEXT"),
        ("ultima_revisao_data", "DATETIME")
    ]

    for nome_coluna, tipo in novas_colunas:
        try:
            cursor.execute(f"ALTER TABLE printers ADD COLUMN {nome_coluna} {tipo}")
            print(f"Coluna {nome_coluna} adicionada com sucesso!")
        except sqlite3.OperationalError:
            print(f"Coluna {nome_coluna} já existe ou erro na tabela.")

    conn.commit()
    conn.close()
    print("Processo de atualização finalizado.")

if __name__ == "__main__":
    atualizar()