import re
from collections.abc import Callable
from typing import Optional

from PySide6.QtWidgets import QLabel, QLineEdit

from app.views.styles.theme import ESTILO_INPUT


_PADRAO_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

Regra = Callable[[str], Optional[str]]


class ValidadorCampo:
    def __init__(self, line_edit: QLineEdit, regra: Regra, label_erro: Optional[QLabel] = None) -> None:
        self._line: QLineEdit = line_edit
        self._regra: Regra = regra
        self._label_erro: Optional[QLabel] = label_erro
        self._base: str = ESTILO_INPUT
        line_edit.textChanged.connect(lambda: self._validar())
        self._validar()

    def _validar(self) -> None:
        texto: str = self._line.text()
        erro: Optional[str] = self._regra(texto)
        if erro:
            self._line.setStyleSheet(self._base + " border-color: #ef4444;")
            if self._label_erro:
                self._label_erro.setText(erro)
                self._label_erro.show()
        elif texto:
            self._line.setStyleSheet(self._base + " border-color: #10b981;")
            if self._label_erro:
                self._label_erro.hide()
        else:
            self._line.setStyleSheet(self._base)
            if self._label_erro:
                self._label_erro.hide()

    @property
    def valido(self) -> bool:
        return self._regra(self._line.text()) is None


def obrigatorio(texto: str) -> Optional[str]:
    if not texto.strip():
        return "Campo obrigatório"
    return None


def email(texto: str) -> Optional[str]:
    if not texto.strip():
        return "Campo obrigatório"
    if not _PADRAO_EMAIL.match(texto.strip()):
        return "E-mail inválido"
    return None


def email_opcional(texto: str) -> Optional[str]:
    if not texto.strip():
        return None
    if not _PADRAO_EMAIL.match(texto.strip()):
        return "E-mail inválido"
    return None


def minimo(n: int) -> Regra:
    def _regra(texto: str) -> Optional[str]:
        if texto.strip() and len(texto.strip()) < n:
            return f"Mínimo de {n} caracteres"
        return None
    return _regra


def alfanumerico(texto: str) -> Optional[str]:
    if not texto.strip():
        return "Campo obrigatório"
    if not texto.strip().isalnum():
        return "Apenas letras e números"
    return None


def email(texto):
    if not texto.strip():
        return "Campo obrigatório"
    if not _PADRAO_EMAIL.match(texto.strip()):
        return "E-mail inválido"
    return None


def minimo(n):
    def _regra(texto):
        if texto.strip() and len(texto.strip()) < n:
            return f"Mínimo de {n} caracteres"
        return None
    return _regra


def alfanumerico(texto):
    if not texto.strip():
        return "Campo obrigatório"
    if not texto.strip().isalnum():
        return "Apenas letras e números"
    return None
