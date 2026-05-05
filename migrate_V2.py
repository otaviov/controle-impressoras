
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from config import DB_PATH, BACKUP_DIR

def fazer_backup():
    """
    Cria backup do banco atual
    """
    if not DB_PATH.exists():
        print(" Banco de dados não encontrado em:", DB_PATH)
        print(" Verifique se o caminho está correto.")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"app_backup_{timestamp}.db"
    
    shutil.copy2(DB_PATH, backup_path)
    print(f" Backup criado: {backup_path.name}")
    print(f"   Tamanho: {backup_path.stat().st_size / 1024:.1f} KB")
    return backup_path

def verificar_estrutura_atual(cursor):
    """
    Mostra o que já existe no banco
    """
    print("\n ESTRUTURA ATUAL DO BANCO:")
    print("-" * 50)
    
    # Lista tabelas existentes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tabelas = cursor.fetchall()
    
    for tabela in tabelas:
        nome_tabela = tabela[0]
        cursor.execute(f"SELECT COUNT(*) FROM {nome_tabela}")
        qtd = cursor.fetchone()[0]
        
        # Pega colunas
        cursor.execute(f"PRAGMA table_info({nome_tabela})")
        colunas = cursor.fetchall()
        nomes_colunas = [col[1] for col in colunas]
        
        print(f"\n Tabela: {nome_tabela}")
        print(f"   Registros: {qtd}")
        print(f"   Colunas: {', '.join(nomes_colunas)}")

def adicionar_colunas_printers(cursor):
    """
    Adiciona novas colunas na tabela printers
    """
    print("\n ADICIONANDO COLUNAS EM printers...")
    print("-" * 50)
    
    novas_colunas = [
        ("marca", "VARCHAR(80) DEFAULT ''"),
        ("tipo", "VARCHAR(20) DEFAULT ''"),
        ("ip_rede", "VARCHAR(15) DEFAULT ''"),
        ("mac_address", "VARCHAR(17) DEFAULT ''"),
        ("empresa_id", "INTEGER"),
        ("proxima_revisao", "DATETIME"),
        ("tecnico", "VARCHAR(120) DEFAULT ''"),
    ]
    
    for nome, tipo in novas_colunas:
        try:
            cursor.execute(f"ALTER TABLE printers ADD COLUMN {nome} {tipo}")
            print(f"   {nome} adicionada")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"  ⏭️  {nome} já existe")
            else:
                print(f"   Erro ao adicionar {nome}: {e}")

def adicionar_colunas_activities(cursor):
    """
    Adiciona novas colunas na tabela activities
    """
    print("\n ADICIONANDO COLUNAS EM activities...")
    print("-" * 50)
    
    novas_colunas = [
        ("from_company_id", "INTEGER"),
        ("to_company_id", "INTEGER"),
        ("numero_recibo", "VARCHAR(50) DEFAULT ''"),
        ("tecnico_id", "INTEGER"),
        ("custo_servico", "FLOAT DEFAULT 0.0"),
        ("status_atividade", "VARCHAR(30) DEFAULT 'concluida'"),
    ]
    
    for nome, tipo in novas_colunas:
        try:
            cursor.execute(f"ALTER TABLE activities ADD COLUMN {nome} {tipo}")
            print(f"   {nome} adicionada")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"   {nome} já existe")
            else:
                print(f"  Erro ao adicionar {nome}: {e}")

def criar_tabelas_novas(cursor):
    """
    Cria tabelas que não existem
    """
    print("\n  CRIANDO NOVAS TABELAS...")
    print("-" * 50)
    
    tabelas = {
        "companies": """
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(150) NOT NULL,
                cnpj VARCHAR(18) UNIQUE,
                endereco VARCHAR(255) DEFAULT '',
                cidade VARCHAR(100) DEFAULT '',
                uf VARCHAR(2) DEFAULT '',
                telefone VARCHAR(20) DEFAULT '',
                email VARCHAR(120) DEFAULT '',
                tipo VARCHAR(20) DEFAULT 'cliente',
                observacao TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "users": """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(120) NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                senha_hash VARCHAR(255) NOT NULL,
                perfil VARCHAR(20) DEFAULT 'visualizador',
                ativo BOOLEAN DEFAULT 1,
                empresa_id INTEGER REFERENCES companies(id),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ultimo_login DATETIME
            )
        """,
        "transfers": """
            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                printer_id VARCHAR(36) REFERENCES printers(id),
                numero_os VARCHAR(50) DEFAULT '',
                tipo VARCHAR(20) DEFAULT 'saida',
                from_company_id INTEGER REFERENCES companies(id),
                to_company_id INTEGER REFERENCES companies(id),
                responsavel_entrega VARCHAR(120) DEFAULT '',
                responsavel_recebimento VARCHAR(120) DEFAULT '',
                data_saida DATETIME,
                data_retorno_prev DATETIME,
                data_retorno_real DATETIME,
                observacao TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "attachments": """
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type VARCHAR(50) NOT NULL,
                entity_id VARCHAR(36) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                original_name VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                mime_type VARCHAR(100) DEFAULT '',
                size_bytes INTEGER DEFAULT 0,
                categoria VARCHAR(50) DEFAULT 'outro',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                uploader_id INTEGER REFERENCES users(id)
            )
        """,
        "alerts": """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                printer_id VARCHAR(36) REFERENCES printers(id),
                tipo VARCHAR(20) DEFAULT 'revisao',
                titulo VARCHAR(150) NOT NULL,
                descricao TEXT DEFAULT '',
                data_alerta DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolvido BOOLEAN DEFAULT 0,
                resolvido_em DATETIME,
                resolvido_por INTEGER REFERENCES users(id),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "audit_logs": """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                acao VARCHAR(50) NOT NULL,
                tabela_alvo VARCHAR(50) NOT NULL,
                registro_id VARCHAR(36) NOT NULL,
                ip_address VARCHAR(45) DEFAULT '',
                dados_antes TEXT,
                dados_depois TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
    }
    
    for nome_tabela, sql in tabelas.items():
        try:
            cursor.execute(sql)
            print(f"   Tabela '{nome_tabela}' pronta")
        except Exception as e:
            print(f"   Erro ao criar '{nome_tabela}': {e}")

