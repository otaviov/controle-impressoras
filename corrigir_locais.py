import sqlite3
from config import DB_PATH

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

# MOSTRA ANTES
cursor.execute("SELECT local_atual, COUNT(*) FROM printers GROUP BY local_atual ORDER BY local_atual")
print("📍 ANTES:")
for row in cursor.fetchall():
    print(f"  '{row[0]}' = {row[1]} impressora(s)")

# CORRIGE TUDO que contém "rasil", "RASIL", "ASIL", "TONER"
cursor.execute("UPDATE printers SET local_atual = 'Brasil Toner' WHERE local_atual LIKE '%rasil%'")
print(f"✅ Linhas afetadas (rasil): {cursor.rowcount}")

cursor.execute("UPDATE printers SET local_atual = 'Brasil Toner' WHERE local_atual LIKE '%RASIL%'")
print(f"✅ Linhas afetadas (RASIL): {cursor.rowcount}")

cursor.execute("UPDATE printers SET local_atual = 'Brasil Toner' WHERE local_atual LIKE '%ASIL TONER%'")
print(f"✅ Linhas afetadas (ASIL): {cursor.rowcount}")

cursor.execute("UPDATE printers SET local_atual = 'Brasil Toner' WHERE local_atual LIKE '%TONER%' AND local_atual != 'Brasil Toner'")
print(f"✅ Linhas afetadas (TONER): {cursor.rowcount}")

cursor.execute("UPDATE printers SET local_atual = 'Sede Recife' WHERE local_atual LIKE '%Sede Recif%' AND local_atual != 'Sede Recife'")
print(f"✅ Linhas afetadas (Recife): {cursor.rowcount}")

conn.commit()

# MOSTRA DEPOIS
cursor.execute("SELECT local_atual, COUNT(*) FROM printers GROUP BY local_atual ORDER BY local_atual")
print("\n📍 DEPOIS:")
for row in cursor.fetchall():
    print(f"  '{row[0]}' = {row[1]} impressora(s)")

conn.close()
print("\n🎉 Concluído!")