from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime as dt
from collections.abc import Callable
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

from PySide6.QtCore import QDate, QDateTime, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
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
    QTabWidget,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models import Attachment, Part
from app.services.part_service import PartService
from app.utils.ui_helpers import tratar_erro
from app.utils.helpers import formatar_data_hora
from db import transacao
from app.utils.constants import STATUS_ATIVIDADE_OPCOES
from app.views.styles.theme import (
    ATIVIDADE_CORES,
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
    ESTILO_TABELA_SIMPLES,
    ESTILO_TITULO_PAGINA,
    URGENCIAS,
    URGENCIA_CORES,
    campo_readonly,
    campo_rotulo,
    configurar_combo,
    configurar_combo_colorido,
    group_box,
    input_label,
)
from app.views.widgets import ToastManager
from app.views.widgets.card_widget import CardMiniClicavel
from app.views.widgets.confirm_dialog import ConfirmacaoDigitarDialog
from app.views.widgets.pagination import PaginacaoWidget
from app.views.widgets.search_bar import SearchBar
from app.views.widgets.table_widget import TabelaPadrao, tornar_interativa
from db import safe_commit as _safe_commit

from config import ANEXOS_DIR


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

    def __init__(self, session: Any, printer_service: Any, activity_service: Any, company_service: Any, technician_service: Any, alert_service: Any = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        self.printer_service = printer_service
        self.activity_service = activity_service
        self.company_service = company_service
        self.technician_service = technician_service
        self.alert_service = alert_service

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

        self.card_andamento = CardMiniClicavel("\U0001f504", "Em Atendimento", "0", "#6366f1",
                                                ao_clicar=lambda: self._filtrar_status("Em Atendimento"))
        cards.addWidget(self.card_andamento)

        self.card_pendentes = CardMiniClicavel("\u23f3", "Aberta", "0", "#94a3b8",
                                                ao_clicar=lambda: self._filtrar_status("Aberta"))
        cards.addWidget(self.card_pendentes)

        self.card_concluidas = CardMiniClicavel("\u2705", "Concluído", "0", "#10b981",
                                                 ao_clicar=lambda: self._filtrar_status("Concluido"))
        cards.addWidget(self.card_concluidas)

        layout.addLayout(cards)

        self.tabela = TabelaPadrao(["Data/Hora", "Patrimônio", "Tipo", "Descrição", "Peças", "Urgência", "Origem", "Destino", "Técnico", "Vínculo"])
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

            urg_val = getattr(atv, 'urgencia', '') or 'Normal'
            cor_urg = URGENCIA_CORES.get(urg_val, "#717182")
            self.tabela.definir_badge(row, 5, urg_val, cor_urg)

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

            tem_vinculo = bool(atv.os_vinculada_id) or bool(atv.oses_filhas)
            self.tabela.definir_badge(row, 9, "🔗" if tem_vinculo else "", "#818cf8" if tem_vinculo else "transparent")

            self.tabela.setItem(row, 0, data_item)
            self.tabela.setItem(row, 1, pat_item)
            self.tabela.setItem(row, 3, desc_item)
            self.tabela.setItem(row, 4, pecas_item)
            self.tabela.setItem(row, 6, orig_item)
            self.tabela.setItem(row, 7, dest_item)
            self.tabela.setItem(row, 8, tecnico_item)

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
        andamento = self.activity_service.contar_por_status("Em Atendimento")
        pendentes = self.activity_service.contar_por_status("Aberta")
        concluidas = self.activity_service.contar_por_status("Concluido")
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
        sintoma_relatado = campos["sintoma"].toPlainText().strip()
        diagnostico_tecnico = campos["diagnostico"].toPlainText().strip()
        solucao_aplicada = campos["solucao"].toPlainText().strip()
        from_location = campos["origem"].currentText().strip()
        to_location = campos["destino"].currentText().strip()
        status_atividade = campos["status"].currentText()
        urgencia = campos["urgencia"].currentText()

        from_company_id = self._resolver_empresa(from_location)
        to_company_id = self._resolver_empresa(to_location)
        tecnico_id = self._resolver_tecnico(campos["tecnico"].currentText().strip())

        inicio_qdt = campos["inicio"].dateTime()
        fim_qdt = campos["fim"].dateTime()
        inicio_atendimento = inicio_qdt.toPython() if inicio_qdt.isValid() else None
        fim_atendimento = fim_qdt.toPython() if fim_qdt.isValid() else None
        parts_used = campos["pecas"].toPlainText().strip()
        os_vinculada_id = campos["os_vinculada"].currentData()

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
                    urgencia=urgencia,
                    os_vinculada_id=os_vinculada_id,
                )
                self._criar_alerta_urgencia(printer, urgencia)
                self._dar_baixa_estoque(parts_used, activity_id=atividade.id)
                self.activity_service.atualizar(
                    atividade,
                    from_company_id=from_company_id,
                    to_company_id=to_company_id,
                )
                fotos_pendentes = getattr(dialog, "pending_fotos", [])
                for file_path, categoria in fotos_pendentes:
                    original_name = os.path.basename(file_path)
                    timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
                    ext = os.path.splitext(original_name)[1]
                    stored_name = f"activity_{atividade.id}_{timestamp}_{original_name}"
                    dest = ANEXOS_DIR / stored_name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, str(dest))
                    anexo = Attachment(
                        entity_type="activity",
                        entity_id=atividade.id,
                        original_name=original_name,
                        file_path=str(dest),
                        categoria=categoria,
                    )
                    self.session.add(anexo)
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
        tornar_interativa(tbl)
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tbl.verticalHeader().setVisible(False)
        tbl.verticalHeader().setDefaultSectionSize(32)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        tbl.setStyleSheet("""
            QTableWidget { background: transparent; border: none; }
            QTableWidget::item { padding: 4px; color: #e2e8f0; font-size: 13px; }
            QHeaderView::section { background: transparent; color: #a0a0b0; border: none; font-weight: 600; padding: 4px; }
            QTableWidget QLineEdit {
                background-color: #1e1e2f !important;
                color: #ffffff !important;
                border: 1px solid #3b82f6 !important;
                border-radius: 4px;
                padding: 2px 6px !important;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px; height: 18px;
                border: 2px solid #3b82f6; border-radius: 4px;
                background-color: #1e1e2f;
            }
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
            }
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
            item_texto = QTableWidgetItem("")
            tbl.setItem(r, 1, item_texto)
            tbl.setCurrentCell(r, 1)
            tbl.editItem(item_texto)

        def _rem():
            r = tbl.currentRow()
            if r >= 0:
                tbl.removeRow(r)

        btn_add.clicked.connect(_add)
        btn_rem.clicked.connect(_rem)

        chk_agendar = QCheckBox("Agendar próxima manutenção da impressora")
        chk_agendar.setStyleSheet("color: #e2e8f0; font-size: 12px; spacing: 8px; margin-top: 4px;")
        chk_agendar.setToolTip("Define a data da próxima manutenção programada para esta impressora")
        chk_agendar.setChecked(True)

        edt_prox = QDateEdit()
        edt_prox.setCalendarPopup(True)
        edt_prox.setDisplayFormat("dd/MM/yyyy")
        edt_prox.setDate(QDate.currentDate().addMonths(3))
        edt_prox.setStyleSheet(ESTILO_INPUT)
        edt_prox.setEnabled(True)
        chk_agendar.toggled.connect(edt_prox.setEnabled)

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
        btn_reservar = QPushButton("📌 Reservar")
        btn_reservar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_reservar.setToolTip("Reservar esta peça para esta OS (baixa no estoque)")
        def _reservar():
            idx = estoque_combo.currentIndex()
            if idx <= 0:
                return
            pid = estoque_combo.currentData()
            if pid is None:
                return
            with tratar_erro("reservar peça"):
                res = self.part_service.criar_reserva(pid, atividade.id, quantidade=1)
                if res:
                    ToastManager.mostrar(f"Peça reservada para OS #{atividade.id}.", "sucesso")
                    _atualizar_reservas()
                    estoque_combo.setCurrentIndex(0)
                    self.recarregar()
                else:
                    ToastManager.mostrar("Estoque insuficiente para reservar.", "erro")
        btn_reservar.clicked.connect(_reservar)
        grid.addWidget(btn_reservar, 8, 0, 1, 2)

        # ── Reservas existentes ──
        reservas_box, reservas_layout = group_box("Peças Reservadas")
        reservas_tabela = QTableWidget()
        reservas_tabela.setColumnCount(5)
        reservas_tabela.setHorizontalHeaderLabels(["Peça", "Qtd", "Status", "Data", ""])
        reservas_tabela.setStyleSheet(ESTILO_TABELA_SIMPLES)
        reservas_tabela.setSelectionBehavior(QTableWidget.SelectRows)
        reservas_tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        reservas_tabela.verticalHeader().setVisible(False)
        reservas_tabela.setAlternatingRowColors(True)
        reservas_tabela.verticalHeader().setDefaultSectionSize(28)
        tornar_interativa(reservas_tabela)
        reservas_tabela.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        def _cancelar_reserva(res_id: int):
            with tratar_erro("cancelar reserva"):
                self.part_service.cancelar_reserva(res_id)
                ToastManager.mostrar("Reserva cancelada. Estoque restaurado.", "sucesso")
                _atualizar_reservas()
                self.recarregar()
        def _atualizar_reservas():
            reservas = self.part_service.reservas_por_os(atividade.id)
            reservas_tabela.setRowCount(len(reservas))
            for i, r in enumerate(reservas):
                reservas_tabela.setItem(i, 0, QTableWidgetItem(r.part.nome if r.part else "-"))
                item_q = QTableWidgetItem(str(r.quantidade))
                item_q.setTextAlignment(Qt.AlignCenter)
                reservas_tabela.setItem(i, 1, item_q)
                reservas_tabela.setItem(i, 2, QTableWidgetItem(r.status))
                reservas_tabela.setItem(i, 3, QTableWidgetItem(formatar_data_hora(r.created_at)))
                if r.status == "reservada":
                    btn_cancel = QPushButton("✕")
                    btn_cancel.setFixedSize(24, 24)
                    btn_cancel.setStyleSheet("color: #ef4444; font-size: 12px; background: transparent; border: none;")
                    btn_cancel.setToolTip("Cancelar reserva")
                    btn_cancel.clicked.connect(lambda _, rid=r.id: _cancelar_reserva(rid))
                    reservas_tabela.setCellWidget(i, 4, btn_cancel)
                else:
                    reservas_tabela.setItem(i, 4, QTableWidgetItem(""))
        _atualizar_reservas()
        reservas_layout.addWidget(reservas_tabela)
        layout.addWidget(reservas_box)

        chk_agendar = QCheckBox("Agendar próxima manutenção da impressora")
        chk_agendar.setStyleSheet("color: #e2e8f0; font-size: 12px; spacing: 8px; margin-top: 4px;")
        chk_agendar.setToolTip("Define a data da próxima manutenção programada para esta impressora")
        chk_agendar.setChecked(True)

        edt_prox = QDateEdit()
        edt_prox.setCalendarPopup(True)
        edt_prox.setDisplayFormat("dd/MM/yyyy")
        edt_prox.setDate(QDate.currentDate().addMonths(3))
        edt_prox.setStyleSheet(ESTILO_INPUT)
        edt_prox.setEnabled(True)
        chk_agendar.toggled.connect(edt_prox.setEnabled)

        grid.addWidget(chk_agendar, 9, 0, 1, 2)
        grid.addWidget(edt_prox, 10, 0)
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

        # ── FOTOS ────────────────────────────────────────────────────────
        dialog._fotos_box_concluir, _ = self._criar_grupo_fotos(atividade.id)
        layout.addWidget(dialog._fotos_box_concluir)

        def _atualizar_galeria_concluir():
            old = dialog._fotos_box_concluir
            idx = layout.indexOf(old)
            if idx >= 0:
                layout.removeWidget(old)
                old.deleteLater()
            dialog._fotos_box_concluir, _ = self._criar_grupo_fotos(atividade.id)
            layout.insertWidget(idx if idx >= 0 else layout.count(), dialog._fotos_box_concluir)

        dialog.refresh_gallery_cb = _atualizar_galeria_concluir

        fotos_upload_layout = QHBoxLayout()
        fotos_upload_layout.setSpacing(8)
        cmb_cat_concluir = QComboBox()
        configurar_combo(cmb_cat_concluir)
        cmb_cat_concluir.addItems(["antes", "depois", "peca"])
        cmb_cat_concluir.setMinimumWidth(140)
        btn_foto_concluir = QPushButton("📷 Adicionar Foto")
        btn_foto_concluir.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_foto_concluir.setToolTip("Adicionar foto antes de concluir")
        btn_foto_concluir.setCursor(Qt.PointingHandCursor)
        btn_foto_concluir.clicked.connect(
            lambda: (self._anexar_arquivo(atividade.id, cmb_cat_concluir.currentText(), dialog),
                     _atualizar_galeria_concluir())
        )
        fotos_upload_layout.addWidget(cmb_cat_concluir)
        fotos_upload_layout.addWidget(btn_foto_concluir)
        fotos_upload_layout.addStretch()
        layout.addLayout(fotos_upload_layout)

        layout.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(24, 12, 24, 24)
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
                        status_atividade="Concluido",
                        procedimentos=procedimentos,
                    )
                    self._dar_baixa_estoque(pecas, activity_id=atividade.id)
                    for res in self.part_service.reservas_por_os(atividade.id):
                        if res.status == "reservada":
                            self.part_service.usar_reserva(res.id)
                    if printer:
                        self.printer_service.atualizar(printer, ultima_revisao=fim)
                        if chk_agendar.isChecked():
                            data_prox = edt_prox.date().toPython()
                            self.printer_service.atualizar(printer, proxima_revisao=data_prox)
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

    # ── Anexos / Fotos ────────────────────────────────────────────────
    def _listar_anexos(self, activity_id: int) -> list[Attachment]:
        return (
            self.session.query(Attachment)
            .filter(Attachment.entity_type == "activity", Attachment.entity_id == activity_id)
            .order_by(Attachment.created_at.desc())
            .all()
        )

    def _anexar_arquivo(self, activity_id: int, categoria: str, dialog: QWidget) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            dialog, "Selecionar Arquivo", "", "Imagens (*.png *.jpg *.jpeg *.bmp);;Todos (*.*)"
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
                ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".bmp": "image/bmp",
            }
            attachment = Attachment(
                entity_type="activity",
                entity_id=activity_id,
                filename=safe_name,
                original_name=original_name,
                file_path=dest_path,
                mime_type=mime_map.get(ext, "application/octet-stream"),
                size_bytes=os.path.getsize(file_path),
                categoria=categoria,
            )
            self.session.add(attachment)
            _safe_commit(self.session)
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(dialog, "Erro", f"Erro ao anexar arquivo:\n{e}")

    def _remover_anexo(self, anexo_id: int, dialog: QWidget) -> None:
        if not ConfirmacaoDigitarDialog.confirmar(
            "Remover Anexo", "Deseja realmente remover este anexo?",
            dialog,
        ):
            return
        try:
            anexo = self.session.query(Attachment).filter_by(id=anexo_id).first()
            if anexo:
                if os.path.exists(anexo.file_path):
                    os.remove(anexo.file_path)
                self.session.delete(anexo)
                _safe_commit(self.session)
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(dialog, "Erro", f"Erro ao remover anexo:\n{e}")

    def _abrir_anexo(self, file_path: str) -> None:
        if os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Aviso", f"Não foi possível abrir o arquivo:\n{e}")
        else:
            QMessageBox.warning(self, "Aviso", "Arquivo não encontrado:\n" + file_path)

    def _criar_grupo_fotos(self, activity_id: int | None = None, *,
                          pending_fotos: list[tuple[str, str]] | None = None) -> tuple[QWidget, QVBoxLayout]:
        fotos_box, fotos_layout = group_box("GALERIA DE FOTOS")

        galeria_principal = QHBoxLayout()
        galeria_principal.setSpacing(16)
        galeria_principal.setContentsMargins(4, 4, 4, 4)

        galeria_scroll = QScrollArea()
        galeria_scroll.setWidgetResizable(True)
        galeria_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        galeria_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        galeria_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        galeria_container = QWidget()
        galeria_container.setStyleSheet("background: transparent;")
        galeria_container.setLayout(galeria_principal)
        galeria_scroll.setWidget(galeria_container)

        categorias = {"antes": "Antes", "depois": "Depois", "peca": "Peça Quebrada"}
        subtitulos = {"antes": "Antes da manutenção", "depois": "Após a manutenção", "peca": "Peça com defeito"}

        estilo_card = """
            QWidget {
                background-color: #11111e;
                border: 1px solid #2a2a3e;
                border-radius: 8px;
            }
        """
        estilo_titulo_card = "color: #ffffff; font-size: 16px; font-weight: bold; border: none; background: transparent;"
        estilo_sub_card = "color: #717182; font-size: 12px; border: none; background: transparent;"
        estilo_thumb = "border-radius: 6px; border: none; background: #1e1e2f;"
        estilo_btn_visualizar = """
            QPushButton {
                background-color: #3b82f6; color: white; border: none; border-radius: 6px;
                padding: 10px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2563eb; }
        """
        estilo_btn_excluir = """
            QPushButton {
                background-color: #ef4444; color: white; border: none; border-radius: 6px;
                padding: 10px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #dc2626; }
        """
        estilo_seta = """
            QPushButton {
                background-color: transparent; color: #818cf8;
                border: 1px solid #2a2a3e; border-radius: 6px;
                font-size: 18px; min-width: 36px; min-height: 36px;
            }
            QPushButton:hover { background-color: rgba(99,102,241,0.15); border-color: #6366f1; }
            QPushButton:disabled { color: #3a3a4e; border-color: #1e1e2e; }
        """
        estilo_contador = "color: #717182; font-size: 11px; background: transparent;"

        def _criar_card(chave: str, rotulo: str) -> QWidget:
            card = QWidget()
            card.setStyleSheet(estilo_card)
            card.setMinimumWidth(400)
            layout_card = QVBoxLayout(card)
            layout_card.setContentsMargins(16, 16, 16, 16)
            layout_card.setSpacing(12)
            lbl_cat = QLabel(rotulo.upper())
            lbl_cat.setStyleSheet(estilo_titulo_card)
            layout_card.addWidget(lbl_cat)
            lbl_sub = QLabel(subtitulos.get(chave, ""))
            lbl_sub.setStyleSheet(estilo_sub_card)
            layout_card.addWidget(lbl_sub)
            return card

        def _montar_pagina(arquivo_path: str, btn_remover: QPushButton | None) -> tuple[QWidget, QPushButton, QPushButton | None]:
            page = QWidget()
            pl = QVBoxLayout(page)
            pl.setContentsMargins(0, 0, 0, 0)
            pl.setSpacing(10)
            pm = QPixmap(arquivo_path)
            thumb = QLabel()
            thumb.setPixmap(pm.scaled(350, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            thumb.setStyleSheet(estilo_thumb)
            thumb.setAlignment(Qt.AlignCenter)
            pl.addWidget(thumb)
            bv = QPushButton("Visualizar Original em Tamanho Completo")
            bv.setStyleSheet(estilo_btn_visualizar)
            bv.setCursor(Qt.PointingHandCursor)
            bv.clicked.connect(lambda checked, f=arquivo_path: self._abrir_anexo(f))
            pl.addWidget(bv)
            if btn_remover:
                pl.addWidget(btn_remover)
            return page, bv, btn_remover

        def _adicionar_carousel(card_layout: QVBoxLayout, fotos: list) -> None:
            if not fotos:
                return
            stacked = QStackedWidget()
            for ft in fotos:
                page, _, _ = _montar_pagina(ft[0] if isinstance(ft, tuple) else ft.file_path, ft[2] if len(ft) > 2 else None)
                stacked.addWidget(page)
            card_layout.addWidget(stacked, stretch=1)

            nav = QHBoxLayout()
            nav.setSpacing(8)
            btn_prev = QPushButton("◀")
            btn_prev.setStyleSheet(estilo_seta)
            btn_prev.setCursor(Qt.PointingHandCursor)
            btn_next = QPushButton("▶")
            btn_next.setStyleSheet(estilo_seta)
            btn_next.setCursor(Qt.PointingHandCursor)
            contador = QLabel()
            contador.setStyleSheet(estilo_contador)
            contador.setAlignment(Qt.AlignCenter)

            def _atualizar_nav():
                i = stacked.currentIndex()
                total = stacked.count()
                contador.setText(f"{i + 1} / {total}")
                btn_prev.setEnabled(i > 0)
                btn_next.setEnabled(i < total - 1)

            btn_prev.clicked.connect(lambda: (stacked.setCurrentIndex(stacked.currentIndex() - 1), _atualizar_nav()))
            btn_next.clicked.connect(lambda: (stacked.setCurrentIndex(stacked.currentIndex() + 1), _atualizar_nav()))
            _atualizar_nav()

            nav.addWidget(btn_prev)
            nav.addWidget(contador, 1)
            nav.addWidget(btn_next)
            card_layout.addLayout(nav)

        # ── CASO A: Fotos Pendentes (Nova OS) ──────────────────────────────────
        if pending_fotos and activity_id is None:
            for chave, rotulo in categorias.items():
                raw = [(fp, c) for fp, c in pending_fotos if c == chave]
                items = [(fp, c) for fp, c in raw if os.path.exists(fp) and not QPixmap(fp).isNull()]
                if not items:
                    continue
                card = _criar_card(chave, rotulo)
                card_layout_v2 = card.layout()

                fotos_com_botao = []
                for fp, _ in items:
                    def _make_rem(fp=fp, ch=chave):
                        def _handler():
                            dlg = card.window()
                            if hasattr(dlg, 'pending_fotos'):
                                try:
                                    dlg.pending_fotos.remove((fp, ch))
                                except ValueError:
                                    log.exception("Foto %s não estava em pending_fotos", fp)
                            cb = getattr(dlg, 'refresh_gallery_cb', None)
                            if cb:
                                cb()
                        return _handler
                    btn_excluir = QPushButton("🗑️ Excluir Foto")
                    btn_excluir.setStyleSheet(estilo_btn_excluir)
                    btn_excluir.setCursor(Qt.PointingHandCursor)
                    btn_excluir.clicked.connect(_make_rem())
                    fotos_com_botao.append((fp, chave, btn_excluir))

                _adicionar_carousel(card_layout_v2, fotos_com_botao)
                galeria_principal.addWidget(card)

            galeria_scroll.setWidget(galeria_container)
            fotos_layout.addWidget(galeria_scroll)
            return fotos_box, fotos_layout

        # ── CASO B: OS ainda não foi salva (galeria vazia) ─────────────────────
        if not activity_id:
            lbl = QLabel("Adicione fotos da maquina e peças quebradas")
            lbl.setStyleSheet("color: #717182; font-size: 12px; background: transparent;")
            fotos_layout.addWidget(lbl)
            return fotos_box, fotos_layout

        # ── CASO C: Fotos de uma OS Existente ──────────────────────────────────
        anexos = self._listar_anexos(activity_id)
        if not anexos:
            lbl = QLabel("Nenhuma foto anexada.")
            lbl.setStyleSheet("color: #717182; font-size: 12px; background: transparent;")
            fotos_layout.addWidget(lbl)
            return fotos_box, fotos_layout

        for chave, rotulo in categorias.items():
            raw = [a for a in anexos if a.categoria == chave]
            items = [a for a in raw if os.path.exists(a.file_path) and not QPixmap(a.file_path).isNull()]
            if not items:
                continue
            card = _criar_card(chave, rotulo)
            card_layout_v2 = card.layout()

            fotos_com_botao = []
            for a in items:
                def _make_rem_existing(aid=a.id):
                    def _handler():
                        dlg = card.window()
                        self._remover_anexo(aid, dlg)
                        cb = getattr(dlg, 'refresh_gallery_cb', None)
                        if cb:
                            cb()
                    return _handler
                btn_excluir = QPushButton("🗑️ Excluir Foto")
                btn_excluir.setStyleSheet(estilo_btn_excluir)
                btn_excluir.setCursor(Qt.PointingHandCursor)
                btn_excluir.clicked.connect(_make_rem_existing())
                fotos_com_botao.append((a.file_path, chave, btn_excluir))

            _adicionar_carousel(card_layout_v2, fotos_com_botao)
            galeria_principal.addWidget(card)

        fotos_layout.addWidget(galeria_scroll)
        return fotos_box, fotos_layout

    def _abrir_detalhes_por_id(self, activity_id: int) -> None:
        """Abre o dialog de detalhes de uma OS pelo ID."""
        for i, a in enumerate(self._atividades):
            if a.id == activity_id:
                self._detalhes(i)
                return
        atv = self.activity_service.buscar_por_id(activity_id)
        if atv:
            self._atividades.append(atv)
            self._detalhes(len(self._atividades) - 1)

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
        urg_val = getattr(atividade, 'urgencia', '') or 'Normal'
        cor_urg = URGENCIA_CORES.get(urg_val, "#717182")
        urg_lbl = campo_readonly(urg_val)
        urg_lbl.setStyleSheet(
            f"color: {cor_urg}; font-size: 13px; font-weight: 600; background: transparent; border: none; padding: 0;"
        )
        detalhes_form.addRow(campo_rotulo("Urgência"), urg_lbl)
        detalhes_layout.addLayout(detalhes_form)
        layout.addWidget(detalhes_box)

        # ── OS VINCULADA ────────────────────────────────────────────────
        tem_vinculo = bool(atividade.os_vinculada_id)
        tem_filhas = bool(atividade.oses_filhas)
        if tem_vinculo or tem_filhas:
            vinculo_box, vinculo_layout = group_box("Vínculos")
            vinculo_layout.setSpacing(6)
            if tem_vinculo:
                vinc = self.activity_service.buscar_por_id(atividade.os_vinculada_id)
                if vinc:
                    btn_ver = QPushButton(f"🔗 OS #{vinc.id} — {formatar_data_hora(vinc.event_at)} — {(vinc.notes or '')[:60]}")
                    btn_ver.setToolTip("Clique para ver a OS vinculada")
                    btn_ver.setCursor(Qt.PointingHandCursor)
                    btn_ver.setStyleSheet(
                        "QPushButton { background: transparent; color: #818cf8; border: 1px solid #2a2a3e;"
                        " border-radius: 6px; padding: 6px 12px; text-align: left; font-size: 12px; }"
                        "QPushButton:hover { background: rgba(99, 102, 241, 0.1); border-color: #6366f1; }"
                    )
                    def _ver_pai(checked=False, aid=vinc.id):
                        self._abrir_detalhes_por_id(aid)
                    btn_ver.clicked.connect(_ver_pai)
                    vinculo_layout.addWidget(btn_ver)
            if tem_filhas:
                for child in atividade.oses_filhas[:10]:
                    btn_child = QPushButton(f"📋 OS #{child.id} — {formatar_data_hora(child.event_at)} — {(child.notes or '')[:60]}")
                    btn_child.setToolTip("Clique para ver esta OS")
                    btn_child.setCursor(Qt.PointingHandCursor)
                    btn_child.setStyleSheet(
                        "QPushButton { background: transparent; color: #a78bfa; border: 1px solid #2a2a3e;"
                        " border-radius: 6px; padding: 6px 12px; text-align: left; font-size: 12px; }"
                        "QPushButton:hover { background: rgba(167, 139, 250, 0.1); border-color: #a78bfa; }"
                    )
                    def _ver_child(checked=False, cid=child.id):
                        self._abrir_detalhes_por_id(cid)
                    btn_child.clicked.connect(_ver_child)
                    vinculo_layout.addWidget(btn_child)
            layout.addWidget(vinculo_box)

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

        fotos_box, _ = self._criar_grupo_fotos(atividade.id)
        layout.addWidget(fotos_box)

        # ── Peças Reservadas ──
        reservas = self.part_service.reservas_por_os(atividade.id)
        if reservas:
            res_box, res_layout = group_box("Peças Reservadas")
            res_tabela = QTableWidget()
            res_tabela.setColumnCount(4)
            res_tabela.setHorizontalHeaderLabels(["Peça", "Qtd", "Status", "Data"])
            res_tabela.setStyleSheet(ESTILO_TABELA_SIMPLES)
            res_tabela.setSelectionBehavior(QTableWidget.SelectRows)
            res_tabela.setEditTriggers(QTableWidget.NoEditTriggers)
            res_tabela.verticalHeader().setVisible(False)
            res_tabela.setAlternatingRowColors(True)
            res_tabela.verticalHeader().setDefaultSectionSize(28)
            tornar_interativa(res_tabela)
            for i, r in enumerate(reservas):
                res_tabela.setItem(i, 0, QTableWidgetItem(r.part.nome if r.part else "-"))
                item_q = QTableWidgetItem(str(r.quantidade))
                item_q.setTextAlignment(Qt.AlignCenter)
                res_tabela.setItem(i, 1, item_q)
                res_tabela.setItem(i, 2, QTableWidgetItem(r.status))
                res_tabela.setItem(i, 3, QTableWidgetItem(formatar_data_hora(r.created_at)))
            res_layout.addWidget(res_tabela)
            layout.addWidget(res_box)

        layout.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(24, 12, 24, 24)
        btn_layout.setSpacing(10)

        btn_editar = QPushButton("✏️  Editar")
        btn_editar.setStyleSheet(ESTILO_BOTAO_AVISO)
        btn_editar.setToolTip("Editar esta ordem de serviço")

        btn_excluir = QPushButton("🗑️ Excluir")
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_excluir.setToolTip("Excluir esta ordem de serviço (pode ser desfeito pela Lixeira)")

        pode_concluir = atividade.status_atividade not in ("Concluido", "Verificada")
        btn_concluir = QPushButton("✅ Concluir OS")
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
        botoes.setContentsMargins(24, 12, 24, 24)
        botoes.setSpacing(10)

        def _btn(texto: str, estilo: str, tooltip: str) -> QPushButton:
            btn = QPushButton(texto)
            btn.setStyleSheet(estilo)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.PointingHandCursor)
            return btn

        btn_salvar = _btn("Salvar", ESTILO_BOTAO_SUCESSO, "Salvar alterações da ordem de serviço")
        btn_excluir = _btn("Excluir", ESTILO_BOTAO_ERRO, "Excluir esta ordem de serviço (pode ser desfeito pela Lixeira)")
        btn_cancelar = _btn("Cancelar", ESTILO_BOTAO_FECHAR, "Descartar alterações e fechar")
        botoes.addWidget(btn_salvar)
        botoes.addWidget(btn_excluir)
        botoes.addStretch()
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
            urgencia = campos["urgencia"].currentText()
            from_company_id = self._resolver_empresa(from_location)
            to_company_id = self._resolver_empresa(to_location)
            tecnico_id = self._resolver_tecnico(campos["tecnico"].currentText().strip())
            inicio_qdt = campos["inicio"].dateTime()
            fim_qdt = campos["fim"].dateTime()
            inicio_atendimento = inicio_qdt.toPython() if inicio_qdt.isValid() else None
            fim_atendimento = fim_qdt.toPython() if fim_qdt.isValid() else None
            os_vinculada_id = campos["os_vinculada"].currentData()

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
                        urgencia=urgencia,
                        from_company_id=from_company_id,
                        to_company_id=to_company_id,
                        tecnico_id=tecnico_id,
                        procedimentos=procedimentos,
                        os_vinculada_id=os_vinculada_id,
                    )
                    self._dar_baixa_estoque(parts_used, activity_id=atividade.id)
                resultado["acao"] = "salvar"
                dialog.accept()
                self.recarregar()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")

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
        dialog.setMinimumSize(800, 690)
        dialog.setStyleSheet(ESTILO_DIALOG)

        outer = QVBoxLayout(dialog)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: transparent; }
            QTabBar::tab {
                padding: 10px 24px; color: #a0a0b0; font-size: 13px; font-weight: 600;
                border: none; border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected { color: #818cf8; border-bottom: 2px solid #818cf8; }
            QTabBar::tab:hover { color: #e2e8f0; }
        """)

        tab1_scroll = QScrollArea()
        tab1_scroll.setWidgetResizable(True)
        tab1_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tab1_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        tab1_container = QWidget()
        tab1_container.setStyleSheet("background: transparent;")
        content = QVBoxLayout(tab1_container)
        content.setContentsMargins(24, 20, 24, 20)
        content.setSpacing(16)

        # ── EQUIPAMENTO ───────────────────────────────────────────────────────
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
        if cmb_tipo.completer():
            cmb_tipo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        cmb_tipo.addItems(["MANUTENCAO", "MOVIMENTACAO"])

        cmb_tecnico = QComboBox()
        cmb_tecnico.setEditable(True)
        configurar_combo(cmb_tecnico)
        if cmb_tecnico.completer():
            cmb_tecnico.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        if self.technician_service:
            cmb_tecnico.addItems(self.technician_service.nomes_exibicao())
        cmb_tecnico.setInsertPolicy(QComboBox.NoInsert)

        equip_box, equip_layout = group_box("EQUIPAMENTO")
        equip_grid = QGridLayout()
        equip_grid.setSpacing(8)
        equip_grid.setHorizontalSpacing(16)
        equip_grid.addWidget(input_label("IMPRESSORA"), 0, 0)
        equip_grid.addWidget(cmb_printer, 1, 0)
        equip_grid.addWidget(input_label("TIPO"), 0, 1)
        equip_grid.addWidget(cmb_tipo, 1, 1)
        equip_grid.addWidget(input_label("TÉCNICO"), 0, 2)
        equip_grid.addWidget(cmb_tecnico, 1, 2)
        equip_grid.setColumnStretch(0, 1)
        equip_grid.setColumnStretch(1, 1)
        equip_grid.setColumnStretch(2, 1)
        equip_layout.addLayout(equip_grid)
        content.addWidget(equip_box)

        # ── AGENDAMENTO ───────────────────────────────────────────────────────
        from PySide6.QtCore import QDateTime
        edt_data = QDateTimeEdit(QDateTime.currentDateTime())
        edt_data.setCalendarPopup(True)
        edt_data.setDisplayFormat("dd/MM/yyyy HH:mm")
        edt_data.setStyleSheet(ESTILO_INPUT)

        cmb_status = QComboBox()
        configurar_combo(cmb_status)
        if cmb_status.completer():
            cmb_status.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        cmb_status.addItems(STATUS_ATIVIDADE_OPCOES)
        configurar_combo_colorido(cmb_status, ATIVIDADE_CORES)

        cmb_urgencia = QComboBox()
        configurar_combo(cmb_urgencia)
        if cmb_urgencia.completer():
            cmb_urgencia.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        cmb_urgencia.addItems(URGENCIAS)
        configurar_combo_colorido(cmb_urgencia, URGENCIA_CORES)

        edt_inicio = QDateTimeEdit()
        edt_inicio.setCalendarPopup(True)
        edt_inicio.setDisplayFormat("dd/MM/yyyy HH:mm")
        edt_inicio.setStyleSheet(ESTILO_INPUT)
        edt_inicio.setDateTime(QDateTime.currentDateTime())

        edt_fim = QDateTimeEdit()
        edt_fim.setCalendarPopup(True)
        edt_fim.setDisplayFormat("dd/MM/yyyy HH:mm")
        edt_fim.setStyleSheet(ESTILO_INPUT)

        agend_box, agend_layout = group_box("AGENDAMENTO")
        agend_grid = QGridLayout()
        agend_grid.setSpacing(8)
        agend_grid.setHorizontalSpacing(16)
        agend_grid.addWidget(input_label("DATA/HORA AGENDA."), 0, 0)
        agend_grid.addWidget(edt_data, 1, 0)
        agend_grid.addWidget(input_label("STATUS"), 0, 1)
        agend_grid.addWidget(cmb_status, 1, 1)
        agend_grid.addWidget(input_label("URGÊNCIA"), 0, 2)
        agend_grid.addWidget(cmb_urgencia, 1, 2)
        agend_grid.addWidget(input_label("INÍCIO ATENDIMENTO"), 2, 0)
        agend_grid.addWidget(edt_inicio, 3, 0)
        agend_grid.addWidget(input_label("FIM ATENDIMENTO"), 2, 1)
        agend_grid.addWidget(edt_fim, 3, 1)
        agend_grid.setColumnStretch(0, 1)
        agend_grid.setColumnStretch(1, 1)
        agend_grid.setColumnStretch(2, 1)
        agend_layout.addLayout(agend_grid)
        content.addWidget(agend_box)

        # ── DETALHES TÉCNICOS ─────────────────────────────────────────────────
        txt_sintoma = QTextEdit()
        txt_sintoma.setStyleSheet(ESTILO_INPUT)
        txt_sintoma.setFixedHeight(72)
        txt_sintoma.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        txt_diagnostico = QTextEdit()
        txt_diagnostico.setStyleSheet(ESTILO_INPUT)
        txt_diagnostico.setFixedHeight(72)
        txt_diagnostico.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        txt_solucao = QTextEdit()
        txt_solucao.setStyleSheet(ESTILO_INPUT)
        txt_solucao.setFixedHeight(72)
        txt_solucao.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        txt_descricao = QTextEdit()
        txt_descricao.setStyleSheet(ESTILO_INPUT)
        txt_descricao.setFixedHeight(72)
        txt_descricao.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        atend_box, atend_layout = group_box("DETALHES TÉCNICOS")
        atend_form = QFormLayout()
        atend_form.setSpacing(10)
        atend_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        atend_form.addRow(input_label("Sintoma Relatado"), txt_sintoma)
        atend_form.addRow(input_label("Diagnóstico Técnico"), txt_diagnostico)
        atend_form.addRow(input_label("Solução Aplicada"), txt_solucao)
        atend_form.addRow(input_label("Descrição"), txt_descricao)
        atend_layout.addLayout(atend_form)
        content.addWidget(atend_box)

        # ── SEÇÃO INFERIOR DIVIDIDA (Peças vs Checklist) ──────────────────────
        colunas_layout = QHBoxLayout()
        colunas_layout.setSpacing(20)

        pecas_box, pecas_layout = group_box("PEÇAS E ESTOQUE")
        txt_pecas = QTextEdit()
        txt_pecas.setStyleSheet(ESTILO_INPUT)
        txt_pecas.setMaximumHeight(80)

        estoque_combo_os = QComboBox()
        configurar_combo(estoque_combo_os)
        if estoque_combo_os.completer():
            estoque_combo_os.completer().setFilterMode(Qt.MatchFlag.MatchContains)
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
                log.exception("Erro ao preencher peças no combo OS")
        estoque_combo_os.currentIndexChanged.connect(_preencher_pecas_os)

        pecas_grid = QVBoxLayout()
        pecas_grid.setSpacing(6)
        pecas_grid.addWidget(input_label("PEÇAS TROCADAS"))
        pecas_grid.addWidget(txt_pecas)
        pecas_grid.addWidget(input_label("ADICIONAR DO ESTOQUE"))
        pecas_grid.addWidget(estoque_combo_os)

        if atividade:
            btn_reservar_edit = QPushButton("📌 Reservar Peça")
            btn_reservar_edit.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
            def _reservar_edit():
                idx = estoque_combo_os.currentIndex()
                if idx <= 0:
                    return
                pid = estoque_combo_os.currentData()
                if pid is None:
                    return
                with tratar_erro("reservar peça"):
                    res = self.part_service.criar_reserva(pid, atividade.id, quantidade=1)
                    if res:
                        ToastManager.mostrar(f"Peça reservada para OS #{atividade.id}.", "sucesso")
                        _atualizar_reservas_edit()
                        estoque_combo_os.setCurrentIndex(0)
                        self.recarregar()
                    else:
                        ToastManager.mostrar("Estoque insuficiente para reservar.", "erro")
            btn_reservar_edit.clicked.connect(_reservar_edit)
            pecas_grid.addWidget(btn_reservar_edit)

            # ── Reservas na edição ──
            reservas_edit_tabela = QTableWidget()
            reservas_edit_tabela.setColumnCount(4)
            reservas_edit_tabela.setHorizontalHeaderLabels(["Peça", "Qtd", "Status", ""])
            reservas_edit_tabela.setStyleSheet(ESTILO_TABELA_SIMPLES)
            reservas_edit_tabela.setSelectionBehavior(QTableWidget.SelectRows)
            reservas_edit_tabela.setEditTriggers(QTableWidget.NoEditTriggers)
            reservas_edit_tabela.verticalHeader().setVisible(False)
            reservas_edit_tabela.setAlternatingRowColors(True)
            reservas_edit_tabela.verticalHeader().setDefaultSectionSize(26)
            tornar_interativa(reservas_edit_tabela)
            reservas_edit_tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            reservas_edit_tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            reservas_edit_tabela.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            def _cancelar_reserva_edit(res_id: int):
                with tratar_erro("cancelar reserva"):
                    self.part_service.cancelar_reserva(res_id)
                    ToastManager.mostrar("Reserva cancelada. Estoque restaurado.", "sucesso")
                    _atualizar_reservas_edit()
                    self.recarregar()
            def _atualizar_reservas_edit():
                reservas = self.part_service.reservas_por_os(atividade.id)
                reservas_edit_tabela.setRowCount(len(reservas))
                for i, r in enumerate(reservas):
                    reservas_edit_tabela.setItem(i, 0, QTableWidgetItem(r.part.nome if r.part else "-"))
                    item_q = QTableWidgetItem(str(r.quantidade))
                    item_q.setTextAlignment(Qt.AlignCenter)
                    reservas_edit_tabela.setItem(i, 1, item_q)
                    reservas_edit_tabela.setItem(i, 2, QTableWidgetItem(r.status))
                    if r.status == "reservada":
                        btn_cancel = QPushButton("✕")
                        btn_cancel.setFixedSize(24, 24)
                        btn_cancel.setStyleSheet("color: #ef4444; font-size: 12px; background: transparent; border: none;")
                        btn_cancel.setToolTip("Cancelar reserva")
                        btn_cancel.clicked.connect(lambda _, rid=r.id: _cancelar_reserva_edit(rid))
                        reservas_edit_tabela.setCellWidget(i, 3, btn_cancel)
            _atualizar_reservas_edit()
            pecas_grid.addWidget(reservas_edit_tabela)

        pecas_layout.addLayout(pecas_grid)

        checklist_box, checklist_layout = group_box("CHECKLIST")
        tbl = QTableWidget()
        tbl.setColumnCount(2)
        tbl.setHorizontalHeaderLabels(["Feito", "Procedimento"])
        tornar_interativa(tbl)
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tbl.verticalHeader().setVisible(False)
        tbl.verticalHeader().setDefaultSectionSize(32)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        tbl.setStyleSheet("""
            QTableWidget { background: transparent; border: none; }
            QTableWidget::item { padding: 4px; color: #e2e8f0; font-size: 13px; }
            QHeaderView::section { background: transparent; color: #a0a0b0; border: none; font-weight: 600; padding: 4px; }
            QTableWidget QLineEdit {
                background-color: #1e1e2f !important;
                color: #ffffff !important;
                border: 1px solid #3b82f6 !important;
                border-radius: 4px;
                padding: 2px 6px !important;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px; height: 18px;
                border: 2px solid #3b82f6; border-radius: 4px;
                background-color: #1e1e2f;
            }
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
            }
        """)
        itens_padrao = ["Limpeza de laser", "Lubrificação do fusor", "Troca de película", "Troca de rolo de pressão", "Teste de impressão"]
        for nome in itens_padrao:
            r = tbl.rowCount()
            tbl.insertRow(r)
            chk = QTableWidgetItem()
            chk.setFlags(chk.flags() | Qt.ItemIsUserCheckable)
            chk.setCheckState(Qt.Unchecked)
            tbl.setItem(r, 0, chk)
            tbl.setItem(r, 1, QTableWidgetItem(nome))
        tbl.setMinimumHeight(120)
        tbl.setMaximumHeight(140)

        btn_add = QPushButton("+ Adicionar")
        btn_add.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_rem = QPushButton("— Remover")
        btn_rem.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_rem.setCursor(Qt.PointingHandCursor)

        def _add_procedimento():
            r = tbl.rowCount()
            tbl.insertRow(r)
            chk = QTableWidgetItem()
            chk.setFlags(chk.flags() | Qt.ItemIsUserCheckable)
            chk.setCheckState(Qt.Unchecked)
            tbl.setItem(r, 0, chk)
            item_texto = QTableWidgetItem("")
            tbl.setItem(r, 1, item_texto)
            tbl.setCurrentCell(r, 1)
            tbl.editItem(item_texto)

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

        checklist_grid = QVBoxLayout()
        checklist_grid.setSpacing(6)
        checklist_grid.addWidget(tbl)
        checklist_grid.addLayout(btn_row)
        checklist_layout.addLayout(checklist_grid)

        colunas_layout.addWidget(pecas_box, stretch=1)
        colunas_layout.addWidget(checklist_box, stretch=1)
        content.addLayout(colunas_layout)

        # ── MOVIMENTAÇÃO (Condicional) ────────────────────────────────────────
        empresas = self.company_service.listar_nomes() if self.company_service else []

        cmb_origem = QComboBox()
        cmb_origem.setEditable(True)
        configurar_combo(cmb_origem)
        if cmb_origem.completer():
            cmb_origem.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        cmb_origem.addItems(empresas)
        cmb_origem.setInsertPolicy(QComboBox.NoInsert)
        cmb_origem.setCurrentText("")

        cmb_destino = QComboBox()
        cmb_destino.setEditable(True)
        configurar_combo(cmb_destino)
        if cmb_destino.completer():
            cmb_destino.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        cmb_destino.addItems(empresas)
        cmb_destino.setInsertPolicy(QComboBox.NoInsert)
        cmb_destino.setCurrentText("")

        mov_box, mov_layout = group_box("MOVIMENTAÇÃO")
        mov_grid = QGridLayout()
        mov_grid.setSpacing(8)
        mov_grid.setHorizontalSpacing(16)
        mov_grid.addWidget(input_label("ORIGEM"), 0, 0)
        mov_grid.addWidget(cmb_origem, 1, 0)
        mov_grid.addWidget(input_label("DESTINO"), 0, 1)
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

        # ── OS VINCULADA ──────────────────────────────────────────────────
        vinculo_box, vinculo_layout = group_box("OS VINCULADA")
        vinculo_form = QFormLayout()
        vinculo_form.setSpacing(8)
        vinculo_form.setLabelAlignment(Qt.AlignRight)

        cmb_os_vinculada = QComboBox()
        configurar_combo(cmb_os_vinculada)
        if cmb_os_vinculada.completer():
            cmb_os_vinculada.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        cmb_os_vinculada.addItem("-- Nenhuma --", None)
        cmb_os_vinculada.setToolTip("Vincular a uma OS anterior com problema semelhante")

        def _atualizar_vinculo_candidatas(patrimonio: str):
            prt = self.printer_service.buscar_por_patrimonio(patrimonio)
            if not prt:
                cmb_os_vinculada.clear()
                cmb_os_vinculada.addItem("-- Nenhuma --", None)
                return
            excluir_id = atividade.id if atividade else None
            candidatas = self.activity_service.listar_candidatas_vinculo(prt.id, excluir_id=excluir_id)
            cmb_os_vinculada.blockSignals(True)
            cmb_os_vinculada.clear()
            cmb_os_vinculada.addItem("-- Nenhuma --", None)
            for c in candidatas:
                label = f"#{c.id} - {formatar_data_hora(c.event_at)} - {(c.notes or '')[:50]}"
                cmb_os_vinculada.addItem(label, c.id)
            cmb_os_vinculada.blockSignals(False)

        cmb_printer.currentTextChanged.connect(_atualizar_vinculo_candidatas)

        vinculo_form.addRow("Vinculada a:", cmb_os_vinculada)
        vinculo_layout.addLayout(vinculo_form)
        content.addWidget(vinculo_box)

        # ── FIM ABA 1 ──
        content.addStretch()
        tab1_scroll.setWidget(tab1_container)
        tabs.addTab(tab1_scroll, "📋 Dados da OS")

        # ── ABA 2: GALERIA / FOTOS ──────────────────────────────────────
        tab2_scroll = QScrollArea()
        tab2_scroll.setWidgetResizable(True)
        tab2_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tab2_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        tab2_container = QWidget()
        tab2_container.setStyleSheet("background: transparent;")
        fotos_content = QVBoxLayout(tab2_container)
        fotos_content.setContentsMargins(24, 20, 24, 20)
        fotos_content.setSpacing(16)

        # ── Upload fixo no topo ──
        upload_layout = QHBoxLayout()
        upload_layout.setSpacing(8)
        cmb_categoria = QComboBox()
        configurar_combo(cmb_categoria)
        cmb_categoria.addItems(["antes", "depois", "peca"])
        cmb_categoria.setMinimumWidth(140)

        def _do_upload_edit():
            self._anexar_arquivo(atividade.id, cmb_categoria.currentText(), dialog)
            _atualizar_galeria()

        btn_upload = QPushButton("📷 Adicionar Foto")
        btn_upload.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_upload.setToolTip("Selecionar imagem para anexar à OS")
        btn_upload.setCursor(Qt.PointingHandCursor)

        if atividade:
            btn_upload.clicked.connect(_do_upload_edit)
        else:
            dialog.pending_fotos = []
            def _abrir_pendente(_categoria):
                path, _ = QFileDialog.getOpenFileName(
                    dialog, "Selecionar Arquivo", "", "Imagens (*.png *.jpg *.jpeg *.bmp);;Todos (*.*)"
                )
                if path:
                    dialog.pending_fotos.append((path, _categoria))
                    _atualizar_galeria()
            btn_upload.clicked.connect(
                lambda: _abrir_pendente(cmb_categoria.currentText())
            )

        upload_layout.addWidget(cmb_categoria)
        upload_layout.addWidget(btn_upload)
        upload_layout.addStretch()
        fotos_content.addLayout(upload_layout)

        # ── Galeria abaixo ──
        def _atualizar_galeria():
            old = dialog._fotos_box if hasattr(dialog, '_fotos_box') else None
            idx = fotos_content.indexOf(old) if old else 0
            if old:
                fotos_content.removeWidget(old)
                old.deleteLater()
            pending = getattr(dialog, 'pending_fotos', None) if not atividade else None
            dialog._fotos_box, _ = self._criar_grupo_fotos(
                atividade.id if atividade else None,
                pending_fotos=pending,
            )
            fotos_content.insertWidget(idx if idx >= 0 else 0, dialog._fotos_box)

        dialog.refresh_gallery_cb = _atualizar_galeria
        _atualizar_galeria()

        fotos_content.addStretch()
        tab2_scroll.setWidget(tab2_container)
        tabs.addTab(tab2_scroll, "📸 Galeria / Fotos")

        outer.addWidget(tabs, stretch=1)

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
            "urgencia": cmb_urgencia,
            "checklist": tbl,
            "os_vinculada": cmb_os_vinculada,
        }

        def _toggle_campos_conclusao(status_text: str) -> None:
            bloq = status_text in ("Aberta", "Aguardando Peça", "Técnico Designado", "Em Deslocamento")
            edt_fim.setEnabled(not bloq)
            txt_solucao.setEnabled(not bloq)
            txt_descricao.setEnabled(not bloq)
            txt_pecas.setEnabled(not bloq)
            estoque_combo_os.setEnabled(not bloq)
        cmb_status.currentTextChanged.connect(_toggle_campos_conclusao)

        if atividade:
            self._preencher_campos(atividade, campos)

        _toggle_campos_conclusao(cmb_status.currentText())

        if not atividade:
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(24, 12, 24, 24)
            btn_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
            btn_box.button(QDialogButtonBox.Save).setText("Salvar")
            btn_box.button(QDialogButtonBox.Save).setStyleSheet(ESTILO_BOTAO_SUCESSO)
            btn_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
            btn_box.button(QDialogButtonBox.Cancel).setStyleSheet(ESTILO_BOTAO_FECHAR)
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

        if atividade.os_vinculada_id:
            vinc = self.activity_service.buscar_por_id(atividade.os_vinculada_id)
            if vinc:
                idx = campos["os_vinculada"].findData(vinc.id)
                if idx >= 0:
                    campos["os_vinculada"].setCurrentIndex(idx)

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

        idx_st = campos["status"].findText(atividade.status_atividade or "Aberta",
                                           Qt.MatchFixedString)
        if idx_st >= 0:
            campos["status"].setCurrentIndex(idx_st)

        urgencia = getattr(atividade, 'urgencia', '')
        if urgencia in URGENCIAS:
            idx_urg = campos["urgencia"].findText(urgencia)
            if idx_urg >= 0:
                campos["urgencia"].setCurrentIndex(idx_urg)

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

    def _dar_baixa_estoque(self, pecas_texto: str, activity_id: int | None = None) -> None:
        if not pecas_texto:
            return
        with tratar_erro("dar baixa no estoque"):
            self.part_service.retirar_estoque_por_nome(pecas_texto, activity_id=activity_id)

    def _criar_alerta_urgencia(self, printer: Any, urgencia: str) -> None:
        if not self.alert_service or urgencia not in ("Alta", "Crítica"):
            return
        from app.models import Alert
        existente = self.alert_service.session.query(Alert).filter(
            Alert.printer_id == printer.id,
            Alert.tipo == "urgencia",
            Alert.resolvido == False
        ).first()
        if existente:
            return
        try:
            self.alert_service.criar(
                printer_id=printer.id,
                tipo="urgencia",
                titulo=f"OS urgente: {printer.patrimonio}",
                descricao=f"Ordem de serviço com urgência {urgencia} criada para {printer.patrimonio} ({printer.modelo or ''}).",
            )
        except Exception as e:
            log.warning("Erro ao criar alerta de urgência: %s", e)
