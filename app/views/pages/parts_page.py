from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIntValidator
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.utils.ui_helpers import tratar_erro
from app.utils.validacao import ValidadorCampo, obrigatorio
from app.views.styles.theme import (
    COR,
    ESTILO_BOTAO_AVISO,
    ESTILO_BOTAO_ERRO,
    ESTILO_BOTAO_FECHAR,
    ESTILO_BOTAO_PRIMARIO,
    ESTILO_BOTAO_SECUNDARIO,
    ESTILO_BOTAO_SUCESSO,
    ESTILO_SUBTITULO,
    ESTILO_TABELA_SIMPLES,
    campo_readonly,
    campo_rotulo,
    configurar_combo,
    ESTILO_DIALOG,
    ESTILO_INPUT,
    ESTILO_INPUT_READONLY,
    ESTILO_TITULO_PAGINA,
    group_box,
    input_label,
)
from app.views.widgets import ToastManager
from app.views.widgets.card_widget import CardMiniWidget
from app.views.widgets.confirm_dialog import ConfirmacaoDigitarDialog
from app.views.widgets.import_dialog import ImportDialog
from app.views.widgets.pagination import PaginacaoWidget
from app.views.widgets.search_bar import SearchBar
from app.views.widgets.table_widget import TabelaPadrao