def criar_indices(cursor):
    """
    Cria índices para melhor performance
    """
    print("\n CRIANDO ÍNDICES...")
    print("-" * 50)
    
    indices = [
        "CREATE INDEX IF NOT EXISTS idx_activities_printer ON activities(printer_id)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_printer ON alerts(printer_id)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_pendentes ON alerts(resolvido)",
        "CREATE INDEX IF NOT EXISTS idx_transfers_printer ON transfers(printer_id)",
        "CREATE INDEX IF NOT EXISTS idx_attachments_entity ON attachments(entity_type, entity_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)",
    ]
    
    for sql in indices:
        try:
            cursor.execute(sql)
        except Exception as e:
            print(f"  ⚠️  Aviso: {e}")
    
    print("   Índices criados")

def inserir_dados_iniciais(cursor):
    """
    Insere dados padrão se necessário
    """
    print("\n VERIFICANDO DADOS INICIAIS...")
    print("-" * 50)
    
    # Verifica se já tem empresa
    cursor.execute("SELECT COUNT(*) FROM companies")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO companies (nome, tipo) VALUES ('Empresa Principal', 'filial')")
        print("   Empresa padrão criada")
    else:
        print("   Empresa já existe")
    
    # Verifica se já tem admin
    cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'admin@sistema.com'")
    if cursor.fetchone()[0] == 0:
        try:
            from passlib.hash import bcrypt
        except ImportError:
            print("   Erro: passlib não instalado. Execute: pip install passlib[bcrypt]")
            return
        
        senha_hash = bcrypt.hash("Admin@123")
        cursor.execute(
            "INSERT INTO users (nome, email, senha_hash, perfil, ativo) VALUES (?, ?, ?, ?, ?)",
            ("Administrador", "admin@sistema.com", senha_hash, "admin", 1)
        )
        print("   Usuário admin criado")
        print("     📧 Email: admin@sistema.com")
        print("     🔑 Senha: Admin@123")
    else:
        print("  ⏭  Usuário admin já existe")

def main():
    print("=" * 60)
    print(" MIGRAÇÃO SEGURA - Controle de Impressoras v2")
    print("=" * 60)
    print()
    
    # PASSO 1: Backup
    print(" PASSO 1: Criando backup...")
    backup = fazer_backup()
    if not backup:
        return
    
    # Conecta ao banco
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # PASSO 2: Mostrar estrutura atual
        verificar_estrutura_atual(cursor)
        
        # Confirmação do usuário
        print("\n" + "=" * 60)
        resposta = input("⚠️  Deseja continuar com a migração? (S/N): ")
        if resposta.upper() != 'S':
            print(" Migração cancelada pelo usuário.")
            conn.close()
            return
        
        # PASSO 3: Adicionar colunas em printers
        adicionar_colunas_printers(cursor)
        
        # PASSO 4: Adicionar colunas em activities
        adicionar_colunas_activities(cursor)
        
        # PASSO 5: Criar tabelas novas
        criar_tabelas_novas(cursor)
        
        # PASSO 6: Criar índices
        criar_indices(cursor)
        
        # PASSO 7: Inserir dados iniciais
        inserir_dados_iniciais(cursor)
        
        # COMMIT FINAL
        conn.commit()
        
        print("\n" + "=" * 60)
        print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        print(f" Seus dados foram PRESERVADOS")
        print(f" Backup salvo em: {BACKUP_DIR}")
        print(f" Novas tabelas e colunas adicionadas")
        print(f"\n Login: admin@sistema.com")
        print(f" Senha: Admin@123")
        print(f"\n  ALTERE A SENHA NO PRIMEIRO ACESSO!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n ERRO: {e}")
        print(" Rollback executado. Nenhum dado foi alterado.")
        print(f" Seu backup está seguro em: {BACKUP_DIR}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()