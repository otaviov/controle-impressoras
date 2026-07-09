from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from config import DB_PATH

log: logging.Logger = logging.getLogger(__name__)

ENGINE: Engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},
)


@event.listens_for(ENGINE, "connect")
def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.close()

SessionFactory: sessionmaker = sessionmaker(bind=ENGINE)
ScopedSession: scoped_session = scoped_session(SessionFactory)

def get_session() -> Session:
    return ScopedSession()

def close_session(session: Session | None) -> None:
    if session:
        try:
            session.close()
        except Exception as exc:
            log.warning("Erro ao fechar sessão: %s", exc)


@contextmanager
def transacao(session: Session) -> Iterator[None]:
    """Context manager for atomic transactions.
    
    Service calls inside this block use flush() instead of commit(),
    so the entire block is committed atomically on success,
    or fully rolled back on any error.
    """
    session.info["_em_transacao"] = True
    try:
        yield
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.info.pop("_em_transacao", None)


def safe_commit(session: Session) -> None:
    """Commits or flushes depending on whether we're inside a transacao() block."""
    try:
        if session.info.get("_em_transacao"):
            session.flush()
        else:
            session.commit()
    except Exception:
        session.rollback()
        raise
