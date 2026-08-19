from __future__ import annotations

import logging
from datetime import datetime as dt
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models import Company
from app.utils.helpers import formatar_data_hora
from app.utils.ui_helpers import tratar_erro
from app.views.styles.theme import (
    ATIVIDADE_CORES,
    ESTILO_BOTAO_AVISO,
    ESTILO_BOTAO_ERRO,
    ESTILO_BOTAO_FECHAR,
    ESTILO_BOTAO_PRIMARIO,
    ESTILO_BOTAO_SECUNDARIO,
    ESTILO_DIALOG,
    ESTILO_INPUT,
    ESTILO_SUBTITULO,
    ESTILO_TABELA_SIMPLES,
    ESTILO_TITULO_PAGINA,
    campo_readonly,
    campo_rotulo,
    configurar_combo,
    group_box,
    input_label,
)
from app.views.widgets.pagination import PaginacaoWidget
from app.views.widgets.search_bar import SearchBar
from app.views.widgets.table_widget import TabelaPadrao, tornar_interativa

log = logging.getLogger(__name__)

ITENS_POR_PAGINA = 20


class TransfersPage(QWidget):
    session: Any
    printer_service: Any
    activity_service: Any
    company_service: Any
    _atividades_visiveis: list[Any]
    tabela: TabelaPadrao
    _paginacao: PaginacaoWidget
    _filtro_status: str
    _filtro_busca: str

    def __init__(self, session: Any, printer_service: Any, activity_service: Any, company_service: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        self.printer_service = printer_service
        self.activity_service = activity_service
        self.company_service = company_service
        self._filtro_status = "Todos"
        self._filtro_busca = ""
        self._atividades_visiveis = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        titulo = QLabel("🚚 Transferências")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        layout.addWidget(titulo)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.btn_todos = QPushButton("Todos")
        self.btn_abertas = QPushButton("Abertas")
        self.btn_concluidas = QPushButton("Concluídas")
        for btn in (self.btn_todos, self.btn_abertas, self.btn_concluidas):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(32)
            btn.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        self.btn_todos.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
        self.btn_todos.clicked.connect(lambda: self._filtrar_status("Todos"))
        self.btn_abertas.clicked.connect(lambda: self._filtrar_status("Aberta"))
        self.btn_concluidas.clicked.connect(lambda: self._filtrar_status("Concluido"))

        toolbar.addWidget(self.btn_todos)
        toolbar.addWidget(self.btn_abertas)
        toolbar.addWidget(self.btn_concluidas)
        toolbar.addStretch()

        self.lbl_contador = QLabel("")
        self.lbl_contador.setStyleSheet(ESTILO_SUBTITULO)
        toolbar.addWidget(self.lbl_contador)
        layout.addLayout(toolbar)

        self.search = SearchBar()
        self.search.setMinimumWidth(250)
        self.search.input.textChanged.connect(self._on_busca)
        layout.addWidget(self.search)

        self.tabela = TabelaPadrao(
            colunas=["Patrimônio", "De", "Para", "Status", "Data"],
        )
        tornar_interativa(self.tabela)
        self.tabela.cellDoubleClicked.connect(self._on_duplo_clique)
        layout.addWidget(self.tabela, stretch=1)

        self._paginacao = PaginacaoWidget()
        self._paginacao.pagina_alterada.connect(self._renderizar_pagina)
        layout.addWidget(self._paginacao)

        self.recarregar()

    def recarregar(self) -> None:
        try:
            todas = self.activity_service.listar(filtro_tipo="MOVIMENTACAO", limite=500)
            self._todas_atividades = todas
            self._aplicar_filtros()
        except Exception:
            log.exception("Erro ao carregar transferências")
            self._todas_atividades = []
            self._atividades_visiveis = []
            self._renderizar_tabela()

    def _filtrar_status(self, status: str) -> None:
        self._filtro_status = status
        for btn in (self.btn_todos, self.btn_abertas, self.btn_concluidas):
            btn.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        if status == "Todos":
            self.btn_todos.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
        elif status == "Aberta":
            self.btn_abertas.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
        else:
            self.btn_concluidas.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
        self._aplicar_filtros()

    def _on_busca(self, texto: str) -> None:
        self._filtro_busca = texto.lower().strip()
        self._aplicar_filtros()

    def _aplicar_filtros(self) -> None:
        resultado = self._todas_atividades
        if self._filtro_status and self._filtro_status != "Todos":
            resultado = [a for a in resultado if a.status_atividade == self._filtro_status]
        if self._filtro_busca:
            resultado = [a for a in resultado if self._matches_busca(a)]
        self._atividades_visiveis = resultado
        self._paginacao.configurar(len(self._atividades_visiveis), 1, ITENS_POR_PAGINA)
        self._renderizar_pagina(1)

    def _matches_busca(self, a: Any) -> bool:
        termo = self._filtro_busca
        printer = self.printer_service.buscar_por_id(a.printer_id) if a.printer_id else None
        campos = [
            a.numero_recibo or "",
            a.responsavel or "",
            a.from_location or "",
            a.to_location or "",
            a.notes or "",
            a.status_atividade or "",
            printer.patrimonio if printer else "",
            printer.modelo if printer else "",
        ]
        return any(termo in c.lower() for c in campos)

    def _renderizar_pagina(self, pagina: int) -> None:
        inicio = (pagina - 1) * ITENS_POR_PAGINA
        fim = inicio + ITENS_POR_PAGINA
        paginados = self._atividades_visiveis[inicio:fim]
        total = len(self._atividades_visiveis)
        self.lbl_contador.setText(f"{total} transferência(s)")
        self._atividades_pagina = paginados
        self._renderizar_tabela()

    def _renderizar_tabela(self) -> None:
        atividades = getattr(self, '_atividades_pagina', [])
        self.tabela.setRowCount(len(atividades))
        for i, a in enumerate(atividades):
            printer = self.printer_service.buscar_por_id(a.printer_id) if a.printer_id else None
            patrimonio = printer.patrimonio if printer else "—"
            empresa_de = ""
            empresa_para = ""
            if a.from_company_id:
                c = self.session.query(Company).filter(Company.id == a.from_company_id).first()
                empresa_de = c.nome if c else str(a.from_company_id)
            if a.to_company_id:
                c = self.session.query(Company).filter(Company.id == a.to_company_id).first()
                empresa_para = c.nome if c else str(a.to_company_id)
            de = a.from_location or empresa_de or "—"
            para = a.to_location or empresa_para or "—"
            status = a.status_atividade or "—"
            data = formatar_data_hora(a.event_at) if a.event_at else "—"

            self.tabela.setItem(i, 0, self._item(patrimonio))
            self.tabela.setItem(i, 1, self._item(de))
            self.tabela.setItem(i, 2, self._item(para))
            item_status = self._item(status)
            cor = ATIVIDADE_CORES.get(status)
            if cor:
                item_status.setForeground(QColor(cor))
            self.tabela.setItem(i, 3, item_status)
            self.tabela.setItem(i, 4, self._item(data))
        self.tabela.redimensionar()

    def _item(self, texto: str):
        from PySide6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(texto)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    def _on_duplo_clique(self, row: int, _col: int) -> None:
        if 0 <= row < len(self._atividades_pagina):
            self._abrir_edicao(self._atividades_pagina[row])

    def _abrir_edicao(self, activity: Any, source: Any | None = None) -> None:
        try:
            printer = self.printer_service.buscar_por_id(activity.printer_id) if activity.printer_id else None
            dlg = _EdicaoTransferenciaDialog(
                activity=activity,
                printer=printer,
                activity_service=self.activity_service,
                printer_service=self.printer_service,
                company_service=self.company_service,
                parent=self,
            )
            if dlg.exec() == QDialog.Accepted:
                self.recarregar()
        except Exception:
            log.exception("Erro ao abrir edição de transferência")
            QMessageBox.warning(self, "Erro", "Não foi possível abrir a edição.")


class _EdicaoTransferenciaDialog(QDialog):
    def __init__(self, activity: Any, printer: Any, activity_service: Any, printer_service: Any, company_service: Any, parent: Any = None) -> None:
        super().__init__(parent)
        self.activity = activity
        self.printer = printer
        self.activity_service = activity_service
        self.printer_service = printer_service
        self.company_service = company_service
        self.setWindowTitle("Editar Transferência")
        self.setMinimumWidth(520)
        self.setMinimumHeight(420)
        self.setStyleSheet(ESTILO_DIALOG)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        patr = self.printer.patrimonio if self.printer else "—"
        modelo = self.printer.modelo if self.printer else ""
        lbl_info = QLabel(f"Transferência — {patr} {modelo}")
        lbl_info.setStyleSheet(ESTILO_SUBTITULO)
        layout.addWidget(lbl_info)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_de = QLineEdit(self.activity.from_location or "")
        self.txt_de.setPlaceholderText("Local de origem")
        self.txt_de.setStyleSheet(ESTILO_INPUT)
        form.addRow("De:", self.txt_de)

        self.txt_para = QLineEdit(self.activity.to_location or "")
        self.txt_para.setPlaceholderText("Local de destino")
        self.txt_para.setStyleSheet(ESTILO_INPUT)
        form.addRow("Para:", self.txt_para)

        self.txt_responsavel = QLineEdit(self.activity.responsavel or "")
        self.txt_responsavel.setPlaceholderText("Responsável")
        self.txt_responsavel.setStyleSheet(ESTILO_INPUT)
        form.addRow("Responsável:", self.txt_responsavel)

        self.txt_recibo = QLineEdit(self.activity.numero_recibo or "")
        self.txt_recibo.setPlaceholderText("Nº recibo")
        self.txt_recibo.setStyleSheet(ESTILO_INPUT)
        form.addRow("Recibo:", self.txt_recibo)

        self.combo_status = QComboBox()
        self.combo_status.addItems(["Aberta", "Em Deslocamento", "Concluido"])
        self.combo_status.setStyleSheet(ESTILO_INPUT)
        configurar_combo(self.combo_status)
        idx = self.combo_status.findText(self.activity.status_atividade or "Aberta")
        if idx >= 0:
            self.combo_status.setCurrentIndex(idx)
        form.addRow("Status:", self.combo_status)

        self.txt_notas = QTextEdit()
        self.txt_notas.setPlainText(self.activity.notes or "")
        self.txt_notas.setPlaceholderText("Observações...")
        self.txt_notas.setStyleSheet(ESTILO_INPUT)
        self.txt_notas.setMaximumHeight(80)
        form.addRow("Notas:", self.txt_notas)

        layout.addLayout(form)

        botoes = QDialogButtonBox()
        btn_salvar = botoes.addButton("Salvar", QDialogButtonBox.AcceptRole)
        btn_salvar.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_cancelar = botoes.addButton("Cancelar", QDialogButtonBox.RejectRole)
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        botoes.accepted.connect(self._salvar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def _salvar(self) -> None:
        try:
            dados: dict[str, Any] = {
                "from_location": self.txt_de.text().strip(),
                "to_location": self.txt_para.text().strip(),
                "responsavel": self.txt_responsavel.text().strip(),
                "numero_recibo": self.txt_recibo.text().strip(),
                "status_atividade": self.combo_status.currentText(),
                "notes": self.txt_notas.toPlainText().strip(),
            }
            self.activity_service.atualizar(self.activity, **dados)

            if self.printer and dados["to_location"]:
                self.printer_service.atualizar(self.printer, local_atual=dados["to_location"])

            QMessageBox.information(self, "Sucesso", "Transferência atualizada com sucesso!")
            self.accept()
        except Exception:
            log.exception("Erro ao salvar transferência")
            QMessageBox.critical(self, "Erro", "Erro ao salvar transferência.")
