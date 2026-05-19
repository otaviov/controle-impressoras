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
