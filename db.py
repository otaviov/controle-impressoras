import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from config import DB_PATH

log = logging.getLogger(__name__)

ENGINE = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},
)


@event.listens_for(ENGINE, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()

SessionFactory = sessionmaker(bind=ENGINE)
ScopedSession = scoped_session(SessionFactory)

def get_session() -> Session:
    return ScopedSession()

def close_session(session: Session | None) -> None:
    if session:
        try:
            session.close()
        except Exception as exc:
            log.warning("Erro ao fechar sessão: %s", exc)

def safe_commit(session: Session) -> None:
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
