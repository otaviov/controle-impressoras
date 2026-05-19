import os

from PySide6.QtWidgets import QApplication, QWidget

import app.views.styles.theme as theme

_THEME_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "themes")


class TemaManager:
    @classmethod
    def atual(cls):
        return theme.atual()

    @classmethod
    def alternar(cls):
        theme.alternar()
        cls._aplicar_qss()
        return theme.atual()

    @classmethod
    def _aplicar_qss(cls):
        app = QApplication.instance()
        if not app:
            return
        qss_file = "dark_premium.qss" if theme.atual() == "dark" else "light.qss"
        path = os.path.join(_THEME_DIR, qss_file)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())

    @classmethod
    def limpar_estilos(cls, root: QWidget):
        fila = [root]
        while fila:
            w = fila.pop(0)
            w.setStyleSheet("")
            for child in w.findChildren(QWidget):
                fila.append(child)

    @classmethod
    def reestilizar_paginas(cls, widgets):
        cls._aplicar_qss()
        for w in widgets:
            cls.limpar_estilos(w)
            if hasattr(w, "recarregar"):
                w.recarregar()
