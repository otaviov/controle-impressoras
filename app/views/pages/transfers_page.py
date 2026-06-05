from __future__ import annotations

import os
import shutil
from datetime import datetime as dt
from pathlib import Path
from typing import Any
from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models import Activity, Attachment, Part
from app.services.part_service import PartService
from app.utils.ui_helpers import tratar_erro
from db import safe_commit, transacao
from app.utils.helpers import encurtar, formatar_data_hora
from app.views.widgets.pagination import PaginacaoWidget
from config import BASE_DIR
from app.views.styles.theme import (
    COR,
    ESTILO_BOTAO_AVISO,
    ESTILO_BOTAO_ERRO,
    ESTILO_BOTAO_FECHAR,
    ESTILO_BOTAO_SUCESSO,
    ESTILO_COMBO,
    ESTILO_DIALOG,
    ESTILO_INPUT,
    ESTILO_TABELA_SIMPLES,
    ESTILO_TITULO_PAGINA,
    STATUS_ATIVIDADE_OPCOES,
    configurar_combo,
    group_box,
    input_label,
    campo_rotulo,
    campo_readonly,
)
from app.views.widgets import ToastManager
from app.views.widgets.card_widget import CardMiniWidget
from app.views.widgets.confirm_dialog import ConfirmacaoDigitarDialog
from app.views.widgets.search_bar import SearchBar
from app.views.widgets.table_widget import TabelaPadrao


def _criar_mascara_data(le: QLineEdit) -> Callable[[str], None]:
    """Retorna callback que formata dd/mm/aaaa automaticamente no QLineEdit dado."""
    def _mascarar(texto: str) -> None:
        old_pos = le.cursorPosition()
        digits = ''.join(c for c in texto if c.isdigit())[:8]
        if not digits and texto:
            le.blockSignals(True)
            le.clear()
            le.blockSignals(False)
            return
        partes = [digits[:2]]
        if len(digits) > 2:
            partes.append(digits[2:4])
        if len(digits) > 4:
            partes.append(digits[4:8])
        nova = '/'.join(partes)
        if nova != texto:
            le.blockSignals(True)
            le.setText(nova)
            le.blockSignals(False)
            le.setCursorPosition(old_pos + (len(nova) - len(texto)))
    return _mascarar


COR_STATUS: dict[str, str] = {
    "pendente": "#fbbf24",
    "em_andamento": "#60a5fa",
    "concluida": "#34d399",
}

ANEXOS_DIR: Path = BASE_DIR / "anexos"


