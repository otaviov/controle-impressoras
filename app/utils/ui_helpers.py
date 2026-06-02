import logging
from contextlib import contextmanager

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


def criar_botao(texto, estilo=ESTILO_BOTAO_PRIMARIO, callback=None):
    btn = QPushButton(texto)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(estilo)
    if callback:
        btn.clicked.connect(callback)
    return btn


def criar_botao_sucesso(texto, callback=None):
    return criar_botao(texto, ESTILO_BOTAO_SUCESSO, callback)


def criar_botao_erro(texto, callback=None):
    return criar_botao(texto, ESTILO_BOTAO_ERRO, callback)


def criar_botao_fechar(texto="Cancelar", callback=None):
    return criar_botao(texto, ESTILO_BOTAO_FECHAR, callback)


def criar_botao_aviso(texto, callback=None):
    return criar_botao(texto, ESTILO_BOTAO_AVISO, callback)


def criar_botao_secundario(texto, callback=None):
    return criar_botao(texto, ESTILO_BOTAO_SECUNDARIO, callback)


@contextmanager
def tratar_erro(operacao):
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
    def __init__(self, fn, *args):
        super().__init__()
        self.fn = fn
        self.args = args
        self.signals = _WorkerSignals()

    def run(self):
        try:
            self.fn(*self.args)
            self.signals.finished.emit(self.args[-1])
        except Exception as e:
            self.signals.error.emit(str(e))


def exportar_em_thread(fn, *args, on_finish=None, on_error=None):
    worker = ExportWorker(fn, *args)
    if on_finish:
        worker.signals.finished.connect(on_finish)
    if on_error:
        worker.signals.error.connect(on_error)
    else:
        def _erro_padrao(msg):
            log.exception("Erro na exportação: %s", msg)
        worker.signals.error.connect(_erro_padrao)
    QThreadPool.globalInstance().start(worker)
