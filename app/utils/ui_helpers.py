from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal
from PySide6.QtWidgets import QPushButton
from sqlalchemy.exc import SQLAlchemyError

from app.views.styles.theme import (
    ESTILO_BOTAO_AVISO,
    ESTILO_BOTAO_ERRO,
    ESTILO_BOTAO_FECHAR,
    ESTILO_BOTAO_PRIMARIO,
    ESTILO_BOTAO_SECUNDARIO,
    ESTILO_BOTAO_SUCESSO,
)
from app.views.widgets.toast import ToastManager

log = logging.getLogger(__name__)


def criar_botao(texto: str, estilo: str = ESTILO_BOTAO_PRIMARIO, callback: Callable[[], object] | None = None) -> QPushButton:
    btn = QPushButton(texto)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(estilo)
    if callback:
        btn.clicked.connect(callback)
    return btn


def criar_botao_sucesso(texto: str, callback: Callable[[], object] | None = None) -> QPushButton:
    return criar_botao(texto, ESTILO_BOTAO_SUCESSO, callback)


def criar_botao_erro(texto: str, callback: Callable[[], object] | None = None) -> QPushButton:
    return criar_botao(texto, ESTILO_BOTAO_ERRO, callback)


def criar_botao_fechar(texto: str = "Cancelar", callback: Callable[[], object] | None = None) -> QPushButton:
    return criar_botao(texto, ESTILO_BOTAO_FECHAR, callback)


def criar_botao_aviso(texto: str, callback: Callable[[], object] | None = None) -> QPushButton:
    return criar_botao(texto, ESTILO_BOTAO_AVISO, callback)


def criar_botao_secundario(texto: str, callback: Callable[[], object] | None = None) -> QPushButton:
    return criar_botao(texto, ESTILO_BOTAO_SECUNDARIO, callback)


@contextmanager
def tratar_erro(operacao: str) -> Iterator[None]:
    try:
        yield
    except SQLAlchemyError:
        log.exception("Erro em %s", operacao)
        ToastManager.erro(f"Erro ao {operacao}. Verifique os dados e tente novamente.")
    except Exception:
        log.exception("Erro inesperado em %s", operacao)
        ToastManager.erro(f"Erro inesperado ao {operacao}.")


class _WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(str)


class ExportWorker(QRunnable):
    def __init__(self, fn: Callable[..., Any], *args: Any) -> None:
        super().__init__()
        self.fn: Callable[..., Any] = fn
        self.args: tuple[Any, ...] = args
        self.signals: _WorkerSignals = _WorkerSignals()

    def run(self) -> None:
        try:
            self.fn(*self.args)
            self.signals.finished.emit(self.args[-1])
        except Exception as e:
            self.signals.error.emit(str(e))


def exportar_em_thread(fn: Callable[..., Any], *args: Any, on_finish: Callable[[object], object] | None = None, on_error: Callable[[str], object] | None = None) -> None:
    worker = ExportWorker(fn, *args)
    if on_finish:
        worker.signals.finished.connect(on_finish)
    if on_error:
        worker.signals.error.connect(on_error)
    else:
        def _erro_padrao(msg: str) -> None:
            log.exception("Erro na exportação: %s", msg)
        worker.signals.error.connect(_erro_padrao)
    QThreadPool.globalInstance().start(worker)