class TransfersPage(QWidget):
    COLUNAS: list[str] = ["Data", "Patrimônio", "Origem", "Destino", "Peças/Equipamento", "Nº Recibo", "Status"]

    _session: Any
    printer_service: Any
    activity_service: Any
    company_service: Any
    transfer_service: Any | None
    part_service: PartService
    _mov_cache: list[Any]
    _mapa_cache: dict[Any, str]
    _filtro_transf: str | None
    search: SearchBar
    btn_nova: QPushButton
    card_total: CardMiniWidget
    card_saidas: CardMiniWidget
    card_entradas: CardMiniWidget
    card_pendentes: CardMiniWidget
    tabela: TabelaPadrao
    _paginacao: PaginacaoWidget

    def __init__(self, session: Any, printer_service: Any, activity_service: Any, company_service: Any, transfer_service: Any | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session = session
        self.printer_service = printer_service
        self.activity_service = activity_service
        self.company_service = company_service
        self.transfer_service = transfer_service
        self.part_service = PartService(session)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        titulo = QLabel("\U0001f69a Transferências / Movimentações")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        header.addWidget(titulo)
        header.addStretch()

        self.btn_nova = QPushButton("➕ Nova Transferência")
        self.btn_nova.setToolTip("Registrar nova transferência de impressora ou peça")
        self.btn_nova.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        self.btn_nova.clicked.connect(self._nova)
        header.addWidget(self.btn_nova)
        layout.addLayout(header)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.card_total = CardMiniWidget("\U0001f4cb", "Total Transf.", "0", COR["azul"])
        self.card_saidas = CardMiniWidget("\U0001f4e4", "Saídas", "0", COR["erro"])
        self.card_entradas = CardMiniWidget("\U0001f4e5", "Entradas", "0", COR["sucesso"])
        self.card_pendentes = CardMiniWidget("\u23f3", "Pendentes", "0", COR["aviso"])
        cards.addWidget(self.card_total)
        cards.addWidget(self.card_saidas)
        cards.addWidget(self.card_entradas)
        cards.addWidget(self.card_pendentes)
        layout.addLayout(cards)

        self.search = SearchBar("Buscar por patrimônio, origem, destino...")
        self.search.textChanged().connect(self._filtrar)
        layout.addWidget(self.search)

        self.tabela = TabelaPadrao(self.COLUNAS)
        self.tabela.cellDoubleClicked.connect(self._detalhes)
        layout.addWidget(self.tabela)

        self._mov_cache = []
        self._mapa_cache = {}
        self._filtro_transf = None
        self._paginacao = PaginacaoWidget()
        self._paginacao.pagina_alterada.connect(lambda p: self._carregar())
        layout.addWidget(self._paginacao)

    def recarregar(self) -> None:
        self._filtro_transf = None
        self._carregar()

    def _carregar(self) -> None:
        if self._filtro_transf:
            movimentacoes = self.activity_service.buscar_movimentacoes_por_filtro(
                self._filtro_transf, limite=self._paginacao.limit, offset=self._paginacao.offset,
            )
            total = len(movimentacoes)
        else:
            movimentacoes = self.activity_service.listar_movimentacoes(
                limite=self._paginacao.limit, offset=self._paginacao.offset,
            )
            total = self.activity_service.contar_total()
        printer_ids = [m.printer_id for m in movimentacoes if m.printer_id]
        self._mapa_cache = self.printer_service.mapa_patrimonio(printer_ids) if printer_ids else {}
        self._mov_cache = movimentacoes
        self._paginacao.configurar(total, pagina_atual=self._paginacao.pagina,
                                   itens_por_pagina=self._paginacao.limit)
        self._preencher_tabela(movimentacoes)

    def _preencher_tabela(self, movimentacoes: list[Any]) -> None:
        self.tabela.limpar()
        self.tabela.setRowCount(len(movimentacoes))
        for i, m in enumerate(movimentacoes):
            self.tabela.setItem(i, 0, QTableWidgetItem(formatar_data_hora(m.event_at)))
            patrimonio = self._mapa_cache.get(m.printer_id, m.printer_id[:8] + "...")
            self.tabela.setItem(i, 1, QTableWidgetItem(patrimonio))
            self.tabela.setItem(i, 2, QTableWidgetItem(m.from_location or "-"))
            self.tabela.setItem(i, 3, QTableWidgetItem(m.to_location or "-"))
            self.tabela.setItem(i, 4, QTableWidgetItem(encurtar(m.parts_used, 30)))
            self.tabela.setItem(i, 5, QTableWidgetItem(m.numero_recibo or "-"))
            status = (m.status_atividade or "concluida").lower()
            cor_status = COR_STATUS.get(status, "#94949f")
            self.tabela.definir_badge(i, 6, status.capitalize(), cor_status)
        self.tabela.redimensionar()
        self._atualizar_cards(movimentacoes)

    def _atualizar_cards(self, movimentacoes: list[Any]) -> None:
        total = len(movimentacoes)
        saidas = sum(1 for m in movimentacoes if m.from_location and not m.to_location)
        entradas = sum(1 for m in movimentacoes if m.to_location and not m.from_location)
        pendentes = sum(1 for m in movimentacoes if (m.status_atividade or "").lower() == "pendente")
        self.card_total.atualizar_valor(total)
        self.card_saidas.atualizar_valor(saidas)
        self.card_entradas.atualizar_valor(entradas)
        self.card_pendentes.atualizar_valor(pendentes)

    def _filtrar(self, texto: str) -> None:
        texto = texto.strip()
        self._filtro_transf = texto if texto else None
        self._carregar()

    def _nova(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Nova Transferência")
        dialog.setMinimumSize(680, 580)
        dialog.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(dialog)
        tabs = QTabWidget()
        

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        content = QVBoxLayout(container)
        content.setContentsMargins(20, 16, 20, 16)
        content.setSpacing(14)

        tipo_box, tipo_layout = group_box("Tipo")
        tipo_form = QFormLayout()
        tipo_form.setLabelAlignment(Qt.AlignRight)
        tipo_form.setSpacing(8)

        tipo_combo = QComboBox()
        tipo_combo.addItems(["Impressora Completa", "Apenas Peça(s)"])
        configurar_combo(tipo_combo)
        cmp = tipo_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        tipo_form.addRow("Tipo:", tipo_combo)
        tipo_layout.addLayout(tipo_form)
        content.addWidget(tipo_box)

        equip_box, equip_layout = group_box("Equipamentos")
        equip_form = QFormLayout()
        equip_form.setLabelAlignment(Qt.AlignRight)
        equip_form.setSpacing(8)

        printer_combo = QComboBox()
        printer_combo.setEditable(True)
        configurar_combo(printer_combo)
        cmp = printer_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        printer_combo.setPlaceholderText("Digite o patrimônio")
        for p in self.printer_service.listar_todos():
            printer_combo.addItem(f"{p.patrimonio} - {p.modelo}", p.id)
        equip_form.addRow("Impressora Origem:", printer_combo)

        printer_destino_combo = QComboBox()
        printer_destino_combo.setEditable(True)
        configurar_combo(printer_destino_combo)
        cmp = printer_destino_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        printer_destino_combo.setPlaceholderText("Digite o patrimônio")
        for p in self.printer_service.listar_todos():
            printer_destino_combo.addItem(f"{p.patrimonio} - {p.modelo}", p.id)
        printer_destino_combo.setVisible(False)
        lbl_dest = QLabel("Impressora Destino:")
        lbl_dest.setVisible(False)
        equip_form.addRow(lbl_dest, printer_destino_combo)

        def _toggle_printer_destino(tipo: str) -> None:
            visivel = tipo == "Apenas Peça(s)"
            lbl_dest.setVisible(visivel)
            printer_destino_combo.setVisible(visivel)
        tipo_combo.currentTextChanged.connect(_toggle_printer_destino)

        equip_layout.addLayout(equip_form)
        content.addWidget(equip_box)

        det_box, det_layout = group_box("Detalhes")
        det_form = QFormLayout()
        det_form.setLabelAlignment(Qt.AlignRight)
        det_form.setSpacing(8)

        data_input = QLineEdit(dt.now().strftime("%d/%m/%Y %H:%M"))
        data_input.setStyleSheet(ESTILO_INPUT)
        data_input.textChanged.connect(_criar_mascara_data(data_input))
        det_form.addRow("Data/Hora:", data_input)

        pecas_text = QTextEdit()
        pecas_text.setStyleSheet(ESTILO_INPUT)
        pecas_text.setPlaceholderText("Peças separadas por vírgula")
        pecas_text.setMaximumHeight(70)
        det_form.addRow("Peças:", pecas_text)

        empresas = self.company_service.listar_nomes()

        origem_combo = QComboBox()
        origem_combo.setEditable(True)
        configurar_combo(origem_combo)
        cmp = origem_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        origem_combo.addItems(empresas)
        det_form.addRow("Origem:", origem_combo)

        destino_combo = QComboBox()
        destino_combo.setEditable(True)
        configurar_combo(destino_combo)
        cmp = destino_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        destino_combo.addItems(empresas)
        det_form.addRow("Destino:", destino_combo)

        recibo_input = QLineEdit()
        recibo_input.setStyleSheet(ESTILO_INPUT)
        recibo_input.setPlaceholderText("Número do recibo")
        det_form.addRow("Nº Recibo:", recibo_input)

        estoque_combo = self._criar_estoque_combo()
        det_form.addRow("Peça do Estoque:", estoque_combo)
        estoque_combo.currentIndexChanged.connect(
            lambda idx: self._preencher_pecas_do_estoque(estoque_combo, pecas_text, idx)
        )

        desc_text = QTextEdit()
        desc_text.setStyleSheet(ESTILO_INPUT)
        desc_text.setPlaceholderText("Descrição da transferência")
        desc_text.setMaximumHeight(70)
        det_form.addRow("Descrição:", desc_text)

        det_layout.addLayout(det_form)
        content.addWidget(det_box)

        status_box, status_layout = group_box("Status")
        status_form = QFormLayout()
        status_form.setLabelAlignment(Qt.AlignRight)
        status_form.setSpacing(8)

        status_combo = QComboBox()
        configurar_combo(status_combo)
        cmp = status_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        status_combo.addItems(STATUS_ATIVIDADE_OPCOES)
        status_form.addRow("Status:", status_combo)
        status_layout.addLayout(status_form)
        content.addWidget(status_box)

        content.addStretch()
        scroll.setWidget(container)
        tabs.addTab(scroll, "\U0001f4cb Dados")

        layout.addWidget(tabs)

        btn_salvar = QPushButton("\U0001f4be Salvar")
        btn_salvar.setToolTip("Salvar nova transferência")
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_salvar)
        layout.addLayout(btn_layout)

        saved_id = [None]

        def salvar_nova_silent() -> int | None:
            if saved_id[0] is not None:
                return saved_id[0]
            patrimonio_texto = printer_combo.currentText().split(" - ")[0].strip()
            printer = self.printer_service.buscar_por_patrimonio(patrimonio_texto)
            if not printer:
                QMessageBox.warning(dialog, "Aviso", "Impressora não encontrada. Verifique o patrimônio.")
                return None

            from app.utils.helpers import parse_data
            data_texto = data_input.text().strip()
            event_at = parse_data(data_texto) if data_texto else dt.now()
            parts = pecas_text.toPlainText().strip()
            from_loc = origem_combo.currentText().strip()
            to_loc = destino_combo.currentText().strip()
            recibo = recibo_input.text().strip()
            status = status_combo.currentText()

            try:
                desc_clean = desc_text.toPlainText().strip()
                tipo = tipo_combo.currentText()

                with transacao(self._session):
                    activity = Activity(
                        printer_id=printer.id,
                        kind="MOVIMENTACAO",
                        event_at=event_at,
                        parts_used=parts,
                        from_location=from_loc,
                        to_location=to_loc,
                        notes=desc_clean,
                        numero_recibo=recibo,
                        status_atividade=status,
                    )
                    self._session.add(activity)
                    self._dar_baixa_estoque(parts)

                    if tipo == "Apenas Peça(s)":
                        dest_texto = printer_destino_combo.currentText().split(" - ")[0].strip()
                        if dest_texto:
                            printer_dest = self.printer_service.buscar_por_patrimonio(dest_texto)
                            if printer_dest:
                                notes_dest = f"Recebeu peça da {patrimonio_texto}"
                                if desc_clean:
                                    notes_dest += f" — {desc_clean}"
                                activity_dest = Activity(
                                    printer_id=printer_dest.id,
                                    kind="MOVIMENTACAO",
                                    event_at=event_at,
                                    parts_used=parts,
                                    from_location=from_loc,
                                    to_location=to_loc,
                                    notes=notes_dest,
                                    numero_recibo=recibo,
                                    status_atividade=status,
                                )
                                self._session.add(activity_dest)

                saved_id[0] = activity.id
                return activity.id
            except Exception as e:
                QMessageBox.critical(dialog, "Erro", f"Erro ao salvar:\n{e}")
                return None

        def salvar_nova() -> None:
            if salvar_nova_silent() is not None:
                dialog.accept()

        btn_salvar.clicked.connect(salvar_nova)

        tab_anexos = self._criar_tab_anexos_nova(dialog, tabs, salvar_nova_silent, saved_id)
        tabs.addTab(tab_anexos, "\U0001f4ce Anexos")

        if dialog.exec() == QDialog.Accepted:
            self.recarregar()

    def _detalhes(self, row: int) -> None:
        if row < 0 or row >= len(self._mov_cache):
            return
        mov = self._mov_cache[row]
        printer = self.printer_service.buscar_por_id(mov.printer_id)
        patrimonio = f"{printer.patrimonio} - {printer.modelo}" if printer else mov.printer_id

        tipo = "Apenas Peça(s)" if (mov.notes and "Peças para" in mov.notes) else "Impressora Completa"

        dialog = QDialog(self)
        dialog.setWindowTitle("Transferência")
        dialog.setMinimumSize(650, 500)
        dialog.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(dialog)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        content = QVBoxLayout(container)
        content.setContentsMargins(20, 16, 20, 16)
        content.setSpacing(14)

        equip_box, equip_layout = group_box("Equipamentos")
        equip_form = QFormLayout()
        equip_form.setLabelAlignment(Qt.AlignRight)
        equip_form.setSpacing(8)
        equip_form.addRow(campo_rotulo("Impressora Origem"), campo_readonly(patrimonio))
        if tipo == "Apenas Peça(s)":
            partes = mov.notes.split(" - ", 1) if mov.notes else []
            destino_pat = partes[0].replace("Peças para ", "").strip() if partes and partes[0].startswith("Peças para") else "—"
            equip_form.addRow(campo_rotulo("Impressora Destino"), campo_readonly(destino_pat))
        equip_layout.addLayout(equip_form)
        content.addWidget(equip_box)

        det_box, det_layout = group_box("Detalhes")
        det_form = QFormLayout()
        det_form.setLabelAlignment(Qt.AlignRight)
        det_form.setSpacing(8)
        det_form.addRow(campo_rotulo("Tipo"), campo_readonly(tipo))
        det_form.addRow(campo_rotulo("Data/Hora"), campo_readonly(formatar_data_hora(mov.event_at)))
        det_form.addRow(campo_rotulo("Peças"), campo_readonly(mov.parts_used or "—"))
        det_form.addRow(campo_rotulo("Origem"), campo_readonly(mov.from_location or "—"))
        det_form.addRow(campo_rotulo("Destino"), campo_readonly(mov.to_location or "—"))
        det_form.addRow(campo_rotulo("Nº Recibo"), campo_readonly(mov.numero_recibo or "—"))
        det_form.addRow(campo_rotulo("Status"), campo_readonly(mov.status_atividade or "—"))
        det_layout.addLayout(det_form)
        content.addWidget(det_box)

        if mov.notes:
            obs_box, obs_layout = group_box("Observações")
            obs_layout.addWidget(campo_readonly(mov.notes))
            content.addWidget(obs_box)

        anexos = self._session.query(Attachment).filter_by(
            entity_type="activity", entity_id=mov.id
        ).order_by(Attachment.created_at.desc()).all()
        if anexos:
            anexos_box, anexos_layout = group_box("Anexos")
            for a in anexos:
                btn_anexo = QPushButton(f"\U0001f4ce {a.original_name}")
                btn_anexo.setStyleSheet(
                    "QPushButton { color: #6366f1; font-size: 12px; background: transparent;"
                    " border: none; text-align: left; padding: 2px 0; }"
                    " QPushButton:hover { color: #818cf8; }"
                )
                btn_anexo.setCursor(Qt.PointingHandCursor)
                file_path = a.file_path
                btn_anexo.clicked.connect(lambda checked, fp=file_path: self._abrir_anexo(fp))
                anexos_layout.addWidget(btn_anexo)
            content.addWidget(anexos_box)

        content.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        botoes = QHBoxLayout()
        botoes.setSpacing(10)

        btn_editar = QPushButton("\u270f\ufe0f  Editar")
        btn_editar.setToolTip("Editar esta transferência")
        btn_editar.setStyleSheet(ESTILO_BOTAO_AVISO)
        btn_editar.clicked.connect(lambda: self._abrir_edicao(mov, dialog))

        btn_excluir = QPushButton("\U0001f5d1\ufe0f Excluir")
        btn_excluir.setToolTip("Excluir esta transferência (pode ser desfeito pela Lixeira)")
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_excluir.clicked.connect(lambda: self._confirmar_exclusao(dialog, mov))

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setToolTip("Fechar detalhes")
        btn_fechar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_fechar.clicked.connect(lambda: dialog.accept())

        botoes.addWidget(btn_editar)
        botoes.addWidget(btn_excluir)
        botoes.addStretch()
        botoes.addWidget(btn_fechar)
        layout.addLayout(botoes)

        dialog.exec()

    def _abrir_edicao(self, mov: Any, parent_dialog: QDialog | None = None) -> None:
        printer = self.printer_service.buscar_por_id(mov.printer_id)
        patrimonio = f"{printer.patrimonio} - {printer.modelo}" if printer else mov.printer_id

        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Transferência")
        dialog.setMinimumSize(680, 580)
        dialog.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(dialog)
        tabs = QTabWidget()
        orig = {
            "printer_id": mov.printer_id,
            "parts_used": mov.parts_used,
            "from_location": mov.from_location,
            "to_location": mov.to_location,
            "notes": mov.notes,
            "numero_recibo": mov.numero_recibo,
            "status_atividade": mov.status_atividade,
        }

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        content = QVBoxLayout(container)
        content.setContentsMargins(20, 16, 20, 16)
        content.setSpacing(14)

        equip_box, equip_layout = group_box("Equipamentos")
        equip_form = QFormLayout()
        equip_form.setLabelAlignment(Qt.AlignRight)
        equip_form.setSpacing(8)

        lbl_printer = QLabel(patrimonio)
        lbl_printer.setStyleSheet("color: #c0c0d0; font-size: 13px; background: transparent;")
        equip_form.addRow("Impressora Origem:", lbl_printer)

        printer_destino_edit_combo = QComboBox()
        printer_destino_edit_combo.setEditable(True)
        configurar_combo(printer_destino_edit_combo)
        cmp = printer_destino_edit_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        printer_destino_edit_combo.setPlaceholderText("Digite o patrimônio")
        for p in self.printer_service.listar_todos():
            printer_destino_edit_combo.addItem(f"{p.patrimonio} - {p.modelo}", p.id)
        if mov.notes and mov.notes.startswith("Peças para"):
            partes = mov.notes.split(" - ", 1)
            destino_pat = partes[0].replace("Peças para ", "").strip()
            idx = printer_destino_edit_combo.findText(destino_pat)
            if idx >= 0:
                printer_destino_edit_combo.setCurrentIndex(idx)
            else:
                printer_destino_edit_combo.setCurrentText(destino_pat)
        lbl_dest_edit = QLabel("Impressora Destino:")
        equip_form.addRow(lbl_dest_edit, printer_destino_edit_combo)
        equip_layout.addLayout(equip_form)
        content.addWidget(equip_box)

        tipo_box, tipo_layout = group_box("Tipo")
        tipo_form = QFormLayout()
        tipo_form.setLabelAlignment(Qt.AlignRight)
        tipo_form.setSpacing(8)

        tipo_edit_combo = QComboBox()
        configurar_combo(tipo_edit_combo)
        cmp = tipo_edit_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        tipo_edit_combo.addItems(["Impressora Completa", "Apenas Peça(s)"])
        if mov.notes and mov.notes.startswith("Peças para"):
            tipo_edit_combo.setCurrentText("Apenas Peça(s)")
        tipo_form.addRow("Tipo:", tipo_edit_combo)
        tipo_layout.addLayout(tipo_form)
        content.addWidget(tipo_box)

        is_pecas = tipo_edit_combo.currentText() == "Apenas Peça(s)"
        lbl_dest_edit.setVisible(is_pecas)
        printer_destino_edit_combo.setVisible(is_pecas)

        def _toggle_printer_destino_edit(tipo: str) -> None:
            visivel = tipo == "Apenas Peça(s)"
            lbl_dest_edit.setVisible(visivel)
            printer_destino_edit_combo.setVisible(visivel)
        tipo_edit_combo.currentTextChanged.connect(_toggle_printer_destino_edit)

        det_box, det_layout = group_box("Detalhes")
        det_form = QFormLayout()
        det_form.setLabelAlignment(Qt.AlignRight)
        det_form.setSpacing(8)

        data_input = QLineEdit(formatar_data_hora(mov.event_at))
        data_input.setStyleSheet(ESTILO_INPUT)
        data_input.textChanged.connect(_criar_mascara_data(data_input))
        det_form.addRow("Data/Hora:", data_input)

        pecas_text = QTextEdit()
        pecas_text.setStyleSheet(ESTILO_INPUT)
        pecas_text.setText(mov.parts_used or "")
        pecas_text.setMaximumHeight(70)
        det_form.addRow("Peças:", pecas_text)

        empresas = self.company_service.listar_nomes()

        origem_combo = QComboBox()
        origem_combo.setEditable(True)
        configurar_combo(origem_combo)
        cmp = origem_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        origem_combo.addItems(empresas)
        if mov.from_location:
            idx = origem_combo.findText(mov.from_location)
            if idx >= 0:
                origem_combo.setCurrentIndex(idx)
            else:
                origem_combo.setEditText(mov.from_location)
        det_form.addRow("Origem:", origem_combo)

        destino_combo = QComboBox()
        destino_combo.setEditable(True)
        configurar_combo(destino_combo)
        cmp = destino_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        destino_combo.addItems(empresas)
        if mov.to_location:
            idx = destino_combo.findText(mov.to_location)
            if idx >= 0:
                destino_combo.setCurrentIndex(idx)
            else:
                destino_combo.setEditText(mov.to_location)
        det_form.addRow("Destino:", destino_combo)

        recibo_input = QLineEdit()
        recibo_input.setStyleSheet(ESTILO_INPUT)
        recibo_input.setText(mov.numero_recibo or "")
        det_form.addRow("Nº Recibo:", recibo_input)

        estoque_edit_combo = self._criar_estoque_combo()
        det_form.addRow("Peça do Estoque:", estoque_edit_combo)
        estoque_edit_combo.currentIndexChanged.connect(
            lambda idx: self._preencher_pecas_do_estoque(estoque_edit_combo, pecas_text, idx)
        )

        def _strip_prefix(txt: str) -> str:
            import re
            return re.sub(r'^(Peças para \S+|Recebeu peça da \S+)\s*[—\-]?\s*', '', txt).strip()

        desc_text = QTextEdit()
        desc_text.setStyleSheet(ESTILO_INPUT)
        desc_text.setText(_strip_prefix(mov.notes or ""))
        desc_text.setMaximumHeight(70)
        det_form.addRow("Descrição:", desc_text)

        det_layout.addLayout(det_form)
        content.addWidget(det_box)

        status_box, status_layout = group_box("Status")
        status_form = QFormLayout()
        status_form.setLabelAlignment(Qt.AlignRight)
        status_form.setSpacing(8)

        status_combo = QComboBox()
        configurar_combo(status_combo)
        cmp = status_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        status_combo.addItems(STATUS_ATIVIDADE_OPCOES)
        sidx = status_combo.findText(mov.status_atividade or "Concluida", Qt.MatchFixedString)
        if sidx >= 0:
            status_combo.setCurrentIndex(sidx)
        status_form.addRow("Status:", status_combo)
        status_layout.addLayout(status_form)
        content.addWidget(status_box)

        content.addStretch()
        scroll.setWidget(container)
        tabs.addTab(scroll, "\U0001f4cb Dados")

        def salvar_edicao() -> None:
            from app.utils.helpers import parse_data
            data_texto = data_input.text().strip()
            desc_clean = desc_text.toPlainText().strip()
            parts = pecas_text.toPlainText().strip()
            from_loc = origem_combo.currentText().strip()
            to_loc = destino_combo.currentText().strip()
            recibo = recibo_input.text().strip()
            status = status_combo.currentText()
            novos = {
                "parts_used": parts,
                "from_location": from_loc,
                "to_location": to_loc,
                "notes": desc_clean,
                "numero_recibo": recibo,
                "status_atividade": status,
            }
            if data_texto:
                parsed = parse_data(data_texto)
                if parsed:
                    mov.event_at = parsed
            if novos == orig:
                return
            try:
                with transacao(self._session):
                    for chave, valor in novos.items():
                        setattr(mov, chave, valor)
                    self._dar_baixa_estoque(parts)

                    if tipo_edit_combo.currentText() == "Apenas Peça(s)":
                        dest_texto = printer_destino_edit_combo.currentText().split(" - ")[0].strip()
                        if dest_texto:
                            printer_dest = self.printer_service.buscar_por_patrimonio(dest_texto)
                            if printer_dest:
                                src_pat = printer.patrimonio if printer else str(orig['printer_id'])
                                existing = self._session.query(Activity).filter(
                                    Activity.printer_id == printer_dest.id,
                                    Activity.kind == "MOVIMENTACAO",
                                    Activity.notes.like(f"Recebeu peça da {src_pat}%"),
                                ).first()
                                notes_dest = f"Recebeu peça da {src_pat}"
                                if desc_clean:
                                    notes_dest += f" — {desc_clean}"
                                if existing:
                                    existing.notes = notes_dest
                                    existing.parts_used = parts
                                    existing.from_location = from_loc
                                    existing.to_location = to_loc
                                    existing.numero_recibo = recibo
                                else:
                                    event_at = parse_data(data_texto) if data_texto else mov.event_at
                                    activity_dest = Activity(
                                        printer_id=printer_dest.id,
                                        kind="MOVIMENTACAO",
                                        event_at=event_at,
                                        parts_used=parts,
                                        from_location=from_loc,
                                        to_location=to_loc,
                                        notes=notes_dest,
                                        numero_recibo=recibo,
                                        status_atividade=status,
                                    )
                                    self._session.add(activity_dest)

                orig.update(novos)
                QMessageBox.information(dialog, "Sucesso", "Alterações salvas!")
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Erro", f"Erro ao salvar:\n{e}")

        tab_anexos = self._criar_tab_anexos("activity", mov.id, dialog, None, tabs)
        tabs.addTab(tab_anexos, "\U0001f4ce Anexos")

        layout.addWidget(tabs)

        botoes = QHBoxLayout()
        botoes.setSpacing(10)

        btn_salvar = QPushButton("\U0001f4be Salvar")
        btn_salvar.setToolTip("Salvar alterações da transferência")
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_salvar.clicked.connect(salvar_edicao)
        botoes.addWidget(btn_salvar)

        btn_excluir = QPushButton("\U0001f5d1\ufe0f Excluir")
        btn_excluir.setToolTip("Excluir esta transferência (pode ser desfeito pela Lixeira)")
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_excluir.clicked.connect(lambda: self._confirmar_exclusao(dialog, mov))
        botoes.addWidget(btn_excluir)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setToolTip("Descartar alterações e fechar")
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_cancelar.clicked.connect(lambda: dialog.reject())
        botoes.addWidget(btn_cancelar)

        layout.addLayout(botoes)

        alterado = [False]

        def marcar_alterado() -> None:
            alterado[0] = True

        pecas_text.textChanged.connect(marcar_alterado)
        origem_combo.currentTextChanged.connect(marcar_alterado)
        destino_combo.currentTextChanged.connect(marcar_alterado)
        recibo_input.textChanged.connect(marcar_alterado)
        desc_text.textChanged.connect(marcar_alterado)
        status_combo.currentTextChanged.connect(marcar_alterado)

        original_close = dialog.closeEvent

        def close_event(event: Any) -> None:
            if alterado[0]:
                resposta = QMessageBox.question(
                    dialog, "Alterações não salvas",
                    "Deseja salvar as alterações antes de fechar?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Yes,
                )
                if resposta == QMessageBox.Yes:
                    salvar_edicao()
                    event.accept()
                elif resposta == QMessageBox.No:
                    self._session.rollback()
                    event.accept()
                else:
                    event.ignore()
            else:
                event.accept()

        dialog.closeEvent = close_event

        if dialog.exec() == QDialog.Accepted:
            self.recarregar()
            if parent_dialog is not None:
                parent_dialog.accept()

    def _confirmar_exclusao(self, dialog: QDialog, mov: Any) -> None:
        if ConfirmacaoDigitarDialog.confirmar(
            "Confirmar Exclusão",
            "Tem certeza que deseja excluir esta transferência?",
            dialog,
        ):
            try:
                if self.transfer_service:
                    self.transfer_service.excluir(mov)
                    ToastManager.mostrar(
                        "Transferência excluída.",
                        "aviso", duracao=8000,
                        acao=("Desfazer", lambda o=mov, svc=self.transfer_service, pag=self: (svc.restaurar(o), pag.recarregar())),
                    )
                else:
                    mov.deleted_at = dt.utcnow()
                    safe_commit(self._session)
                dialog.accept()
            except Exception as e:
                self._session.rollback()
                QMessageBox.critical(dialog, "Erro", f"Erro ao excluir:\n{e}")

    def _criar_tab_anexos_nova(self, dialog: QDialog, tabs: QTabWidget, fn_salvar_silent: Callable[[], int | None], saved_id: list[int | None]) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        if saved_id[0] is not None:
            return self._criar_tab_anexos("activity", saved_id[0], dialog, None, tabs)

        lbl_aviso = QLabel("Area para anexar seus arquivos.")
        lbl_aviso.setStyleSheet("color: #94949f; font-size: 13px;")
        lbl_aviso.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_aviso)

        btn_add = QPushButton("\U0001f4ce Adicionar Anexo")
        btn_add.setToolTip("Adicionar arquivo anexo à transferência")
        btn_add.setStyleSheet(ESTILO_BOTAO_AVISO)

        def _salvar_e_anexar() -> None:  
            eid = fn_salvar_silent()
            if eid is None:
                return
            self._anexar_arquivo("activity", eid, dialog, None, tabs)

        btn_add.clicked.connect(_salvar_e_anexar)
        layout.addWidget(btn_add, alignment=Qt.AlignCenter)
        return tab

    def _criar_tab_anexos(self, entity_type: str, entity_id: int, dialog: QDialog, callback_salvar: Callable[[], None] | None, tabs: QTabWidget) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        tabela_anexos = QTableWidget()
        tabela_anexos.setColumnCount(5)
        tabela_anexos.setHorizontalHeaderLabels(["Arquivo", "Categoria", "Data", "Abrir", "Remover"])
        tabela_anexos.setStyleSheet(ESTILO_TABELA_SIMPLES)
        tabela_anexos.setSelectionBehavior(QAbstractItemView.SelectRows)
        tabela_anexos.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tabela_anexos.verticalHeader().setVisible(False)
        tabela_anexos.setAlternatingRowColors(True)

        anexos = self._session.query(Attachment).filter_by(
            entity_type=entity_type, entity_id=entity_id
        ).order_by(Attachment.created_at.desc()).all()

        tabela_anexos.setRowCount(len(anexos))
        for i, a in enumerate(anexos):
            tabela_anexos.setItem(i, 0, QTableWidgetItem(a.original_name))
            tabela_anexos.setItem(i, 1, QTableWidgetItem(a.categoria or "-"))
            tabela_anexos.setItem(i, 2, QTableWidgetItem(formatar_data_hora(a.created_at)))
            btn_abrir = QPushButton("\U0001f4c2 Abrir")
            btn_abrir.setToolTip("Abrir arquivo anexo")
            btn_abrir.setStyleSheet("""
                QPushButton {
                    background-color: #1f2937; color: #94a3b8;
                    border: none; border-radius: 4px;
                    padding: 4px 12px; font-size: 11px;
                }
                QPushButton:hover { background-color: #374151; color: #e2e8f0; }
            """)
            file_path = a.file_path
            btn_abrir.clicked.connect(lambda checked, fp=file_path: self._abrir_anexo(fp))
            tabela_anexos.setCellWidget(i, 3, btn_abrir)

            btn_remover = QPushButton("\u274c")
            btn_remover.setToolTip("Remover este anexo")
            btn_remover.setStyleSheet("""
                QPushButton {
                    background-color: transparent; color: #f87171;
                    border: none; border-radius: 4px;
                    padding: 4px 8px; font-size: 13px;
                }
                QPushButton:hover { background-color: rgba(248,113,113,0.15); }
            """)
            anexo_id = a.id
            btn_remover.clicked.connect(
                lambda checked, aid=anexo_id: self._remover_anexo(
                    aid, entity_type, entity_id, dialog, callback_salvar, tabs
                )
            )
            tabela_anexos.setCellWidget(i, 4, btn_remover)

        tabela_anexos.verticalHeader().setDefaultSectionSize(44)
        for i in range(tabela_anexos.columnCount()):
            tabela_anexos.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        layout.addWidget(tabela_anexos)

        botoes_anexos = QHBoxLayout()
        btn_adicionar = QPushButton("\U0001f4ce Adicionar Anexo")
        btn_adicionar.setToolTip("Adicionar arquivo anexo à transferência")
        btn_adicionar.setStyleSheet(ESTILO_BOTAO_AVISO)

        btn_adicionar.clicked.connect(
            lambda: self._anexar_arquivo(entity_type, entity_id, dialog, callback_salvar, tabs)
        )
        botoes_anexos.addWidget(btn_adicionar)

        if callback_salvar:
            btn_salvar_tab = QPushButton("\U0001f4be Salvar")
            btn_salvar_tab.setToolTip("Salvar anexos")
            btn_salvar_tab.setStyleSheet(ESTILO_BOTAO_SUCESSO)
            btn_salvar_tab.clicked.connect(callback_salvar)
            botoes_anexos.addWidget(btn_salvar_tab)

        layout.addLayout(botoes_anexos)
        return tab

    def _remover_anexo(self, anexo_id: int, entity_type: str, entity_id: int, dialog: QDialog, callback_salvar: Callable[[], None] | None, tabs: QTabWidget) -> None:
        if not ConfirmacaoDigitarDialog.confirmar(
            "Remover Anexo",
            "Deseja realmente remover este anexo?\n\nO arquivo será excluído permanentemente.",
            dialog,
        ):
            return
        try:
            anexo = self._session.query(Attachment).filter_by(id=anexo_id).first()
            if anexo:
                if os.path.exists(anexo.file_path):
                    os.remove(anexo.file_path)
                self._session.delete(anexo)
                safe_commit(self._session)
            idx = tabs.currentIndex()
            tabs.removeTab(1)
            nova_tab = self._criar_tab_anexos(entity_type, entity_id, dialog, callback_salvar, tabs)
            tabs.addTab(nova_tab, "\U0001f4ce Anexos")
            tabs.setCurrentIndex(idx)
        except Exception as e:
            self._session.rollback()
            QMessageBox.critical(dialog, "Erro", f"Erro ao remover anexo:\n{e}")

    def _anexar_arquivo(self, entity_type: str, entity_id: int, dialog: QDialog, callback_salvar: Callable[[], None] | None, tabs: QTabWidget) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            dialog, "Selecionar Arquivo",
            "",
            "Todos os arquivos (*.*)",
        )
        if not file_path:
            return

        try:
            original_name = os.path.basename(file_path)
            timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
            safe_name = f"{timestamp}_{original_name}"
            ANEXOS_DIR.mkdir(parents=True, exist_ok=True)
            dest_path = str(ANEXOS_DIR / safe_name)

            shutil.copy2(file_path, dest_path)

            ext = os.path.splitext(original_name)[1].lower()
            mime_map = {
                ".pdf": "application/pdf",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".doc": "application/msword",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".xls": "application/vnd.ms-excel",
                ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".txt": "text/plain",
            }
            mime_type = mime_map.get(ext, "application/octet-stream")

            attachment = Attachment(
                entity_type=entity_type,
                entity_id=entity_id,
                filename=safe_name,
                original_name=original_name,
                file_path=dest_path,
                mime_type=mime_type,
                size_bytes=os.path.getsize(file_path),
                categoria="recibo",
            )
            self._session.add(attachment)
            safe_commit(self._session)

            idx = tabs.currentIndex()
            tabs.removeTab(1)
            nova_tab = self._criar_tab_anexos(entity_type, entity_id, dialog, callback_salvar, tabs)
            tabs.addTab(nova_tab, "\U0001f4ce Anexos")
            tabs.setCurrentIndex(idx)
        except Exception as e:
            self._session.rollback()
            QMessageBox.critical(dialog, "Erro", f"Erro ao anexar arquivo:\n{e}")

    def _abrir_anexo(self, file_path: str) -> None:
        if os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Aviso", f"Não foi possível abrir o arquivo:\n{e}")
        else:
            QMessageBox.warning(self, "Aviso", "Arquivo não encontrado:\n" + file_path)

    def _criar_estoque_combo(self) -> QComboBox:
        combo = QComboBox()
        configurar_combo(combo)
        cmp = combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        combo.addItem("-- Nenhuma --", None)
        for p in self.part_service.listar_todas():
            if p.quantidade_estoque > 0:
                combo.addItem(f"{p.nome} ({p.quantidade_estoque} un.)", p.id)
        return combo

    def _preencher_pecas_do_estoque(self, combo: QComboBox, pecas_widget: QTextEdit, idx: int) -> None:
        if idx <= 0:
            return
        try:
            part_id = combo.currentData()
            if part_id is None:
                return
            part = self.part_service.buscar_por_id(part_id)
            if part:
                atual = pecas_widget.toPlainText().strip()
                nova = f"{part.nome}" if not atual else f"{atual}, {part.nome}"
                pecas_widget.setPlainText(nova)
        except RuntimeError:
            pass

    def _dar_baixa_estoque(self, pecas_texto: str) -> None:
        if not pecas_texto:
            return
        nome_peca = pecas_texto.split(",")[0].strip()
        with tratar_erro("dar baixa no estoque"):
            part = self.part_service.buscar_por_nome(nome_peca)
            if part and part.quantidade_estoque > 0:
                self.part_service.atualizar(part, quantidade_estoque=part.quantidade_estoque - 1)