class PartsPage(QWidget):
    abrir_atividade: Signal = Signal(int)

    session: Any
    part_service: Any
    printer_service: Any
    activity_service: Any | None
    _filtro_atual: str | None
    _partes_visiveis: list[Any]
    search: SearchBar
    btn_nova: QPushButton
    card_total: CardMiniWidget
    card_em_estoque: CardMiniWidget
    card_sem_estoque: CardMiniWidget
    tabela: TabelaPadrao
    _paginacao: PaginacaoWidget

    def __init__(self, session: Any, part_service: Any, printer_service: Any, activity_service: Any | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        self.part_service = part_service
        self.printer_service = printer_service
        self.activity_service = activity_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(10)

        titulo = QLabel("\U0001f527 Peças")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        sub = QLabel("Gerencie o estoque de peças")
        sub.setStyleSheet(ESTILO_SUBTITULO)

        titulo_col = QVBoxLayout()
        titulo_col.setSpacing(2)
        titulo_col.addWidget(titulo)
        titulo_col.addWidget(sub)
        header.addLayout(titulo_col)
        header.addStretch()

        self.search = SearchBar(placeholder="Buscar por nome, código ou modelo...", glass=True)
        self.search.textChanged().connect(lambda texto: self._filtrar(texto))
        header.addWidget(self.search)

        self.btn_nova = QPushButton("\u2795 Nova Peça")
        self.btn_nova.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
        self.btn_nova.setToolTip("Cadastrar nova peça no estoque")
        self.btn_nova.clicked.connect(self._nova)
        header.addWidget(self.btn_nova)

        btn_importar = QPushButton("  Importar")
        btn_importar.setStyleSheet(ESTILO_BOTAO_AVISO)
        btn_importar.setToolTip("Importar peças de arquivo CSV ou XLSX")
        btn_importar.clicked.connect(lambda: self._importar())
        header.addWidget(btn_importar)

        layout.addLayout(header)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.card_total = CardMiniWidget("\U0001f4e6", "Total Peças", "0", COR["roxo"])
        cards.addWidget(self.card_total)
        self.card_em_estoque = CardMiniWidget("\u2705", "Em Estoque", "0", COR["sucesso"])
        cards.addWidget(self.card_em_estoque)
        self.card_sem_estoque = CardMiniWidget("\u274c", "Sem Estoque", "0", COR["erro"])
        cards.addWidget(self.card_sem_estoque)
        layout.addLayout(cards)

        self._filtro_atual = None
        self._partes_visiveis = []
        self.tabela = TabelaPadrao(["Código", "Nome", "Descrição", "Modelo Compatível", "Estoque", "Mín."])
        self.tabela.cellDoubleClicked.connect(self._detalhes)
        layout.addWidget(self.tabela)

        self._paginacao = PaginacaoWidget()
        self._paginacao.pagina_alterada.connect(lambda p: self._carregar())
        layout.addWidget(self._paginacao)

        self._carregar()

    def recarregar(self) -> None:
        self._filtro_atual = None
        self._carregar()

    def _carregar(self) -> None:
        filtro = self._filtro_atual
        pecas = self.part_service.listar_todas(filtro=filtro, limite=self._paginacao.limit, offset=self._paginacao.offset)
        total = self.part_service.contar(filtro=filtro)
        self._paginacao.configurar(total, pagina_atual=self._paginacao.pagina,
                                   itens_por_pagina=self._paginacao.limit)

        self._partes_visiveis = pecas
        self.tabela.limpar()
        self.tabela.setRowCount(len(pecas))

        soma_estoque = 0
        sem_estoque = 0

        for i, p in enumerate(pecas):
            items = [
                (p.codigo, None),
                (p.nome, None),
                (p.descricao, None),
                (p.modelo_compativel, None),
                (str(p.quantidade_estoque), None),
                (str(p.estoque_minimo), None),
            ]
            for j, (texto, _) in enumerate(items):
                item = QTableWidgetItem(texto)
                item.setTextAlignment(Qt.AlignCenter if j >= 4 else Qt.AlignLeft)
                self.tabela.setItem(i, j, item)

            qtd = p.quantidade_estoque
            soma_estoque += qtd
            if qtd <= 0:
                sem_estoque += 1

            if qtd >= p.estoque_minimo:
                cor = COR["status_ok"]
            elif qtd > 0:
                cor = COR["status_alerta"]
            else:
                cor = COR["status_ruim"]

            self.tabela.item(i, 4).setForeground(QColor(cor))
            self.tabela.item(i, 4).setTextAlignment(Qt.AlignCenter)
            self.tabela.item(i, 5).setTextAlignment(Qt.AlignCenter)
            if qtd < p.estoque_minimo:
                self.tabela.item(i, 5).setForeground(QColor("#fb923c"))

        self.tabela.redimensionar()
        self.card_total.atualizar_valor(total)
        self.card_em_estoque.atualizar_valor(soma_estoque)
        self.card_sem_estoque.atualizar_valor(sem_estoque)

    def _filtrar(self, texto: str) -> None:
        self._filtro_atual = texto if texto else None
        self._carregar()

    def _nova(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Nova Peça")
        dialog.setStyleSheet(ESTILO_DIALOG)
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        codigo = self.part_service.gerar_codigo()

        id_box, id_layout = group_box("Identificação")
        form_id = QFormLayout()
        form_id.setLabelAlignment(Qt.AlignRight)
        form_id.setSpacing(8)

        edit_codigo = QLineEdit(codigo)
        edit_codigo.setStyleSheet(ESTILO_INPUT_READONLY)
        edit_codigo.setReadOnly(True)
        form_id.addRow("Código:", edit_codigo)

        edit_nome = QLineEdit()
        edit_nome.setStyleSheet(ESTILO_INPUT)
        edit_nome.setMaxLength(150)
        edit_nome.setPlaceholderText("* Obrigatório")
        form_id.addRow("Nome:", edit_nome)

        edit_descricao = QLineEdit()
        edit_descricao.setStyleSheet(ESTILO_INPUT)
        form_id.addRow("Descrição:", edit_descricao)

        combo_modelo = QComboBox()
        configurar_combo(combo_modelo)
        cmp = combo_modelo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        combo_modelo.setEditable(True)
        combo_modelo.setInsertPolicy(QComboBox.NoInsert)
        modelos = self.printer_service.modelos_distintos()
        combo_modelo.addItems(modelos)
        form_id.addRow("Modelo Compatível:", combo_modelo)

        id_layout.addLayout(form_id)
        layout.addWidget(id_box)

        est_box, est_layout = group_box("Estoque")
        form_est = QFormLayout()
        form_est.setLabelAlignment(Qt.AlignRight)
        form_est.setSpacing(8)

        edit_qtd = QLineEdit("0")
        edit_qtd.setStyleSheet(ESTILO_INPUT)
        edit_qtd.setValidator(QIntValidator(0, 999999, edit_qtd))
        form_est.addRow("Quantidade:", edit_qtd)

        edit_minimo = QLineEdit("1")
        edit_minimo.setStyleSheet(ESTILO_INPUT)
        edit_minimo.setValidator(QIntValidator(0, 999999, edit_minimo))
        form_est.addRow("Estoque Mín.:", edit_minimo)

        est_layout.addLayout(form_est)
        layout.addWidget(est_box)

        botoes = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botoes.button(QDialogButtonBox.Save).setText("Salvar")
        botoes.button(QDialogButtonBox.Save).setStyleSheet(ESTILO_BOTAO_SUCESSO)
        botoes.button(QDialogButtonBox.Save).setToolTip("Salvar nova peça")
        botoes.button(QDialogButtonBox.Cancel).setStyleSheet(ESTILO_BOTAO_FECHAR)
        botoes.button(QDialogButtonBox.Cancel).setToolTip("Cancelar")
        layout.addWidget(botoes)

        botoes.accepted.connect(lambda: self._salvar_nova(dialog, codigo, edit_nome, edit_descricao, combo_modelo, edit_qtd, edit_minimo))
        botoes.rejected.connect(dialog.reject)

        dialog.exec()

    def _salvar_nova(self, dialog: QDialog, codigo: str, edit_nome: QLineEdit, edit_descricao: QLineEdit, combo_modelo: QComboBox, edit_qtd: QLineEdit, edit_minimo: QLineEdit) -> None:
        nome = edit_nome.text().strip()
        if not nome:
            QMessageBox.warning(dialog, "Aviso", "O campo Nome é obrigatório.")
            return
        descricao = edit_descricao.text().strip()
        modelo = combo_modelo.currentText().strip()
        try:
            quantidade = int(edit_qtd.text().strip())
        except ValueError:
            quantidade = 0
        try:
            estoque_minimo = int(edit_minimo.text().strip())
        except ValueError:
            estoque_minimo = 1
        with tratar_erro("criar peça"):
            self.part_service.criar(codigo=codigo, nome=nome, descricao=descricao, modelo_compativel=modelo, quantidade=quantidade, estoque_minimo=estoque_minimo)
            dialog.accept()
            self.recarregar()

    def _abrir_edicao(self, peca, parent_dialog: QDialog | None = None) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Peça")
        dialog.setStyleSheet(ESTILO_DIALOG)
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        id_box, id_layout = group_box("Identificação")
        form_id = QFormLayout()
        form_id.setLabelAlignment(Qt.AlignRight)
        form_id.setSpacing(8)

        edit_codigo = QLineEdit(peca.codigo)
        edit_codigo.setStyleSheet(ESTILO_INPUT_READONLY)
        edit_codigo.setReadOnly(True)
        form_id.addRow("Código:", edit_codigo)

        edit_nome = QLineEdit(peca.nome)
        edit_nome.setStyleSheet(ESTILO_INPUT)
        edit_nome.setMaxLength(150)
        form_id.addRow("Nome:", edit_nome)

        erro_nome = QLabel()
        erro_nome.setStyleSheet("color: #ef4444; font-size: 10px; background: transparent;")
        erro_nome.hide()
        form_id.addRow("", erro_nome)
        ValidadorCampo(edit_nome, obrigatorio, erro_nome)

        edit_descricao = QLineEdit(peca.descricao)
        edit_descricao.setStyleSheet(ESTILO_INPUT)
        form_id.addRow("Descrição:", edit_descricao)

        combo_modelo = QComboBox()
        configurar_combo(combo_modelo)
        cmp = combo_modelo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        combo_modelo.setEditable(True)
        combo_modelo.setInsertPolicy(QComboBox.NoInsert)
        modelos = self.printer_service.modelos_distintos()
        combo_modelo.addItems(modelos)
        if peca.modelo_compativel:
            idx = combo_modelo.findText(peca.modelo_compativel)
            if idx >= 0:
                combo_modelo.setCurrentIndex(idx)
            else:
                combo_modelo.setCurrentText(peca.modelo_compativel)
        form_id.addRow("Modelo Compatível:", combo_modelo)

        id_layout.addLayout(form_id)
        layout.addWidget(id_box)

        est_box, est_layout = group_box("Estoque")
        form_est = QFormLayout()
        form_est.setLabelAlignment(Qt.AlignRight)
        form_est.setSpacing(8)

        edit_qtd = QLineEdit(str(peca.quantidade_estoque))
        edit_qtd.setStyleSheet(ESTILO_INPUT)
        edit_qtd.setValidator(QIntValidator(0, 999999, edit_qtd))
        form_est.addRow("Quantidade:", edit_qtd)

        edit_minimo = QLineEdit(str(peca.estoque_minimo))
        edit_minimo.setStyleSheet(ESTILO_INPUT)
        edit_minimo.setValidator(QIntValidator(0, 999999, edit_minimo))
        form_est.addRow("Estoque Mín.:", edit_minimo)

        est_layout.addLayout(form_est)
        layout.addWidget(est_box)

        botoes = QDialogButtonBox()
        btn_salvar = botoes.addButton("Salvar", QDialogButtonBox.AcceptRole)
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_salvar.setToolTip("Salvar alterações da peça")
        btn_cancelar = botoes.addButton("Cancelar", QDialogButtonBox.RejectRole)
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_cancelar.setToolTip("Descartar alterações e fechar")
        layout.addWidget(botoes)

        def salvar():
            nome = edit_nome.text().strip()
            descricao = edit_descricao.text().strip()
            modelo = combo_modelo.currentText().strip()
            try:
                quantidade = int(edit_qtd.text().strip())
            except ValueError:
                quantidade = 0
            try:
                estoque_minimo = int(edit_minimo.text().strip())
            except ValueError:
                estoque_minimo = 1
            with tratar_erro("atualizar peça"):
                self.part_service.atualizar(peca, nome=nome, descricao=descricao, modelo_compativel=modelo, quantidade_estoque=quantidade, estoque_minimo=estoque_minimo)
                dialog.accept()
                if parent_dialog:
                    parent_dialog.accept()
                idx = next((i for i, p in enumerate(self._partes_visiveis) if p.id == peca.id), -1)
                if idx >= 0:
                    self._detalhes(idx)
                else:
                    self.recarregar()

        botoes.accepted.connect(salvar)
        botoes.rejected.connect(dialog.reject)

        dialog.exec()

    def _detalhes(self, row: int) -> None:
        if row < 0 or row >= len(self._partes_visiveis):
            return
        peca = self._partes_visiveis[row]

        dialog = QDialog(self)
        dialog.setWindowTitle(peca.nome)
        dialog.setStyleSheet(ESTILO_DIALOG)
        dialog.setMinimumSize(650, 500)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        content = QVBoxLayout(container)
        content.setContentsMargins(24, 20, 24, 20)
        content.setSpacing(20)

        id_box, id_layout = group_box("Identificação")
        id_form = QFormLayout()
        id_form.setLabelAlignment(Qt.AlignRight)
        id_form.setSpacing(8)
        id_form.addRow(campo_rotulo("Código"), campo_readonly(peca.codigo))
        id_form.addRow(campo_rotulo("Nome"), campo_readonly(peca.nome))
        id_form.addRow(campo_rotulo("Descrição"), campo_readonly(peca.descricao))
        id_form.addRow(campo_rotulo("Modelo Compatível"), campo_readonly(peca.modelo_compativel))
        id_layout.addLayout(id_form)
        content.addWidget(id_box)

        est_box, est_layout = group_box("Estoque")
        est_form = QFormLayout()
        est_form.setLabelAlignment(Qt.AlignRight)
        est_form.setSpacing(8)
        est_form.addRow(campo_rotulo("Quantidade"), campo_readonly(str(peca.quantidade_estoque)))
        est_form.addRow(campo_rotulo("Estoque Mín."), campo_readonly(str(peca.estoque_minimo)))
        if peca.quantidade_estoque <= peca.estoque_minimo:
            warn = QLabel("⚠️  Estoque baixo! A quantidade está no ou abaixo do mínimo.")
            warn.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600; background: transparent; padding: 8px 0 0 0;")
            est_layout.addWidget(warn)
        est_layout.addLayout(est_form)
        # ── Receber Estoque ──
        btn_receber = QPushButton("📦 Receber Estoque")
        btn_receber.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_receber.clicked.connect(lambda: self._receber_estoque(peca, dialog))
        est_layout.addWidget(btn_receber)
        content.addWidget(est_box)

        # ── Movimentações Recentes ──
        mov_box, mov_layout = group_box("Movimentações Recentes")
        mov_tabela = QTableWidget()
        mov_tabela.setColumnCount(6)
        mov_tabela.setHorizontalHeaderLabels(["Data/Hora", "Tipo", "Qtd", "Saldo", "Observação", ""])
        mov_tabela.setStyleSheet(ESTILO_TABELA_SIMPLES)
        mov_tabela.setSelectionBehavior(QTableWidget.SelectRows)
        mov_tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        mov_tabela.verticalHeader().setVisible(False)
        mov_tabela.setAlternatingRowColors(True)
        mov_tabela.verticalHeader().setDefaultSectionSize(30)
        h = mov_tabela.horizontalHeader()
        for i in range(5):
            h.setSectionResizeMode(i, QHeaderView.Stretch)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        from app.utils.helpers import formatar_data_hora
        movimentos = self.part_service.movimentacoes(peca.id, limite=20)
        mov_tabela.setRowCount(len(movimentos))
        for i, m in enumerate(movimentos):
            mov_tabela.setItem(i, 0, QTableWidgetItem(formatar_data_hora(m.created_at)))
            mov_tabela.setItem(i, 1, QTableWidgetItem(m.tipo))
            item_qtd = QTableWidgetItem(str(m.quantidade))
            item_qtd.setTextAlignment(Qt.AlignCenter)
            mov_tabela.setItem(i, 2, item_qtd)
            item_saldo = QTableWidgetItem(str(m.saldo_posterior))
            item_saldo.setTextAlignment(Qt.AlignCenter)
            mov_tabela.setItem(i, 3, item_saldo)
            mov_tabela.setItem(i, 4, QTableWidgetItem(m.observacao or ""))
            btn_lixeira = QPushButton("🗑")
            btn_lixeira.setFixedSize(28, 28)
            btn_lixeira.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    font-size: 14px;
                    color: #ef4444;
                }
                QPushButton:hover {
                    background: rgba(239, 68, 68, 0.15);
                    border-radius: 4px;
                }
            """)
            btn_lixeira.setToolTip("Estornar esta movimentação")
            mov_id = m.id
            btn_lixeira.clicked.connect(lambda checked, mid=mov_id: self._estornar_movimento(mid, peca, dialog))
            mov_tabela.setCellWidget(i, 5, btn_lixeira)
        mov_layout.addWidget(mov_tabela)
        content.addWidget(mov_box)

        # ── Requisição de Compra Pendente ──
        reqs = self.part_service.listar_requisicoes(status="pendente", limite=10)
        reqs_desta = [r for r in reqs if r.part_id == peca.id]
        if reqs_desta:
            req_box, req_layout = group_box("Requisição de Compra Pendente")
            for r in reqs_desta:
                lbl_req = QLabel(f"🛒 #{r.id} — {r.quantidade_sugerida} un. ({r.observacao or ''})")
                lbl_req.setStyleSheet("color: #f59e0b; font-size: 12px; background: transparent; padding: 2px 0;")
                req_layout.addWidget(lbl_req)
            content.addWidget(req_box)

        content.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, stretch=1)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(24, 12, 24, 16)
        btn_layout.setSpacing(10)

        btn_editar = QPushButton("✏️  Editar")
        btn_editar.setStyleSheet(ESTILO_BOTAO_AVISO)
        btn_editar.setToolTip("Editar esta peça")
        btn_editar.clicked.connect(lambda: self._abrir_edicao(peca, dialog))

        btn_excluir = QPushButton("🗑️ Excluir")
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_excluir.setToolTip("Excluir esta peça (pode ser desfeito pela Lixeira)")
        btn_excluir.clicked.connect(lambda: self._confirmar_exclusao(peca, dialog))

        btn_layout.addWidget(btn_editar)
        btn_layout.addWidget(btn_excluir)

        if self.activity_service:
            btn_historico = QPushButton("📋 Histórico de Uso")
            btn_historico.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
            btn_historico.setToolTip("Ver histórico de uso desta peça em ordens de serviço")
            btn_historico.clicked.connect(lambda: self._mostrar_uso(peca))
            btn_layout.addWidget(btn_historico)

        btn_layout.addStretch()

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_fechar.setToolTip("Fechar")
        btn_fechar.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_fechar)

        layout.addLayout(btn_layout)

        dialog.exec()

    def _estornar_movimento(self, movimento_id: int, peca: Any, parent_dialog: QDialog) -> None:
        from app.views.widgets.confirm_dialog import ConfirmacaoDigitarDialog
        resp = ConfirmacaoDigitarDialog.confirmar(
            "Estornar Movimentação",
            f"Tem certeza que deseja estornar esta movimentação?\n\nO estoque da peça \"{peca.nome}\" será ajustado automaticamente.",
            parent=parent_dialog,
            palavra_chave="ESTORNAR",
        )
        if not resp:
            return
        with tratar_erro("estornar movimentação"):
            self.part_service.estornar_movimento(movimento_id)
            ToastManager.mostrar("Movimentação estornada com sucesso!", tipo="sucesso")
            parent_dialog.accept()
            self._detalhes(self._partes_visiveis.index(peca) if peca in self._partes_visiveis else 0)

    def _receber_estoque(self, peca: Any, parent_dialog: QDialog) -> None:
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle(f"Receber Estoque — {peca.nome}")
        dialog.setStyleSheet(ESTILO_DIALOG)
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        lbl = QLabel(f"Estoque atual: <b>{peca.quantidade_estoque}</b> un.  |  Mínimo: <b>{peca.estoque_minimo}</b> un.")
        lbl.setStyleSheet("color: #c8c8e0; font-size: 13px; background: transparent;")
        layout.addWidget(lbl)

        qtd_layout = QFormLayout()
        qtd_spin = QSpinBox()
        qtd_spin.setRange(1, 99999)
        qtd_spin.setValue(1)
        qtd_spin.setStyleSheet(ESTILO_INPUT)
        qtd_layout.addRow(campo_rotulo("Quantidade a receber:"), qtd_spin)
        layout.addLayout(qtd_layout)

        obs_input = QLineEdit()
        obs_input.setStyleSheet(ESTILO_INPUT)
        obs_input.setPlaceholderText("Observação (opcional)")
        layout.addWidget(QLabel("Observação:"))
        layout.addWidget(obs_input)

        botoes = QHBoxLayout()
        btn_confirmar = QPushButton("📦 Receber")
        btn_confirmar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_confirmar.clicked.connect(lambda: self._confirmar_recebimento(peca, qtd_spin, obs_input, dialog, parent_dialog))
        botoes.addWidget(btn_confirmar)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_cancelar.clicked.connect(dialog.reject)
        botoes.addWidget(btn_cancelar)
        layout.addLayout(botoes)

        dialog.exec()

    def _confirmar_recebimento(self, peca: Any, qtd_spin: QSpinBox, obs_input: QLineEdit, dialog: QDialog, parent_dialog: QDialog) -> None:
        qtd = qtd_spin.value()
        obs = obs_input.text().strip()
        with tratar_erro("receber estoque"):
            self.part_service.receber_estoque(peca, qtd, observacao=obs)
            ToastManager.mostrar(f"{qtd} unidade(s) de '{peca.nome}' adicionada(s) ao estoque.", "sucesso")
            dialog.accept()
            parent_dialog.accept()
            self.recarregar()

    def _confirmar_exclusao(self, peca, dialog: QDialog) -> None:
        if ConfirmacaoDigitarDialog.confirmar(
            "Confirmar", f"Excluir a peça '{peca.nome}'?",
            dialog,
        ):
            with tratar_erro("excluir peça"):
                self.part_service.excluir(peca)
                ToastManager.mostrar(
                    f"Peça '{peca.nome}' excluída.",
                    "aviso", duracao=8000,
                    acao=("Desfazer", lambda o=peca, svc=self.part_service, pag=self: (svc.restaurar(o), pag.recarregar())),
                )
                dialog.accept()
                self.recarregar()

    def _mostrar_uso(self, peca: Any) -> None:
        from app.utils.helpers import formatar_data_hora
        diretas, relacionadas = self.activity_service.listar_por_peca_com_relacionadas(peca.nome, limite=200)
        if not diretas:
            QMessageBox.information(self, "Histórico de Uso", f"Nenhum uso encontrado para '{peca.nome}'.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Uso da peça: {peca.nome}")
        dialog.setMinimumSize(780, 500)
        dialog.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        def preencher_tabela(atividades):
            tabela = QTableWidget()
            tabela.setColumnCount(5)
            tabela.setHorizontalHeaderLabels(["Data/Hora", "Tipo", "Impressora", "Origem", "Destino"])
            tabela.horizontalHeader().setStretchLastSection(True)
            tabela.setSelectionBehavior(QTableWidget.SelectRows)
            tabela.setEditTriggers(QTableWidget.NoEditTriggers)
            tabela.setAlternatingRowColors(True)
            tabela.setRowCount(len(atividades))
            tabela.verticalHeader().setVisible(False)
            for i, a in enumerate(atividades):
                pat = a.printer.patrimonio if a.printer else "-"
                tabela.setItem(i, 0, QTableWidgetItem(formatar_data_hora(a.event_at)))
                tabela.setItem(i, 1, QTableWidgetItem("Manutenção" if a.kind == "MANUTENCAO" else "Movimentação"))
                tabela.setItem(i, 2, QTableWidgetItem(pat))
                tabela.setItem(i, 3, QTableWidgetItem(a.from_location or "-"))
                tabela.setItem(i, 4, QTableWidgetItem(a.to_location or "-"))
            tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            tabela.resizeColumnsToContents()
            return tabela

        box, box_layout = group_box("Histórico de Uso")

        box_layout.addWidget(QLabel(f"<b style='font-size:14px'>📌 Uso direto — {len(diretas)} registro(s)</b>"))
        tab_diretas = preencher_tabela(diretas)
        tab_diretas.cellDoubleClicked.connect(lambda r, c: self._abrir_atividade_historico(diretas[r].id, dialog) if r < len(diretas) else None)
        box_layout.addWidget(tab_diretas)

        if relacionadas:
            box_layout.addWidget(QLabel(f"<b style='font-size:14px'>🔗 Outras atividades nas mesmas impressoras — {len(relacionadas)} registro(s)</b>"))
            tab_rel = preencher_tabela(relacionadas)
            tab_rel.cellDoubleClicked.connect(lambda r, c: self._abrir_atividade_historico(relacionadas[r].id, dialog) if r < len(relacionadas) else None)
            box_layout.addWidget(tab_rel)

        layout.addWidget(box)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_fechar.setToolTip("Fechar janela")
        btn_fechar.clicked.connect(dialog.accept)
        layout.addWidget(btn_fechar, alignment=Qt.AlignCenter)

        dialog.exec()

    def _importar(self) -> None:
        dialog: ImportDialog = ImportDialog(self, "parts", "Peças", self.part_service, self.session)
        if dialog.exec() == ImportDialog.Accepted:
            self.recarregar()

    def _abrir_atividade_historico(self, activity_id: int, dialog: QDialog) -> None:
        self.abrir_atividade.emit(activity_id)
