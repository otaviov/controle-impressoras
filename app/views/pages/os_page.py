from __future__ import annotations

import json
from datetime import datetime as dt
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models import Part
from app.services.part_service import PartService
from app.utils.ui_helpers import tratar_erro
from app.utils.helpers import formatar_data_hora
from db import transacao
from app.views.styles.theme import (
    ESTILO_BOTAO_AVISO,
    ESTILO_BOTAO_ERRO,
    ESTILO_BOTAO_FECHAR,
    ESTILO_BOTAO_PRIMARIO,
    ESTILO_BOTAO_SECUNDARIO,
    ESTILO_BOTAO_SUCESSO,
    ESTILO_COMBO,
    ESTILO_DIALOG,
    ESTILO_INPUT,
    ESTILO_SUBTITULO,
    ESTILO_TITULO_PAGINA,
    configurar_combo,
    group_box,
    input_label,
    campo_rotulo,
    campo_readonly,
)
from app.views.widgets import ToastManager
from app.views.widgets.card_widget import CardMiniClicavel
from app.views.widgets.confirm_dialog import ConfirmacaoDigitarDialog
from app.views.widgets.pagination import PaginacaoWidget
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


class OSPage(QWidget):
    session: Any
    printer_service: Any
    activity_service: Any
    company_service: Any
    technician_service: Any
    part_service: PartService
    _atividades: list[Any]
    _filtro_tipo_atual: str | None
    _filtro_status_atual: str | None
    _filtro_busca_atual: str | None
    search: SearchBar
    btn_nova: QPushButton
    btn_manut: QPushButton
    btn_mov: QPushButton
    btn_todas: QPushButton
    btn_atualizar: QPushButton
    card_total: CardMiniClicavel
    card_andamento: CardMiniClicavel
    card_pendentes: CardMiniClicavel
    card_concluidas: CardMiniClicavel
    tabela: TabelaPadrao
    _paginacao: PaginacaoWidget

    def __init__(self, session: Any, printer_service: Any, activity_service: Any, company_service: Any, technician_service: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        self.printer_service = printer_service
        self.activity_service = activity_service
        self.company_service = company_service
        self.technician_service = technician_service

        self._atividades = []
        self._filtro_tipo_atual = None
        self.part_service = PartService(session)

        self._setup_ui()
        self.recarregar()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Header ──────────────────────────────────────
        header = QHBoxLayout()
        titulo_col = QVBoxLayout()
        titulo_col.setSpacing(2)
        titulo = QLabel("Ordens de Serviço")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        titulo_col.addWidget(titulo)
        subtitulo = QLabel("Gerencie as atividades e ordens de serviço")
        subtitulo.setStyleSheet(ESTILO_SUBTITULO)
        titulo_col.addWidget(subtitulo)
        header.addLayout(titulo_col)
        header.addStretch()

        self.btn_nova = QPushButton("Nova OS")
        self.btn_nova.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
        self.btn_nova.setToolTip("Criar nova ordem de serviço")
        self.btn_nova.clicked.connect(self._nova)
        header.addWidget(self.btn_nova)

        self.btn_manut = QPushButton("Manutenções")
        self.btn_manut.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        self.btn_manut.setToolTip("Filtrar apenas manutenções")
        self.btn_manut.clicked.connect(lambda: self._filtrar_tipo("MANUTENCAO"))
        header.addWidget(self.btn_manut)

        self.btn_mov = QPushButton("Movimentações")
        self.btn_mov.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        self.btn_mov.setToolTip("Filtrar apenas movimentações")
        self.btn_mov.clicked.connect(lambda: self._filtrar_tipo("MOVIMENTACAO"))
        header.addWidget(self.btn_mov)

        self.btn_todas = QPushButton("Todas")
        self.btn_todas.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        self.btn_todas.setToolTip("Mostrar todas as ordens de serviço")
        self.btn_todas.clicked.connect(lambda: self._filtrar_tipo("TODAS"))
        header.addWidget(self.btn_todas)

        self.btn_atualizar = QPushButton("Atualizar")
        self.btn_atualizar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        self.btn_atualizar.setToolTip("Recarregar lista de ordens de serviço")
        self.btn_atualizar.clicked.connect(self.recarregar)
        header.addWidget(self.btn_atualizar)

        layout.addLayout(header)

        self.search = SearchBar(placeholder="Buscar por patrimônio, descrição...", glass=True)
        self.search.textChanged().connect(self._filtrar_busca)
        layout.addWidget(self.search)

        cards = QHBoxLayout()
        cards.setSpacing(12)

        self.card_total = CardMiniClicavel("\U0001f4ca", "Total", "0", "#6366f1",
                                           ao_clicar=lambda: self._filtrar_tipo("TODAS"))
        cards.addWidget(self.card_total)

        self.card_andamento = CardMiniClicavel("\U0001f504", "Em Andamento", "0", "#3b82f6",
                                                ao_clicar=lambda: self._filtrar_status("Em Andamento"))
        cards.addWidget(self.card_andamento)

        self.card_pendentes = CardMiniClicavel("\u23f3", "Pendentes", "0", "#f59e0b",
                                                ao_clicar=lambda: self._filtrar_status("Pendente"))
        cards.addWidget(self.card_pendentes)

        self.card_concluidas = CardMiniClicavel("\u2705", "Concluídas", "0", "#10b981",
                                                 ao_clicar=lambda: self._filtrar_status("Concluida"))
        cards.addWidget(self.card_concluidas)

        layout.addLayout(cards)

        self.tabela = TabelaPadrao(["Data/Hora", "Patrimônio", "Tipo", "Descrição", "Peças", "Origem", "Destino", "Técnico"])
        self.tabela.cellDoubleClicked.connect(self._detalhes)
        layout.addWidget(self.tabela)

        self._paginacao = PaginacaoWidget()
        self._paginacao.pagina_alterada.connect(lambda p: self._carregar())
        layout.addWidget(self._paginacao)

        self._filtro_status_atual = None
        self._filtro_busca_atual = None

    def recarregar(self, filtro_tipo: str | None = None) -> None:
        if filtro_tipo:
            self._filtro_tipo_atual = filtro_tipo
        self._filtro_status_atual = None
        self._filtro_busca_atual = None
        self._carregar()

    def _carregar(self) -> None:
        if self._filtro_status_atual:
            atividades = self.activity_service.listar_por_status(
                self._filtro_status_atual,
                limite=self._paginacao.limit, offset=self._paginacao.offset,
            )
            total = self.activity_service.contar_por_status(self._filtro_status_atual)
        elif self._filtro_busca_atual:
            atividades = self.activity_service.buscar_por_filtro_busca(
                self._filtro_busca_atual,
                limite=self._paginacao.limit, offset=self._paginacao.offset,
            )
            total = len(atividades)
        else:
            atividades = self.activity_service.listar(
                filtro_tipo=self._filtro_tipo_atual,
                limite=self._paginacao.limit, offset=self._paginacao.offset,
            )
            total = self.activity_service.contar_total()
        self._atividades = atividades
        self._paginacao.configurar(total, pagina_atual=self._paginacao.pagina,
                                   itens_por_pagina=self._paginacao.limit)
        self._preencher_tabela(atividades)
        self._atualizar_cards()

    def _preencher_tabela(self, atividades: list[Any]) -> None:
        self.tabela.limpar()
        if not atividades:
            return

        printer_ids = list({a.printer_id for a in atividades if a.printer_id})
        mapa_pat = self.printer_service.mapa_patrimonio(printer_ids)

        self.tabela.setRowCount(len(atividades))
        for row, atv in enumerate(atividades):
            patrimonio = mapa_pat.get(atv.printer_id, atv.printer_id[:8] if atv.printer_id else "-")
            cor_tipo = "#f59e0b" if atv.kind == "MANUTENCAO" else "#6366f1"

            data_item = QTableWidgetItem(formatar_data_hora(atv.event_at))
            data_item.setTextAlignment(Qt.AlignCenter)

            pat_item = QTableWidgetItem(patrimonio)
            pat_item.setTextAlignment(Qt.AlignCenter)

            cor_kind = "#f59e0b" if atv.kind == "MANUTENCAO" else "#6366f1"
            self.tabela.definir_badge(row, 2, atv.kind or "-", cor_kind)

            desc_item = QTableWidgetItem(atv.notes or "-")

            pecas_item = QTableWidgetItem(atv.parts_used or "-")

            orig_item = QTableWidgetItem(atv.from_location or "-")
            orig_item.setTextAlignment(Qt.AlignCenter)

            dest_item = QTableWidgetItem(atv.to_location or "-")
            dest_item.setTextAlignment(Qt.AlignCenter)

            nome_tecnico = "-"
            if atv.tecnico_id and self.technician_service:
                tec = self.technician_service.buscar_por_id(atv.tecnico_id)
                if tec:
                    nome_tecnico = tec.nome_exibicao
            tecnico_item = QTableWidgetItem(nome_tecnico)
            tecnico_item.setTextAlignment(Qt.AlignCenter)

            self.tabela.setItem(row, 0, data_item)
            self.tabela.setItem(row, 1, pat_item)
            self.tabela.setItem(row, 3, desc_item)
            self.tabela.setItem(row, 4, pecas_item)
            self.tabela.setItem(row, 5, orig_item)
            self.tabela.setItem(row, 6, dest_item)
            self.tabela.setItem(row, 7, tecnico_item)

        self.tabela.redimensionar()

    def _filtrar_tipo(self, tipo: str) -> None:
        self.recarregar(filtro_tipo=tipo)

    def _filtrar_status(self, status: str) -> None:
        self._filtro_status_atual = status
        self._filtro_busca_atual = None
        self._carregar()

    def _filtrar_busca(self, texto: str) -> None:
        self._filtro_status_atual = None
        self._filtro_busca_atual = texto.strip() if texto.strip() else None
        self._carregar()

    def _atualizar_cards(self) -> None:
        total = self.activity_service.contar_total()
        andamento = self.activity_service.contar_por_status("Em Andamento")
        pendentes = self.activity_service.contar_por_status("Pendente")
        concluidas = self.activity_service.contar_por_status("Concluida")
        self.card_total.atualizar_valor(total)
        self.card_andamento.atualizar_valor(andamento)
        self.card_pendentes.atualizar_valor(pendentes)
        self.card_concluidas.atualizar_valor(concluidas)

    def _nova(self) -> None:
        dialog, campos = self._criar_form_dialog("Nova OS")
        if dialog.exec() != QDialog.Accepted:
            return

        patrimonio = campos["printer"].currentText().strip()
        if not patrimonio:
            QMessageBox.warning(self, "Aviso", "Selecione uma impressora.")
            return

        printer = self.printer_service.buscar_por_patrimonio(patrimonio)
        if not printer:
            QMessageBox.warning(self, "Aviso", f"Impressora '{patrimonio}' não encontrada.")
            return

        kind = campos["tipo"].currentText()
        event_at = campos["data"].dateTime().toPython()
        notes = campos["descricao"].toPlainText().strip()
        parts_used = campos["pecas"].toPlainText().strip()
        sintoma_relatado = campos["sintoma"].toPlainText().strip()
        diagnostico_tecnico = campos["diagnostico"].toPlainText().strip()
        solucao_aplicada = campos["solucao"].toPlainText().strip()
        from_location = campos["origem"].currentText().strip()
        to_location = campos["destino"].currentText().strip()
        status_atividade = campos["status"].currentText()

        from_company_id = self._resolver_empresa(from_location)
        to_company_id = self._resolver_empresa(to_location)
        tecnico_id = self._resolver_tecnico(campos["tecnico"].currentText().strip())

        inicio_qdt = campos["inicio"].dateTime()
        fim_qdt = campos["fim"].dateTime()
        inicio_atendimento = inicio_qdt.toPython() if inicio_qdt.isValid() else None
        fim_atendimento = fim_qdt.toPython() if fim_qdt.isValid() else None

        tbl = campos.get("checklist")
        procedimentos = ""
        if tbl:
            dados = []
            for r in range(tbl.rowCount()):
                chk = tbl.item(r, 0)
                nome = tbl.item(r, 1)
                if nome and nome.text().strip():
                    dados.append({"nome": nome.text().strip(), "feito": bool(chk and chk.checkState() == Qt.Checked)})
            procedimentos = json.dumps(dados, ensure_ascii=False)

        try:
            with transacao(self.session):
                atividade = self.activity_service.criar(
                    printer_id=printer.id,
                    kind=kind,
                    notes=notes,
                    parts_used=parts_used,
                    sintoma_relatado=sintoma_relatado,
                    diagnostico_tecnico=diagnostico_tecnico,
                    solucao_aplicada=solucao_aplicada,
                    inicio_atendimento=inicio_atendimento,
                    fim_atendimento=fim_atendimento,
                    from_location=from_location,
                    to_location=to_location,
                    status_atividade=status_atividade,
                    event_at=event_at,
                    tecnico_id=tecnico_id,
                    procedimentos=procedimentos,
                )
                self._dar_baixa_estoque(parts_used)
                self.activity_service.atualizar(
                    atividade,
                    from_company_id=from_company_id,
                    to_company_id=to_company_id,
                )
            self.recarregar()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao criar OS: {e}")

    def editar_atividade_por_id(self, activity_id: int) -> None:
        atividade = self.activity_service.buscar_por_id(activity_id)
        if not atividade:
            return
        self._atividades = [atividade]
        self._preencher_tabela(self._atividades)
        self._abrir_edicao(atividade)

    def _concluir_os_dialog(self, atividade: Any) -> None:
        printer = self.printer_service.buscar_por_id(atividade.printer_id)
        printer_str = f"{printer.patrimonio} - {printer.modelo}" if printer else "-"

        dialog = QDialog(self)
        dialog.setWindowTitle("Concluir OS")
        dialog.setMinimumSize(500, 480)
        dialog.setStyleSheet(ESTILO_DIALOG)

        root = QVBoxLayout(dialog)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        equip_box, equip_layout = group_box("Equipamento")
        ef = QFormLayout()
        ef.setSpacing(8)
        ef.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ef.addRow(campo_rotulo("Impressora"), campo_readonly(printer_str))
        ef.addRow(campo_rotulo("Tipo"), campo_readonly(atividade.kind or "-"))
        if atividade.tecnico_id and self.technician_service:
            tec = self.technician_service.buscar_por_id(atividade.tecnico_id)
            ef.addRow(campo_rotulo("Técnico"), campo_readonly(tec.nome_exibicao if tec else "-"))
        equip_layout.addLayout(ef)
        layout.addWidget(equip_box)

        concluir_box, concluir_layout = group_box("Finalização")

        edt_solucao = QTextEdit()
        edt_solucao.setStyleSheet(ESTILO_INPUT)
        edt_solucao.setMaximumHeight(80)
        edt_solucao.setPlainText(atividade.solucao_aplicada or "")

        edt_fim = QDateTimeEdit()
        edt_fim.setCalendarPopup(True)
        edt_fim.setDisplayFormat("dd/MM/yyyy HH:mm")
        edt_fim.setStyleSheet(ESTILO_INPUT)
        edt_fim.setDateTime(QDateTime.currentDateTime())

        edt_pecas = QTextEdit()
        edt_pecas.setStyleSheet(ESTILO_INPUT)
        edt_pecas.setMaximumHeight(60)
        edt_pecas.setPlainText(atividade.parts_used or "")

        estoque_combo = QComboBox()
        estoque_combo.setEditable(True)
        configurar_combo(estoque_combo)
        cmp = estoque_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        estoque_combo.addItem("-- Nenhuma --", None)
        for p in self.part_service.listar_todas():
            if p.quantidade_estoque > 0:
                estoque_combo.addItem(f"{p.nome} ({p.quantidade_estoque} un.)", p.id)

        def _add_peca():
            idx = estoque_combo.currentIndex()
            if idx <= 0:
                return
            pid = estoque_combo.currentData()
            if pid is None:
                return
            part = self.part_service.buscar_por_id(pid)
            if part:
                atual = edt_pecas.toPlainText().strip()
                edt_pecas.setPlainText(f"{part.nome}" if not atual else f"{atual}, {part.nome}")
        estoque_combo.currentIndexChanged.connect(lambda i: _add_peca() if i > 0 else None)

        tbl = QTableWidget()
        tbl.setColumnCount(2)
        tbl.setHorizontalHeaderLabels(["Feito", "Procedimento"])
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        tbl.setStyleSheet("""
            QTableWidget { background: transparent; border: none; }
            QTableWidget::item { padding: 4px; }
            QHeaderView::section { background: transparent; color: #a0a0b0; border: none; font-weight: 600; padding: 4px; }
        """)
        if atividade.procedimentos:
            try:
                dados = json.loads(atividade.procedimentos)
                for item in dados:
                    r = tbl.rowCount()
                    tbl.insertRow(r)
                    chk = QTableWidgetItem()
                    chk.setFlags(chk.flags() | Qt.ItemIsUserCheckable)
                    chk.setCheckState(Qt.Checked if item.get("feito") else Qt.Unchecked)
                    tbl.setItem(r, 0, chk)
                    tbl.setItem(r, 1, QTableWidgetItem(item.get("nome", "")))
            except json.JSONDecodeError:
                pass
        else:
            itens_padrao = [
                "Limpeza de laser", "Lubrificação do fusor",
                "Troca de película", "Troca de rolo de pressão", "Teste de impressão",
            ]
            for nome in itens_padrao:
                r = tbl.rowCount()
                tbl.insertRow(r)
                chk = QTableWidgetItem()
                chk.setFlags(chk.flags() | Qt.ItemIsUserCheckable)
                chk.setCheckState(Qt.Unchecked)
                tbl.setItem(r, 0, chk)
                tbl.setItem(r, 1, QTableWidgetItem(nome))

        btn_add = QPushButton("+ Adicionar")
        btn_add.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_add.setToolTip("Adicionar procedimento")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_rem = QPushButton("— Remover")
        btn_rem.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_rem.setToolTip("Remover selecionado")
        btn_rem.setCursor(Qt.PointingHandCursor)

        def _add():
            r = tbl.rowCount()
            tbl.insertRow(r)
            chk = QTableWidgetItem()
            chk.setFlags(chk.flags() | Qt.ItemIsUserCheckable)
            chk.setCheckState(Qt.Unchecked)
            tbl.setItem(r, 0, chk)
            tbl.setItem(r, 1, QTableWidgetItem(""))
            tbl.editItem(tbl.item(r, 1))

        def _rem():
            r = tbl.currentRow()
            if r >= 0:
                tbl.removeRow(r)

        btn_add.clicked.connect(_add)
        btn_rem.clicked.connect(_rem)

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setHorizontalSpacing(16)
        grid.addWidget(input_label("Solução Aplicada"), 0, 0, 1, 2)
        grid.addWidget(edt_solucao, 1, 0, 1, 2)
        grid.addWidget(input_label("Fim Atendimento"), 2, 0)
        grid.addWidget(edt_fim, 3, 0)
        grid.addWidget(input_label("Peças Trocadas"), 4, 0, 1, 2)
        grid.addWidget(edt_pecas, 5, 0, 1, 2)
        grid.addWidget(input_label("Peça do Estoque"), 6, 0, 1, 2)
        grid.addWidget(estoque_combo, 7, 0, 1, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        concluir_layout.addLayout(grid)
        concluir_layout.addWidget(QLabel("Checklist"))
        concluir_layout.addWidget(tbl)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_rem)
        concluir_layout.addLayout(btn_row)
        layout.addWidget(concluir_box)

        layout.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(24, 12, 24, 16)
        btn_layout.setSpacing(10)

        btn_concluir = QPushButton("✅ Concluir OS")
        btn_concluir.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_concluir.setToolTip("Finalizar ordem de serviço")
        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_fechar.setToolTip("Fechar sem concluir")

        def _salvar():
            solucao = edt_solucao.toPlainText().strip()
            fim = edt_fim.dateTime().toPython()
            pecas = edt_pecas.toPlainText().strip()

            dados = []
            for r in range(tbl.rowCount()):
                chk = tbl.item(r, 0)
                nome = tbl.item(r, 1)
                if nome and nome.text().strip():
                    dados.append({"nome": nome.text().strip(), "feito": bool(chk and chk.checkState() == Qt.Checked)})
            procedimentos = json.dumps(dados, ensure_ascii=False)

            try:
                with transacao(self.session):
                    self.activity_service.atualizar(
                        atividade,
                        solucao_aplicada=solucao,
                        fim_atendimento=fim,
                        parts_used=pecas,
                        status_atividade="Concluida",
                        procedimentos=procedimentos,
                    )
                    self._dar_baixa_estoque(pecas)
                dialog.accept()
                self.recarregar()
            except Exception as e:
                QMessageBox.critical(dialog, "Erro", f"Erro ao concluir OS: {e}")

        btn_concluir.clicked.connect(_salvar)
        btn_fechar.clicked.connect(dialog.reject)

        btn_layout.addWidget(btn_concluir)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_fechar)
        root.addLayout(btn_layout)

        dialog.exec()

    def _detalhes(self, row: int) -> None:
        if row < 0 or row >= len(self._atividades):
            return
        atividade = self._atividades[row]

        printer_str = "-"
        if atividade.printer_id:
            printer = self.printer_service.buscar_por_id(atividade.printer_id)
            if printer:
                printer_str = f"{printer.patrimonio} - {printer.modelo}"

        tecnico_str = "-"
        if atividade.tecnico_id and self.technician_service:
            tec = self.technician_service.buscar_por_id(atividade.tecnico_id)
            if tec:
                tecnico_str = tec.nome_exibicao

        dialog = QDialog(self)
        dialog.setWindowTitle("Ordem de Serviço")
        dialog.setMinimumSize(650, 500)
        dialog.setStyleSheet(ESTILO_DIALOG)

        root = QVBoxLayout(dialog)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        equip_box, equip_layout = group_box("Equipamento")
        equip_form = QFormLayout()
        equip_form.setSpacing(8)
        equip_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        equip_form.addRow(campo_rotulo("Impressora"), campo_readonly(printer_str))
        equip_form.addRow(campo_rotulo("Tipo"), campo_readonly(atividade.kind or "-"))
        equip_form.addRow(campo_rotulo("Técnico"), campo_readonly(tecnico_str))
        equip_layout.addLayout(equip_form)
        layout.addWidget(equip_box)

        def _formatar_tempo(diff):
            total_seg = int(diff.total_seconds())
            h = total_seg // 3600
            m = (total_seg % 3600) // 60
            if h > 0:
                return f"{h}h {m}min"
            return f"{m}min"

        tempo_str = "—"
        if atividade.inicio_atendimento and atividade.fim_atendimento:
            diff = atividade.fim_atendimento - atividade.inicio_atendimento
            tempo_str = _formatar_tempo(diff)

        detalhes_box, detalhes_layout = group_box("Detalhes")
        detalhes_form = QFormLayout()
        detalhes_form.setSpacing(8)
        detalhes_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        detalhes_form.addRow(campo_rotulo("Data/Hora"), campo_readonly(formatar_data_hora(atividade.event_at)))
        detalhes_form.addRow(campo_rotulo("Início Atendimento"), campo_readonly(formatar_data_hora(atividade.inicio_atendimento) if atividade.inicio_atendimento else "—"))
        detalhes_form.addRow(campo_rotulo("Fim Atendimento"), campo_readonly(formatar_data_hora(atividade.fim_atendimento) if atividade.fim_atendimento else "—"))
        detalhes_form.addRow(campo_rotulo("Tempo Atendimento"), campo_readonly(tempo_str))
        detalhes_form.addRow(campo_rotulo("Sintoma Relatado"), campo_readonly(atividade.sintoma_relatado or "—"))
        detalhes_form.addRow(campo_rotulo("Diagnóstico Técnico"), campo_readonly(atividade.diagnostico_tecnico or "—"))
        detalhes_form.addRow(campo_rotulo("Solução Aplicada"), campo_readonly(atividade.solucao_aplicada or "—"))
        detalhes_form.addRow(campo_rotulo("Descrição"), campo_readonly(atividade.notes or "—"))
        detalhes_form.addRow(campo_rotulo("Peças Trocadas"), campo_readonly(atividade.parts_used or "—"))
        detalhes_form.addRow(campo_rotulo("Status"), campo_readonly(atividade.status_atividade or "—"))
        detalhes_layout.addLayout(detalhes_form)
        layout.addWidget(detalhes_box)

        if atividade.procedimentos:
            try:
                procedimentos = json.loads(atividade.procedimentos)
                checklist_box, checklist_layout = group_box("Procedimentos Realizados")
                for item in procedimentos:
                    nome = item.get("nome", "")
                    feito = item.get("feito", False)
                    icon = "✅" if feito else "⬜"
                    lbl = QLabel(f"{icon}  {nome}")
                    lbl.setStyleSheet("color: #c8c8d8; font-size: 12px; padding: 2px 0; background: transparent;")
                    checklist_layout.addWidget(lbl)
                layout.addWidget(checklist_box)
            except json.JSONDecodeError:
                pass

        if atividade.kind == "MOVIMENTACAO":
            mov_box, mov_layout = group_box("Movimentação")
            mov_form = QFormLayout()
            mov_form.setSpacing(8)
            mov_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
            mov_form.addRow(campo_rotulo("Origem"), campo_readonly(atividade.from_location or "—"))
            mov_form.addRow(campo_rotulo("Destino"), campo_readonly(atividade.to_location or "—"))
            mov_layout.addLayout(mov_form)
            layout.addWidget(mov_box)

        layout.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(24, 12, 24, 16)
        btn_layout.setSpacing(10)

        btn_editar = QPushButton("✏️  Editar")
        btn_editar.setStyleSheet(ESTILO_BOTAO_AVISO)
        btn_editar.setToolTip("Editar esta ordem de serviço")

        btn_excluir = QPushButton("🗑️ Excluir")
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_excluir.setToolTip("Excluir esta ordem de serviço (pode ser desfeito pela Lixeira)")

        pode_concluir = atividade.status_atividade in ("Pendente", "Em Andamento")
        btn_concluir = QPushButton("✅ Concluir")
        btn_concluir.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_concluir.setToolTip("Finalizar esta ordem de serviço")
        btn_concluir.setVisible(pode_concluir)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_fechar.setToolTip("Fechar detalhes")

        def excluir():
            if ConfirmacaoDigitarDialog.confirmar(
                "Confirmar", "Deseja realmente excluir esta OS?",
                dialog,
            ):
                try:
                    self.activity_service.excluir(atividade)
                    ToastManager.mostrar(
                        "OS excluída.",
                        "aviso", duracao=8000,
                        acao=("Desfazer", lambda o=atividade, svc=self.activity_service, pag=self: (svc.restaurar(o), pag.recarregar())),
                    )
                    dialog.accept()
                    self.recarregar()
                except Exception as e:
                    QMessageBox.critical(dialog, "Erro", f"Erro ao excluir: {e}")

        def editar():
            dialog.accept()
            self._abrir_edicao(atividade)

        def concluir():
            dialog.accept()
            self._concluir_os_dialog(atividade)

        btn_editar.clicked.connect(editar)
        btn_excluir.clicked.connect(excluir)
        btn_concluir.clicked.connect(concluir)
        btn_fechar.clicked.connect(dialog.accept)

        btn_layout.addWidget(btn_concluir)
        btn_layout.addWidget(btn_editar)
        btn_layout.addWidget(btn_excluir)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_fechar)

        root.addLayout(btn_layout)

        dialog.exec()

    def _abrir_edicao(self, atividade: Any) -> None:
        dialog, campos = self._criar_form_dialog("Editar OS", atividade)

        botoes = QHBoxLayout()
        btn_salvar = QPushButton("Salvar")
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_salvar.setToolTip("Salvar alterações da ordem de serviço")
        btn_excluir = QPushButton("Excluir")
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_excluir.setToolTip("Excluir esta ordem de serviço (pode ser desfeito pela Lixeira)")
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_cancelar.setToolTip("Descartar alterações e fechar")
        botoes.addWidget(btn_salvar)
        botoes.addWidget(btn_excluir)
        botoes.addWidget(btn_cancelar)

        form_layout = dialog.layout()
        form_layout.addLayout(botoes)

        resultado = {"acao": None}

        def salvar():
            patrimonio = campos["printer"].currentText().strip()
            if not patrimonio:
                QMessageBox.warning(dialog, "Aviso", "Selecione uma impressora.")
                return
            printer = self.printer_service.buscar_por_patrimonio(patrimonio)
            if not printer:
                QMessageBox.warning(dialog, "Aviso", f"Impressora '{patrimonio}' não encontrada.")
                return

            kind = campos["tipo"].currentText()
            event_at = campos["data"].dateTime().toPython()
            notes = campos["descricao"].toPlainText().strip()
            parts_used = campos["pecas"].toPlainText().strip()
            sintoma_relatado = campos["sintoma"].toPlainText().strip()
            diagnostico_tecnico = campos["diagnostico"].toPlainText().strip()
            solucao_aplicada = campos["solucao"].toPlainText().strip()
            from_location = campos["origem"].currentText().strip()
            to_location = campos["destino"].currentText().strip()
            status_atividade = campos["status"].currentText()
            from_company_id = self._resolver_empresa(from_location)
            to_company_id = self._resolver_empresa(to_location)
            tecnico_id = self._resolver_tecnico(campos["tecnico"].currentText().strip())
            inicio_qdt = campos["inicio"].dateTime()
            fim_qdt = campos["fim"].dateTime()
            inicio_atendimento = inicio_qdt.toPython() if inicio_qdt.isValid() else None
            fim_atendimento = fim_qdt.toPython() if fim_qdt.isValid() else None

            tbl = campos.get("checklist")
            procedimentos = ""
            if tbl:
                dados = []
                for r in range(tbl.rowCount()):
                    chk = tbl.item(r, 0)
                    nome = tbl.item(r, 1)
                    if nome and nome.text().strip():
                        dados.append({"nome": nome.text().strip(), "feito": bool(chk and chk.checkState() == Qt.Checked)})
                procedimentos = json.dumps(dados, ensure_ascii=False)

            try:
                with transacao(self.session):
                    self.activity_service.atualizar(
                        atividade,
                        printer_id=printer.id,
                        kind=kind,
                        event_at=event_at,
                        notes=notes,
                        parts_used=parts_used,
                        sintoma_relatado=sintoma_relatado,
                        diagnostico_tecnico=diagnostico_tecnico,
                        solucao_aplicada=solucao_aplicada,
                        inicio_atendimento=inicio_atendimento,
                        fim_atendimento=fim_atendimento,
                        from_location=from_location,
                        to_location=to_location,
                        status_atividade=status_atividade,
                        from_company_id=from_company_id,
                        to_company_id=to_company_id,
                        tecnico_id=tecnico_id,
                        procedimentos=procedimentos,
                    )
                    self._dar_baixa_estoque(parts_used)
                resultado["acao"] = "salvar"
                dialog.accept()
                self.recarregar()
            except Exception as e:
                QMessageBox.critical(dialog, "Erro", f"Erro ao salvar: {e}")

        def excluir():
            if ConfirmacaoDigitarDialog.confirmar(
                "Confirmar", "Deseja realmente excluir esta OS?",
                dialog,
            ):
                try:
                    self.activity_service.excluir(atividade)
                    ToastManager.mostrar(
                        "OS excluída.",
                        "aviso", duracao=8000,
                        acao=("Desfazer", lambda o=atividade, svc=self.activity_service, pag=self: (svc.restaurar(o), pag.recarregar())),
                    )
                    resultado["acao"] = "excluir"
                    dialog.accept()
                    self.recarregar()
                except Exception as e:
                    QMessageBox.critical(dialog, "Erro", f"Erro ao excluir: {e}")

        def cancelar():
            resultado["acao"] = "cancelar"
            dialog.reject()

        btn_salvar.clicked.connect(salvar)
        btn_excluir.clicked.connect(excluir)
        btn_cancelar.clicked.connect(cancelar)

        dialog.exec()

    def _criar_form_dialog(self, titulo: str, atividade: Any = None) -> tuple[QDialog, dict[str, Any]]:
        dialog = QDialog(self)
        dialog.setWindowTitle(titulo)
        dialog.setMinimumSize(580, 620)
        dialog.setStyleSheet(ESTILO_DIALOG)

        outer = QVBoxLayout(dialog)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        content = QVBoxLayout(container)
        content.setContentsMargins(16, 8, 16, 8)
        content.setSpacing(14)

        printers = self.printer_service.listar_todos()
        nomes_impressoras = [p.patrimonio for p in printers]

        cmb_printer = QComboBox()
        cmb_printer.setEditable(True)
        configurar_combo(cmb_printer)
        cmp = cmb_printer.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        cmb_printer.addItems(nomes_impressoras)
        cmb_printer.setInsertPolicy(QComboBox.NoInsert)

        cmb_tipo = QComboBox()
        configurar_combo(cmb_tipo)
        cmp = cmb_tipo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        cmb_tipo.addItems(["MANUTENCAO", "MOVIMENTACAO"])

        cmb_tecnico = QComboBox()
        cmb_tecnico.setEditable(True)
        configurar_combo(cmb_tecnico)
        cmp = cmb_tecnico.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        if self.technician_service:
            cmb_tecnico.addItems(self.technician_service.nomes_exibicao())
        cmb_tecnico.setInsertPolicy(QComboBox.NoInsert)

        equip_box, equip_layout = group_box("Equipamento")
        equip_grid = QGridLayout()
        equip_grid.setSpacing(8)
        equip_grid.setHorizontalSpacing(16)
        equip_grid.addWidget(input_label("Impressora"), 0, 0)
        equip_grid.addWidget(cmb_printer, 1, 0)
        equip_grid.addWidget(input_label("Tipo"), 0, 1)
        equip_grid.addWidget(cmb_tipo, 1, 1)
        equip_grid.addWidget(input_label("Técnico"), 2, 0, 1, 2)
        equip_grid.addWidget(cmb_tecnico, 3, 0, 1, 2)
        equip_grid.setColumnStretch(0, 1)
        equip_grid.setColumnStretch(1, 1)
        equip_layout.addLayout(equip_grid)
        content.addWidget(equip_box)

        from PySide6.QtCore import QDateTime

        edt_data = QDateTimeEdit(QDateTime.currentDateTime())
        edt_data.setCalendarPopup(True)
        edt_data.setDisplayFormat("dd/MM/yyyy HH:mm")
        edt_data.setStyleSheet(ESTILO_INPUT)

        cmb_status = QComboBox()
        configurar_combo(cmb_status)
        cmp = cmb_status.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        cmb_status.addItems(["Concluida", "Pendente", "Em Andamento"])

        txt_descricao = QTextEdit()
        txt_descricao.setStyleSheet(ESTILO_INPUT)
        txt_descricao.setMaximumHeight(80)

        txt_pecas = QTextEdit()
        txt_pecas.setStyleSheet(ESTILO_INPUT)
        txt_pecas.setMaximumHeight(60)

        estoque_combo_os = QComboBox()
        configurar_combo(estoque_combo_os)
        cmp = estoque_combo_os.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        estoque_combo_os.addItem("-- Nenhuma --", None)
        for p in self.part_service.listar_todas():
            if p.quantidade_estoque > 0:
                estoque_combo_os.addItem(f"{p.nome} ({p.quantidade_estoque} un.)", p.id)

        def _preencher_pecas_os(idx):
            if idx <= 0:
                return
            try:
                pid = estoque_combo_os.currentData()
                if pid is None:
                    return
                part = self.part_service.buscar_por_id(pid)
                if part:
                    atual = txt_pecas.toPlainText().strip()
                    txt_pecas.setPlainText(f"{part.nome}" if not atual else f"{atual}, {part.nome}")
            except RuntimeError:
                pass
        estoque_combo_os.currentIndexChanged.connect(_preencher_pecas_os)

        txt_sintoma = QTextEdit()
        txt_sintoma.setStyleSheet(ESTILO_INPUT)
        txt_sintoma.setMaximumHeight(80)

        txt_diagnostico = QTextEdit()
        txt_diagnostico.setStyleSheet(ESTILO_INPUT)
        txt_diagnostico.setMaximumHeight(80)

        txt_solucao = QTextEdit()
        txt_solucao.setStyleSheet(ESTILO_INPUT)
        txt_solucao.setMaximumHeight(80)

        edt_inicio = QDateTimeEdit()
        edt_inicio.setCalendarPopup(True)
        edt_inicio.setDisplayFormat("dd/MM/yyyy HH:mm")
        edt_inicio.setStyleSheet(ESTILO_INPUT)
        edt_inicio.setDateTime(QDateTime.currentDateTime())

        edt_fim = QDateTimeEdit()
        edt_fim.setCalendarPopup(True)
        edt_fim.setDisplayFormat("dd/MM/yyyy HH:mm")
        edt_fim.setStyleSheet(ESTILO_INPUT)

        detalhes_box, detalhes_layout = group_box("Detalhes")
        detalhes_grid = QGridLayout()
        detalhes_grid.setSpacing(8)
        detalhes_grid.setHorizontalSpacing(16)
        detalhes_grid.addWidget(input_label("Data/Hora"), 0, 0)
        detalhes_grid.addWidget(edt_data, 1, 0)
        detalhes_grid.addWidget(input_label("Status"), 0, 1)
        detalhes_grid.addWidget(cmb_status, 1, 1)
        detalhes_grid.addWidget(input_label("Início Atendimento"), 2, 0)
        detalhes_grid.addWidget(edt_inicio, 3, 0)
        detalhes_grid.addWidget(input_label("Fim Atendimento"), 2, 1)
        detalhes_grid.addWidget(edt_fim, 3, 1)
        detalhes_grid.addWidget(input_label("Sintoma Relatado"), 4, 0, 1, 2)
        detalhes_grid.addWidget(txt_sintoma, 5, 0, 1, 2)
        detalhes_grid.addWidget(input_label("Diagnóstico Técnico"), 6, 0, 1, 2)
        detalhes_grid.addWidget(txt_diagnostico, 7, 0, 1, 2)
        detalhes_grid.addWidget(input_label("Solução Aplicada"), 8, 0, 1, 2)
        detalhes_grid.addWidget(txt_solucao, 9, 0, 1, 2)
        detalhes_grid.addWidget(input_label("Descrição"), 10, 0, 1, 2)
        detalhes_grid.addWidget(txt_descricao, 11, 0, 1, 2)
        detalhes_grid.addWidget(input_label("Peças Trocadas"), 12, 0, 1, 2)
        detalhes_grid.addWidget(txt_pecas, 13, 0, 1, 2)
        detalhes_grid.addWidget(input_label("Peça do Estoque"), 14, 0, 1, 2)
        detalhes_grid.addWidget(estoque_combo_os, 15, 0, 1, 2)
        detalhes_grid.setColumnStretch(0, 1)
        detalhes_grid.setColumnStretch(1, 1)
        detalhes_layout.addLayout(detalhes_grid)
        content.addWidget(detalhes_box)

        # ── Checklist ──
        checklist_box, checklist_layout = group_box("Checklist")
        tbl = QTableWidget()
        tbl.setColumnCount(2)
        tbl.setHorizontalHeaderLabels(["Feito", "Procedimento"])
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        tbl.setStyleSheet("""
            QTableWidget { background: transparent; border: none; }
            QTableWidget::item { padding: 4px; }
            QHeaderView::section { background: transparent; color: #a0a0b0; border: none; font-weight: 600; padding: 4px; }
        """)
        itens_padrao = [
            "Limpeza de laser",
            "Lubrificação do fusor",
            "Troca de película",
            "Troca de rolo de pressão",
            "Teste de impressão",
        ]
        for nome in itens_padrao:
            r = tbl.rowCount()
            tbl.insertRow(r)
            chk = QTableWidgetItem()
            chk.setFlags(chk.flags() | Qt.ItemIsUserCheckable)
            chk.setCheckState(Qt.Unchecked)
            tbl.setItem(r, 0, chk)
            tbl.setItem(r, 1, QTableWidgetItem(nome))
        tbl.setMinimumHeight(140)
        checklist_layout.addWidget(tbl)

        btn_add = QPushButton("+ Adicionar")
        btn_add.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_add.setToolTip("Adicionar procedimento personalizado")
        btn_add.setCursor(Qt.PointingHandCursor)

        btn_rem = QPushButton("— Remover")
        btn_rem.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_rem.setToolTip("Remover procedimento selecionado")
        btn_rem.setCursor(Qt.PointingHandCursor)

        def _add_procedimento():
            r = tbl.rowCount()
            tbl.insertRow(r)
            chk = QTableWidgetItem()
            chk.setFlags(chk.flags() | Qt.ItemIsUserCheckable)
            chk.setCheckState(Qt.Unchecked)
            tbl.setItem(r, 0, chk)
            tbl.setItem(r, 1, QTableWidgetItem(""))
            tbl.editItem(tbl.item(r, 1))

        def _rem_procedimento():
            r = tbl.currentRow()
            if r >= 0:
                tbl.removeRow(r)

        btn_add.clicked.connect(_add_procedimento)
        btn_rem.clicked.connect(_rem_procedimento)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_rem)
        checklist_layout.addLayout(btn_row)
        content.addWidget(checklist_box)

        empresas = self.company_service.listar_nomes() if self.company_service else []

        cmb_origem = QComboBox()
        cmb_origem.setEditable(True)
        configurar_combo(cmb_origem)
        cmp = cmb_origem.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        cmb_origem.addItems(empresas)
        cmb_origem.setInsertPolicy(QComboBox.NoInsert)
        cmb_origem.setCurrentText("")

        cmb_destino = QComboBox()
        cmb_destino.setEditable(True)
        configurar_combo(cmb_destino)
        cmp = cmb_destino.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        cmb_destino.addItems(empresas)
        cmb_destino.setInsertPolicy(QComboBox.NoInsert)
        cmb_destino.setCurrentText("")

        mov_box, mov_layout = group_box("Movimentação")
        mov_grid = QGridLayout()
        mov_grid.setSpacing(8)
        mov_grid.setHorizontalSpacing(16)
        mov_grid.addWidget(input_label("Origem"), 0, 0)
        mov_grid.addWidget(cmb_origem, 1, 0)
        mov_grid.addWidget(input_label("Destino"), 0, 1)
        mov_grid.addWidget(cmb_destino, 1, 1)
        mov_grid.setColumnStretch(0, 1)
        mov_grid.setColumnStretch(1, 1)
        mov_layout.addLayout(mov_grid)
        content.addWidget(mov_box)

        def _toggle_origem_destino(tipo):
            visivel = tipo == "MOVIMENTACAO"
            mov_box.setVisible(visivel)
            if not visivel:
                cmb_origem.setCurrentText("")
                cmb_destino.setCurrentText("")
        cmb_tipo.currentTextChanged.connect(_toggle_origem_destino)
        _toggle_origem_destino(cmb_tipo.currentText())

        content.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll, stretch=1)

        campos = {
            "printer": cmb_printer,
            "tipo": cmb_tipo,
            "data": edt_data,
            "inicio": edt_inicio,
            "fim": edt_fim,
            "sintoma": txt_sintoma,
            "diagnostico": txt_diagnostico,
            "solucao": txt_solucao,
            "descricao": txt_descricao,
            "pecas": txt_pecas,
            "origem": cmb_origem,
            "destino": cmb_destino,
            "tecnico": cmb_tecnico,
            "status": cmb_status,
            "checklist": tbl,
        }

        if atividade:
            self._preencher_campos(atividade, campos)

        if not atividade:
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(10)
            btn_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
            btn_box.button(QDialogButtonBox.Save).setText("Salvar")
            btn_box.button(QDialogButtonBox.Save).setStyleSheet(ESTILO_BOTAO_SUCESSO)
            btn_box.button(QDialogButtonBox.Save).setToolTip("Salvar alterações da ordem de serviço")
            btn_box.button(QDialogButtonBox.Cancel).setStyleSheet(ESTILO_BOTAO_FECHAR)
            btn_box.button(QDialogButtonBox.Cancel).setToolTip("Cancelar e fechar")
            btn_box.accepted.connect(dialog.accept)
            btn_box.rejected.connect(dialog.reject)
            btn_layout.addStretch()
            btn_layout.addWidget(btn_box)
            outer.addLayout(btn_layout)

        return dialog, campos

    def _preencher_campos(self, atividade: Any, campos: dict[str, Any]) -> None:
        printer = self.printer_service.buscar_por_id(atividade.printer_id)
        if printer:
            idx = campos["printer"].findText(printer.patrimonio)
            if idx >= 0:
                campos["printer"].setCurrentIndex(idx)
            else:
                campos["printer"].setCurrentText(printer.patrimonio)

        idx_tipo = campos["tipo"].findText(atividade.kind)
        if idx_tipo >= 0:
            campos["tipo"].setCurrentIndex(idx_tipo)

        campos["data"].setDateTime(QDateTime(atividade.event_at))
        if atividade.inicio_atendimento:
            campos["inicio"].setDateTime(QDateTime(atividade.inicio_atendimento))
        if atividade.fim_atendimento:
            campos["fim"].setDateTime(QDateTime(atividade.fim_atendimento))
        campos["sintoma"].setPlainText(atividade.sintoma_relatado or "")
        campos["diagnostico"].setPlainText(atividade.diagnostico_tecnico or "")
        campos["solucao"].setPlainText(atividade.solucao_aplicada or "")
        campos["descricao"].setPlainText(atividade.notes or "")
        campos["pecas"].setPlainText(atividade.parts_used or "")

        if atividade.from_location:
            idx_orig = campos["origem"].findText(atividade.from_location)
            if idx_orig >= 0:
                campos["origem"].setCurrentIndex(idx_orig)
            else:
                campos["origem"].setCurrentText(atividade.from_location)

        if atividade.to_location:
            idx_dest = campos["destino"].findText(atividade.to_location)
            if idx_dest >= 0:
                campos["destino"].setCurrentIndex(idx_dest)
            else:
                campos["destino"].setCurrentText(atividade.to_location)

        if atividade.tecnico_id and self.technician_service:
            tec = self.technician_service.buscar_por_id(atividade.tecnico_id)
            if tec:
                idx_tec = campos["tecnico"].findText(tec.nome_exibicao)
                if idx_tec >= 0:
                    campos["tecnico"].setCurrentIndex(idx_tec)
                else:
                    campos["tecnico"].setCurrentText(tec.nome_exibicao)

        idx_st = campos["status"].findText(atividade.status_atividade or "Concluida",
                                           Qt.MatchFixedString)
        if idx_st >= 0:
            campos["status"].setCurrentIndex(idx_st)

        tbl = campos.get("checklist")
        if tbl and atividade.procedimentos:
            try:
                dados = json.loads(atividade.procedimentos)
                tbl.setRowCount(0)
                for item in dados:
                    r = tbl.rowCount()
                    tbl.insertRow(r)
                    chk = QTableWidgetItem()
                    chk.setFlags(chk.flags() | Qt.ItemIsUserCheckable)
                    chk.setCheckState(Qt.Checked if item.get("feito") else Qt.Unchecked)
                    tbl.setItem(r, 0, chk)
                    tbl.setItem(r, 1, QTableWidgetItem(item.get("nome", "")))
            except json.JSONDecodeError:
                pass

    def _resolver_empresa(self, nome: str) -> Any | None:
        if not nome or not self.company_service:
            return None
        empresa = self.company_service.buscar_por_nome(nome)
        return empresa.id if empresa else None

    def _resolver_tecnico(self, nome: str) -> int | None:
        if not nome or not self.technician_service:
            return None
        tecnicos = self.technician_service.listar_ativos()
        for t in tecnicos:
            if t.nome_exibicao == nome or t.nome_completo == nome:
                return t.id
        return None

    def _dar_baixa_estoque(self, pecas_texto: str) -> None:
        if not pecas_texto:
            return
        for nome_peca in pecas_texto.split(","):
            nome_peca = nome_peca.strip()
            if not nome_peca:
                continue
            with tratar_erro("dar baixa no estoque"):
                part = self.part_service.buscar_por_nome(nome_peca)
                if part and part.quantidade_estoque > 0:
                    self.part_service.atualizar(part, quantidade_estoque=part.quantidade_estoque - 1)
