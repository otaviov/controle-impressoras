import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base
from app.models.user import User
from app.utils.security import hash_password


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.close()


@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
        nome="Admin Teste",
        email="admin@teste.com",
        username="admin",
        senha_hash=hash_password("123456"),
        perfil="admin",
        ativo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def inactive_user(db_session: Session) -> User:
    user = User(
        nome="Inativo",
        email="inativo@teste.com",
        username="inativo",
        senha_hash=hash_password("123456"),
        perfil="visualizador",
        ativo=False,
    )
    db_session.add(user)
    db_session.commit()
    return user
