from datetime import datetime

from app.models.company import Company
from app.models.printer import Printer
from app.models.user import User
from app.utils.security import hash_password


def test_create_user(db_session):
    user = User(
        nome="João",
        email="joao@teste.com",
        username="joao",
        senha_hash=hash_password("123"),
        perfil="tecnico",
    )
    db_session.add(user)
    db_session.commit()

    saved = db_session.query(User).filter_by(username="joao").first()
    assert saved is not None
    assert saved.nome == "João"
    assert saved.perfil == "tecnico"
    assert saved.ativo is True


def test_create_printer(db_session):
    printer = Printer(
        patrimonio="PAT001",
        modelo="HP LaserJet M404",
        serial="ABC123",
        status="Operacional",
        local_atual="Matriz",
    )
    db_session.add(printer)
    db_session.commit()

    saved = db_session.query(Printer).filter_by(patrimonio="PAT001").first()
    assert saved is not None
    assert saved.modelo == "HP LaserJet M404"


def test_printer_default_status(db_session):
    printer = Printer(patrimonio="PAT002", modelo="Epson L3250")
    db_session.add(printer)
    db_session.commit()

    assert printer.status == "Operacional"


def test_login_admin_success(db_session, admin_user):
    from app.utils.security import verify_password
    user = db_session.query(User).filter_by(username="admin").first()
    assert user is not None
    assert user.ativo is True
    assert verify_password("123456", user.senha_hash)


def test_login_inactive_user_fails(db_session, inactive_user):
    user = db_session.query(User).filter_by(username="inativo").first()
    assert user is not None
    assert user.ativo is False


def test_login_wrong_password(db_session, admin_user):
    from app.utils.security import verify_password
    assert not verify_password("senha_errada", admin_user.senha_hash)


def test_create_company(db_session):
    company = Company(nome="Empresa Teste", tipo="filial")
    db_session.add(company)
    db_session.commit()

    saved = db_session.query(Company).filter_by(nome="Empresa Teste").first()
    assert saved is not None
    assert saved.tipo == "filial"


# ═══════════════════════════════════════════════════════════════
# Edge cases – Model defaults & nullables
# ═══════════════════════════════════════════════════════════════

def test_printer_all_nullable_fields(db_session):
    p = Printer(patrimonio="NULLS01", modelo="HP")
    db_session.add(p)
    db_session.commit()
    assert p.serial == ""
    assert p.marca == ""
    assert p.tipo == ""
    assert p.ip_rede == ""
    assert p.observacao == ""
    assert p.mac_address == ""
    assert p.tecnico == ""


def test_printer_soft_delete_default(db_session):
    p = Printer(patrimonio="SDEL", modelo="HP")
    db_session.add(p)
    db_session.commit()
    assert p.deleted_at is None


def test_user_defaults(db_session):
    from app.utils.security import hash_password
    u = User(nome="Default", username="default", email="d@t.com", senha_hash=hash_password("123"))
    db_session.add(u)
    db_session.commit()
    assert u.ativo is True
    assert u.perfil == "visualizador"


def test_technician_soft_delete_default(db_session):
    from app.models.technician import Technician
    t = Technician(nome_completo="Tec", telefone="81")
    db_session.add(t)
    db_session.commit()
    assert t.deleted_at is None
    assert t.ativo is True


def test_part_default_estoque(db_session):
    from app.models.part import Part
    p = Part(codigo="PADRAO", nome="Peça Padrão")
    db_session.add(p)
    db_session.commit()
    assert p.quantidade_estoque == 0
    assert p.estoque_minimo == 1
    assert p.deleted_at is None


def test_alert_defaults(db_session):
    from app.models.alert import Alert
    a = Alert(tipo="info", titulo="Teste")
    db_session.add(a)
    db_session.commit()
    assert a.resolvido is False
    assert a.notificado is False
    assert a.deleted_at is None
    assert a.printer_id is None
    assert a.part_id is None


def test_attachment_defaults(db_session):
    from app.models.attachment import Attachment
    a = Attachment(entity_type="printer", entity_id=1, filename="test.pdf", original_name="test.pdf", mime_type="application/pdf")
    db_session.add(a)
    db_session.commit()
    assert a.created_at is not None


def test_login_history_defaults(db_session):
    from app.models.login_history import LoginHistory
    lh = LoginHistory(user_id=1, login_at=datetime.now())
    db_session.add(lh)
    db_session.commit()
    assert lh.logout_at is None


def test_audit_log_defaults(db_session):
    from app.models.audit_log import AuditLog
    log = AuditLog(user_id=1, acao="CRIAR", tabela_alvo="printers", registro_id="abc")
    db_session.add(log)
    db_session.commit()
    assert log.dados_antes is None
    assert log.dados_depois is None


def test_printer_activity_relationship_empty(db_session):
    p = Printer(patrimonio="NOREL", modelo="HP")
    db_session.add(p)
    db_session.commit()
    assert p.activities == []


def test_company_printers_relationship_empty(db_session):
    c = Company(nome="Sem Impressoras")
    db_session.add(c)
    db_session.commit()
    assert c.printers == []
