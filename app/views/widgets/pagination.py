from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget,
)


class PaginacaoWidget(QWidget):
    pagina_alterada = Signal(int)

    _pagina_atual: int
    _total_paginas: int
    _total_registros: int
    _itens_por_pagina: int
    _btn_anterior: QPushButton
    _label_info: QLabel
    _btn_proximo: QPushButton
    _combo_itens: QComboBox

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._pagina_atual = 1
        self._total_paginas = 1
        self._total_registros = 0
        self._itens_por_pagina = 50

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        self._btn_anterior = QPushButton("« Anterior")
        self._btn_anterior.setStyleSheet(self._estilo_botao())
        self._btn_anterior.clicked.connect(self._anterior)

        self._label_info = QLabel("Página 1 de 1")
        self._label_info.setStyleSheet("color: #94949f; font-size: 12px; background: transparent;")

        self._btn_proximo = QPushButton("Próximo »")
        self._btn_proximo.setStyleSheet(self._estilo_botao())
        self._btn_proximo.clicked.connect(self._proximo)

        self._combo_itens = QComboBox()
        self._combo_itens.addItems(["20", "50", "100", "200"])
        self._combo_itens.setCurrentText("50")
        self._combo_itens.currentTextChanged.connect(self._itens_por_pagina_changed)
        self._combo_itens.setStyleSheet(
            "QComboBox { background-color: #1e1e2e; color: #e8e8f0;"
            " border: 1px solid #2a2a3e; border-radius: 6px;"
            " padding: 4px 8px; font-size: 11px; min-height: 20px; }"
        )

        layout.addWidget(self._btn_anterior)
        layout.addWidget(self._label_info)
        layout.addWidget(self._btn_proximo)
        layout.addStretch()
        lbl = QLabel("Itens/página:")
        lbl.setStyleSheet("color: #717182; font-size: 11px; background: transparent;")
        layout.addWidget(lbl)
        layout.addWidget(self._combo_itens)

        self._atualizar_botoes()

    def configurar(self, total_registros: int, pagina_atual: int = 1, itens_por_pagina: int = 50) -> None:
        self._total_registros = total_registros
        self._pagina_atual = pagina_atual
        self._itens_por_pagina = itens_por_pagina
        self._total_paginas = max(1, (total_registros + itens_por_pagina - 1) // itens_por_pagina)
        self._combo_itens.blockSignals(True)
        self._combo_itens.setCurrentText(str(itens_por_pagina))
        self._combo_itens.blockSignals(False)
        self._atualizar_label()
        self._atualizar_botoes()

    def _anterior(self) -> None:
        if self._pagina_atual > 1:
            self._pagina_atual -= 1
            self._atualizar_label()
            self._atualizar_botoes()
            self.pagina_alterada.emit(self._pagina_atual)

    def _proximo(self) -> None:
        if self._pagina_atual < self._total_paginas:
            self._pagina_atual += 1
            self._atualizar_label()
            self._atualizar_botoes()
            self.pagina_alterada.emit(self._pagina_atual)

    def _itens_por_pagina_changed(self, valor: str) -> None:
        self._itens_por_pagina = int(valor)
        self._total_paginas = max(1, (self._total_registros + self._itens_por_pagina - 1) // self._itens_por_pagina)
        self._pagina_atual = 1
        self._atualizar_label()
        self._atualizar_botoes()
        self.pagina_alterada.emit(self._pagina_atual)

    def _atualizar_label(self) -> None:
        texto = f"Página {self._pagina_atual} de {self._total_paginas}"
        if self._total_registros > 0:
            texto += f" ({self._total_registros} registro{'s' if self._total_registros != 1 else ''})"
        self._label_info.setText(texto)

    def _atualizar_botoes(self) -> None:
        self._btn_anterior.setEnabled(self._pagina_atual > 1)
        self._btn_proximo.setEnabled(self._pagina_atual < self._total_paginas)

    def _estilo_botao(self) -> str:
        return (
            "QPushButton { background-color: #1e1e2e; color: #c8c8d8;"
            " border: 1px solid #2a2a3e; border-radius: 6px;"
            " padding: 6px 14px; font-size: 11px; font-weight: 600; }"
            "QPushButton:hover { background-color: #2a2a3e; color: #e8e8f0; border-color: #6366f1; }"
            "QPushButton:disabled { color: #3a3a50; border-color: #1e1e2e; }"
        )

    @property
    def offset(self) -> int:
        return (self._pagina_atual - 1) * self._itens_por_pagina

    @property
    def limit(self) -> int:
        return self._itens_por_pagina

    @property
    def pagina(self) -> int:
        return self._pagina_atual
