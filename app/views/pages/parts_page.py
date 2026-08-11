from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIntValidator
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
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
from app.views.widgets.card_widget import CardMiniClicavel
from app.views.widgets.confirm_dialog import ConfirmacaoDigitarDialog
from app.views.widgets.import_dialog import ImportDialog
from app.views.widgets.pagination import PaginacaoWidget
from app.views.widgets.search_bar import SearchBar
from app.views.widgets.table_widget import TabelaPadrao, tornar_interativa


class MultiModelWidget(QWidget):
    """Widget para selecionar multiplos modelos compativeis."""

    def __init__(self, modelos_disponiveis: list[str] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        add_row = QHBoxLayout()
        add_row.setSpacing(6)
        self._combo = QComboBox()
        self._combo.setEditable(True)
        self._combo.setInsertPolicy(QComboBox.NoInsert)
        self._combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self._combo.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._combo.setMinimumWidth(200)
        self._combo.setStyleSheet(
            "QComboBox { background-color: #1e1e2e; color: #e8e8f0;"
            " border: 1px solid #2a2a3e; border-radius: 6px;"
            " padding: 4px 8px; font-size: 12px; min-height: 24px; }"
            "QComboBox:hover { border: 1px solid #6366f1; }"
        )
        if modelos_disponiveis:
            self._combo.addItems(modelos_disponiveis)
        add_row.addWidget(self._combo, stretch=1)

        btn_add = QPushButton("Adicionar")
        btn_add.setFixedHeight(32)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setToolTip("Adicionar modelo selecionado")
        btn_add.setStyleSheet(
            "QPushButton { background: #22c55e; color: white; border: none;"
            " border-radius: 6px; font-size: 12px; font-weight: bold;"
            " font-family: 'Segoe UI', Arial, sans-serif;"
            " padding: 0 14px; }"
            "QPushButton:hover { background: #16a34a; }"
            "QPushButton:pressed { background: #15803d; }"
        )
        btn_add.clicked.connect(self._adicionar)
        add_row.addWidget(btn_add)

        btn_rem = QPushButton("Remover")
        btn_rem.setFixedHeight(32)
        btn_rem.setCursor(Qt.PointingHandCursor)
        btn_rem.setToolTip("Remover modelo selecionado na lista")
        btn_rem.setStyleSheet(
            "QPushButton { background: #ef4444; color: white; border: none;"
            " border-radius: 6px; font-size: 12px; font-weight: bold;"
            " font-family: 'Segoe UI', Arial, sans-serif;"
            " padding: 0 14px; }"
            "QPushButton:hover { background: #dc2626; }"
            "QPushButton:pressed { background: #b91c1c; }"
        )
        btn_rem.clicked.connect(self._remover)
        add_row.addWidget(btn_rem)

        layout.addLayout(add_row)

        self._lista = QListWidget()
        self._lista.setMaximumHeight(100)
        self._lista.setDragDropMode(QListWidget.NoDragDrop)
        self._lista.setStyleSheet(
            "QListWidget { background-color: #1e1e2e; color: #e8e8f0;"
            " border: 1px solid #2a2a3e; border-radius: 6px;"
            " padding: 4px; font-size: 12px; }"
            "QListWidget::item { padding: 4px 8px; border-radius: 4px; margin: 1px 0; }"
            "QListWidget::item:selected { background-color: rgba(99,102,241,0.3); color: #c7d2fe; }"
            "QListWidget::item:hover { background-color: rgba(99,102,241,0.15); }"
        )
        layout.addWidget(self._lista)

        self._lbl_count = QLabel("0 modelo(s)")
        self._lbl_count.setStyleSheet("color: #6c7086; font-size: 11px; background: transparent;")
        layout.addWidget(self._lbl_count)

        le = self._combo.lineEdit()
        if le:
            le.returnPressed.connect(self._adicionar)

    def _adicionar(self) -> None:
        texto = self._combo.currentText().strip()
        if not texto:
            return
        existentes = [self._lista.item(i).text() for i in range(self._lista.count())]
        if texto not in existentes:
            self._lista.addItem(texto)
            self._atualizar_contador()
        self._combo.setCurrentText("")

    def _remover(self) -> None:
        row = self._lista.currentRow()
        if row >= 0:
            self._lista.takeItem(row)
            self._atualizar_contador()

    def _atualizar_contador(self) -> None:
        n = self._lista.count()
        self._lbl_count.setText(f"{n} modelo(s)")

    def modelos(self) -> list[str]:
        return [self._lista.item(i).text() for i in range(self._lista.count())]

    def set_modelos(self, modelos: list[str]) -> None:
        self._lista.clear()
        for m in modelos:
            if m.strip():
                self._lista.addItem(m.strip())
        self._atualizar_contador()

    def modelo_string(self) -> str:
        return "/".join(self.modelos())

    def set_modelo_string(self, texto: str) -> None:
        if not texto:
            self._lista.clear()
            self._atualizar_contador()
            return
        partes = [t.strip() for t in texto.split("/") if t.strip()]
        self.set_modelos(partes)


class PartsPage(QWidget):
    abrir_atividade: Signal = Signal(int)

    session: Any
    part_service: Any
    printer_service: Any
    activity_service: Any | None
    _filtro_atual: str | None
    _card_filtro: str | None
    _partes_visiveis: list[Any]
    search: SearchBar
    btn_nova: QPushButton
    card_total: CardMiniClicavel
    card_em_estoque: CardMiniClicavel
    card_sem_estoque: CardMiniClicavel
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
        self.card_total = CardMiniClicavel("\U0001f4e6", "Total Peças", "0", COR["roxo"], ao_clicar=lambda: self._clicar_card(None))
        cards.addWidget(self.card_total)
        self.card_em_estoque = CardMiniClicavel("\u2705", "Em Estoque", "0", COR["sucesso"], ao_clicar=lambda: self._clicar_card("em_estoque"))
        cards.addWidget(self.card_em_estoque)
        self.card_sem_estoque = CardMiniClicavel("\u274c", "Sem Estoque", "0", COR["erro"], ao_clicar=lambda: self._clicar_card("sem_estoque"))
        cards.addWidget(self.card_sem_estoque)
        layout.addLayout(cards)

        self._filtro_atual = None
        self._card_filtro = None
        self._partes_visiveis = []
        self.tabela = TabelaPadrao(["Código", "Nome", "Marca", "Modelo Compatível", "Categoria", "Estoque", "Mín.", "Fornecedor"])
        self.tabela.cellDoubleClicked.connect(self._detalhes)
        layout.addWidget(self.tabela)

        self._paginacao = PaginacaoWidget()
        self._paginacao.pagina_alterada.connect(lambda p: self._carregar())
        layout.addWidget(self._paginacao)

        self._carregar()

    def recarregar(self) -> None:
        texto = self.search.texto().strip() if hasattr(self, 'search') else ""
        self._filtro_atual = texto if texto else None
        self._card_filtro = None
        self._carregar()

    def _clicar_card(self, card: str | None) -> None:
        if self._card_filtro == card:
            self._card_filtro = None
        else:
            self._card_filtro = card
        self._carregar()

    def _atualizar_estado_cards(self) -> None:
        for card, filtro in [
            (self.card_total, None),
            (self.card_em_estoque, "em_estoque"),
            (self.card_sem_estoque, "sem_estoque"),
        ]:
            ativo = self._card_filtro == filtro
            card.setStyleSheet(
                f"QFrame#miniCard {{ background-color: {'rgba(99,102,241,0.15)' if ativo else 'rgba(20,20,31,0.5)'}; "
                f"border: 1px solid {'#6366f1' if ativo else 'rgba(42,42,62,0.5)'}; border-radius: 12px; padding: 16px; }}"
                f"QFrame#miniCard:hover {{ background-color: {'rgba(99,102,241,0.25)' if ativo else 'rgba(30,30,46,0.6)'}; "
                f"border: 1px solid {'#6366f1' if ativo else 'rgba(42,42,62,0.8)'}; border-radius: 12px; padding: 16px; }}"
            )

    def _carregar(self) -> None:
        filtro = self._filtro_atual
        todas = self.part_service.listar_todas(filtro=filtro)

        total = len(todas)
        em_estoque = sum(1 for p in todas if p.quantidade_estoque > 0)
        sem_estoque = sum(1 for p in todas if p.quantidade_estoque <= 0)
        soma_estoque = sum(p.quantidade_estoque for p in todas)

        self.card_total.atualizar_valor(total)
        self.card_em_estoque.atualizar_valor(soma_estoque)
        self.card_sem_estoque.atualizar_valor(sem_estoque)
        self._atualizar_estado_cards()

        if self._card_filtro == "em_estoque":
            todas = [p for p in todas if p.quantidade_estoque > 0]
        elif self._card_filtro == "sem_estoque":
            todas = [p for p in todas if p.quantidade_estoque <= 0]

        total_filtrado = len(todas)
        self._paginacao.configurar(total_filtrado, pagina_atual=self._paginacao.pagina,
                                   itens_por_pagina=self._paginacao.limit)
        inicio = self._paginacao.offset
        pecas = todas[inicio:inicio + self._paginacao.limit]

        self._partes_visiveis = pecas
        self.tabela.limpar()
        self.tabela.setRowCount(len(pecas))

        for i, p in enumerate(pecas):
            items = [
                (p.codigo, None),
                (p.nome, None),
                (p.marca, None),
                (p.modelo_compativel, None),
                (p.categoria, None),
                (str(p.quantidade_estoque), None),
                (str(p.estoque_minimo), None),
                (p.fornecedor, None),
            ]
            for j, (texto, _) in enumerate(items):
                item = QTableWidgetItem(texto)
                item.setTextAlignment(Qt.AlignCenter if j >= 5 else Qt.AlignLeft)
                self.tabela.setItem(i, j, item)

            qtd = p.quantidade_estoque

            if qtd >= p.estoque_minimo:
                cor = COR["status_ok"]
            elif qtd > 0:
                cor = COR["status_alerta"]
            else:
                cor = COR["status_ruim"]

            self.tabela.item(i, 5).setForeground(QColor(cor))
            self.tabela.item(i, 5).setTextAlignment(Qt.AlignCenter)
            self.tabela.item(i, 6).setTextAlignment(Qt.AlignCenter)
            if qtd < p.estoque_minimo:
                self.tabela.item(i, 6).setForeground(QColor("#fb923c"))

        self.tabela.redimensionar()

    def _filtrar(self, texto: str) -> None:
        self._filtro_atual = texto if texto else None
        self._carregar()

    def _nova(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("\U0001f4e6  Nova Peça")
        dialog.setStyleSheet(ESTILO_DIALOG)
        dialog.setMinimumSize(760, 560)

        root = QVBoxLayout(dialog)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(
            "QFrame { background: rgba(14,14,22,0.8);"
            " border-bottom: 1px solid rgba(42,42,62,0.7); }"
        )
        header.setFixedHeight(56)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 20, 0)
        title_lbl = QLabel("\U0001f4e6  Nova Peça")
        title_lbl.setStyleSheet(
            "color: #e8e8f0; font-size: 15px; font-weight: 700;"
            " background: transparent; border: none;"
        )
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        root.addWidget(header)

        # ── Body com scroll ──────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        content = QVBoxLayout(container)
        content.setContentsMargins(20, 16, 20, 12)
        content.setSpacing(14)

        codigo = self.part_service.gerar_codigo()

        # ── SEÇÃO: Identificação ─────────────────────────
        id_box, id_layout = group_box("Identificação")
        id_grid = QGridLayout()
        id_grid.setSpacing(8)
        id_grid.setHorizontalSpacing(16)

        edit_codigo = QLineEdit(codigo)
        edit_codigo.setStyleSheet(ESTILO_INPUT_READONLY)
        edit_codigo.setReadOnly(True)

        edit_nome = QLineEdit()
        edit_nome.setStyleSheet(ESTILO_INPUT)
        edit_nome.setMaxLength(150)
        edit_nome.setPlaceholderText("* Obrigatório")

        err_nome = QLabel()
        err_nome.setStyleSheet("color: #ef4444; font-size: 9px; background: transparent; padding: 0; margin: 0; border: none;")
        err_nome.hide()
        ValidadorCampo(edit_nome, obrigatorio, err_nome)

        edit_descricao = QTextEdit()
        edit_descricao.setStyleSheet(ESTILO_INPUT)
        edit_descricao.setPlaceholderText("Descrição detalhada da peça...")
        edit_descricao.setFixedHeight(80)

        id_grid.addWidget(input_label("Código"), 0, 0)
        id_grid.addWidget(edit_codigo, 1, 0)
        id_grid.addWidget(input_label("Nome *"), 0, 1)
        id_grid.addWidget(edit_nome, 1, 1)
        id_grid.addWidget(err_nome, 2, 1)
        id_grid.addWidget(input_label("Descrição"), 3, 0, 1, 2)
        id_grid.addWidget(edit_descricao, 4, 0, 1, 2)
        id_grid.setColumnStretch(0, 1)
        id_grid.setColumnStretch(1, 1)
        id_layout.addLayout(id_grid)
        content.addWidget(id_box)

        # ── Multi-modelo (seção inteira dedicada) ────────
        mod_box, mod_layout = group_box("Modelo(s) Compatível(is)")
        multi_modelo = MultiModelWidget(modelos_disponiveis=self.printer_service.modelos_distintos())
        mod_layout.addWidget(multi_modelo)
        content.addWidget(mod_box)

        # ── SEÇÃO: Estoque ───────────────────────────────
        est_box, est_layout = group_box("Estoque")
        est_grid = QGridLayout()
        est_grid.setSpacing(8)
        est_grid.setHorizontalSpacing(16)

        edit_qtd = QLineEdit("0")
        edit_qtd.setStyleSheet(ESTILO_INPUT)
        edit_qtd.setValidator(QIntValidator(0, 999999, edit_qtd))

        edit_minimo = QLineEdit("1")
        edit_minimo.setStyleSheet(ESTILO_INPUT)
        edit_minimo.setValidator(QIntValidator(0, 999999, edit_minimo))

        est_grid.addWidget(input_label("Quantidade"), 0, 0)
        est_grid.addWidget(edit_qtd, 1, 0)
        est_grid.addWidget(input_label("Estoque Mínimo"), 0, 1)
        est_grid.addWidget(edit_minimo, 1, 1)
        est_grid.setColumnStretch(0, 1)
        est_grid.setColumnStretch(1, 1)
        est_layout.addLayout(est_grid)
        content.addWidget(est_box)

        # ── SEÇÃO: Complemento ───────────────────────────
        ext_box, ext_layout = group_box("Complemento")
        ext_grid = QGridLayout()
        ext_grid.setSpacing(8)
        ext_grid.setHorizontalSpacing(16)

        edit_marca = QLineEdit()
        edit_marca.setStyleSheet(ESTILO_INPUT)

        edit_categoria = QLineEdit()
        edit_categoria.setStyleSheet(ESTILO_INPUT)

        edit_fornecedor = QLineEdit()
        edit_fornecedor.setStyleSheet(ESTILO_INPUT)

        ext_grid.addWidget(input_label("Marca"), 0, 0)
        ext_grid.addWidget(edit_marca, 1, 0)
        ext_grid.addWidget(input_label("Categoria"), 0, 1)
        ext_grid.addWidget(edit_categoria, 1, 1)
        ext_grid.addWidget(input_label("Fornecedor"), 2, 0)
        ext_grid.addWidget(edit_fornecedor, 3, 0)
        ext_grid.setColumnStretch(0, 1)
        ext_grid.setColumnStretch(1, 1)
        ext_layout.addLayout(ext_grid)
        content.addWidget(ext_box)

        content.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

        # ── Footer ───────────────────────────────────────
        footer = QFrame()
        footer.setStyleSheet(
            "QFrame { background: rgba(14,14,22,0.6);"
            " border-top: 1px solid rgba(42,42,62,0.7); }"
        )
        footer.setFixedHeight(60)
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(20, 0, 20, 0)
        f_layout.setSpacing(10)

        btn_salvar = QPushButton("\U0001f4be  Salvar")
        btn_salvar.setToolTip("Salvar nova peça")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_salvar.setMinimumWidth(120)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setToolTip("Descartar e fechar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)

        f_layout.addStretch()
        f_layout.addWidget(btn_cancelar)
        f_layout.addWidget(btn_salvar)
        root.addWidget(footer)

        def salvar():
            nome_val = edit_nome.text().strip()
            if not nome_val:
                QMessageBox.warning(dialog, "Aviso", "O campo Nome é obrigatório.")
                return
            desc_val = edit_descricao.toPlainText().strip()
            modelo_val = multi_modelo.modelo_string()
            try:
                qtd_val = int(edit_qtd.text().strip())
            except ValueError:
                qtd_val = 0
            try:
                min_val = int(edit_minimo.text().strip())
            except ValueError:
                min_val = 1
            with tratar_erro("criar peça"):
                self.part_service.criar(
                    codigo=codigo, nome=nome_val, descricao=desc_val,
                    modelo_compativel=modelo_val, quantidade=qtd_val,
                    estoque_minimo=min_val, marca=edit_marca.text().strip(),
                    categoria=edit_categoria.text().strip(),
                    fornecedor=edit_fornecedor.text().strip(),
                )
                dialog.accept()
                self.recarregar()

        btn_salvar.clicked.connect(salvar)
        btn_cancelar.clicked.connect(dialog.reject)

        dialog.exec()

    def _abrir_edicao(self, peca, parent_dialog: QDialog | None = None) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(f"\u270f\ufe0f  Editar \u2014 {peca.nome}")
        dialog.setStyleSheet(ESTILO_DIALOG)
        dialog.setMinimumSize(760, 560)

        root = QVBoxLayout(dialog)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(
            "QFrame { background: rgba(14,14,22,0.8);"
            " border-bottom: 1px solid rgba(42,42,62,0.7); }"
        )
        header.setFixedHeight(56)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 20, 0)
        title_lbl = QLabel(f"\u270f\ufe0f  Editar Peça")
        title_lbl.setStyleSheet(
            "color: #e8e8f0; font-size: 15px; font-weight: 700;"
            " background: transparent; border: none;"
        )
        h_layout.addWidget(title_lbl)
        badge = QLabel(peca.codigo)
        badge.setStyleSheet(
            "color: #6366f1; font-size: 11px; font-weight: 600;"
            " background: rgba(99,102,241,0.1);"
            " border: 1px solid rgba(99,102,241,0.3);"
            " border-radius: 6px; padding: 3px 10px;"
        )
        h_layout.addWidget(badge)
        h_layout.addStretch()
        root.addWidget(header)

        # ── Body com scroll ──────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        content = QVBoxLayout(container)
        content.setContentsMargins(20, 16, 20, 12)
        content.setSpacing(14)

        # ── SEÇÃO: Identificação ─────────────────────────
        id_box, id_layout = group_box("Identificação")
        id_grid = QGridLayout()
        id_grid.setSpacing(8)
        id_grid.setHorizontalSpacing(16)

        edit_codigo = QLineEdit(peca.codigo)
        edit_codigo.setStyleSheet(ESTILO_INPUT_READONLY)
        edit_codigo.setReadOnly(True)

        edit_nome = QLineEdit(peca.nome)
        edit_nome.setStyleSheet(ESTILO_INPUT)
        edit_nome.setMaxLength(150)

        err_nome = QLabel()
        err_nome.setStyleSheet("color: #ef4444; font-size: 9px; background: transparent; padding: 0; margin: 0; border: none;")
        err_nome.hide()
        ValidadorCampo(edit_nome, obrigatorio, err_nome)

        edit_descricao = QTextEdit()
        edit_descricao.setStyleSheet(ESTILO_INPUT)
        edit_descricao.setPlaceholderText("Descrição detalhada da peça...")
        edit_descricao.setFixedHeight(80)
        edit_descricao.setPlainText(peca.descricao or "")

        id_grid.addWidget(input_label("Código"), 0, 0)
        id_grid.addWidget(edit_codigo, 1, 0)
        id_grid.addWidget(input_label("Nome *"), 0, 1)
        id_grid.addWidget(edit_nome, 1, 1)
        id_grid.addWidget(err_nome, 2, 1)
        id_grid.addWidget(input_label("Descrição"), 3, 0, 1, 2)
        id_grid.addWidget(edit_descricao, 4, 0, 1, 2)
        id_grid.setColumnStretch(0, 1)
        id_grid.setColumnStretch(1, 1)
        id_layout.addLayout(id_grid)
        content.addWidget(id_box)

        # ── Multi-modelo ────────────────────────────────
        mod_box, mod_layout = group_box("Modelo(s) Compatível(is)")
        multi_modelo = MultiModelWidget(modelos_disponiveis=self.printer_service.modelos_distintos())
        multi_modelo.set_modelo_string(peca.modelo_compativel or "")
        mod_layout.addWidget(multi_modelo)
        content.addWidget(mod_box)

        # ── SEÇÃO: Estoque ───────────────────────────────
        est_box, est_layout = group_box("Estoque")
        est_grid = QGridLayout()
        est_grid.setSpacing(8)
        est_grid.setHorizontalSpacing(16)

        edit_qtd = QLineEdit(str(peca.quantidade_estoque))
        edit_qtd.setStyleSheet(ESTILO_INPUT)
        edit_qtd.setValidator(QIntValidator(0, 999999, edit_qtd))

        edit_minimo = QLineEdit(str(peca.estoque_minimo))
        edit_minimo.setStyleSheet(ESTILO_INPUT)
        edit_minimo.setValidator(QIntValidator(0, 999999, edit_minimo))

        est_grid.addWidget(input_label("Quantidade"), 0, 0)
        est_grid.addWidget(edit_qtd, 1, 0)
        est_grid.addWidget(input_label("Estoque Mínimo"), 0, 1)
        est_grid.addWidget(edit_minimo, 1, 1)
        est_grid.setColumnStretch(0, 1)
        est_grid.setColumnStretch(1, 1)
        est_layout.addLayout(est_grid)
        content.addWidget(est_box)

        # ── SEÇÃO: Complemento ───────────────────────────
        ext_box, ext_layout = group_box("Complemento")
        ext_grid = QGridLayout()
        ext_grid.setSpacing(8)
        ext_grid.setHorizontalSpacing(16)

        edit_marca = QLineEdit(peca.marca or "")
        edit_marca.setStyleSheet(ESTILO_INPUT)

        edit_categoria = QLineEdit(peca.categoria or "")
        edit_categoria.setStyleSheet(ESTILO_INPUT)

        edit_fornecedor = QLineEdit(peca.fornecedor or "")
        edit_fornecedor.setStyleSheet(ESTILO_INPUT)

        ext_grid.addWidget(input_label("Marca"), 0, 0)
        ext_grid.addWidget(edit_marca, 1, 0)
        ext_grid.addWidget(input_label("Categoria"), 0, 1)
        ext_grid.addWidget(edit_categoria, 1, 1)
        ext_grid.addWidget(input_label("Fornecedor"), 2, 0)
        ext_grid.addWidget(edit_fornecedor, 3, 0)
        ext_grid.setColumnStretch(0, 1)
        ext_grid.setColumnStretch(1, 1)
        ext_layout.addLayout(ext_grid)
        content.addWidget(ext_box)

        content.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

        # ── Footer ───────────────────────────────────────
        footer = QFrame()
        footer.setStyleSheet(
            "QFrame { background: rgba(14,14,22,0.6);"
            " border-top: 1px solid rgba(42,42,62,0.7); }"
        )
        footer.setFixedHeight(60)
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(20, 0, 20, 0)
        f_layout.setSpacing(10)

        btn_salvar = QPushButton("\U0001f4be  Salvar")
        btn_salvar.setToolTip("Salvar alterações")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_salvar.setMinimumWidth(120)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setToolTip("Descartar e fechar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)

        f_layout.addStretch()
        f_layout.addWidget(btn_cancelar)
        f_layout.addWidget(btn_salvar)
        root.addWidget(footer)

        def salvar():
            nome_val = edit_nome.text().strip()
            desc_val = edit_descricao.toPlainText().strip()
            modelo_val = multi_modelo.modelo_string()
            try:
                qtd_val = int(edit_qtd.text().strip())
            except ValueError:
                qtd_val = 0
            try:
                min_val = int(edit_minimo.text().strip())
            except ValueError:
                min_val = 1
            with tratar_erro("atualizar peça"):
                self.part_service.atualizar(
                    peca, nome=nome_val, descricao=desc_val,
                    modelo_compativel=modelo_val, quantidade_estoque=qtd_val,
                    estoque_minimo=min_val, marca=edit_marca.text().strip(),
                    categoria=edit_categoria.text().strip(),
                    fornecedor=edit_fornecedor.text().strip(),
                )
                dialog.accept()
                if parent_dialog:
                    parent_dialog.accept()
                idx = next((i for i, p in enumerate(self._partes_visiveis) if p.id == peca.id), -1)
                if idx >= 0:
                    self._detalhes(idx)
                else:
                    self.recarregar()

        btn_salvar.clicked.connect(salvar)
        btn_cancelar.clicked.connect(dialog.reject)

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
        modelos = [m.strip() for m in (peca.modelo_compativel or "").split("/") if m.strip()]
        if modelos:
            tags_layout = QHBoxLayout()
            tags_layout.setSpacing(4)
            for m in modelos:
                tag = QLabel(m)
                tag.setStyleSheet(
                    "QLabel { background: rgba(99,102,241,0.2); color: #c7d2fe;"
                    " border: 1px solid #6366f1; border-radius: 8px;"
                    " padding: 3px 10px; font-size: 11px; }"
                )
                tag.setFixedHeight(24)
                tags_layout.addWidget(tag)
            tags_layout.addStretch()
            id_form.addRow(campo_rotulo("Modelos"), tags_layout)
        else:
            id_form.addRow(campo_rotulo("Modelos"), campo_readonly(""))
        id_form.addRow(campo_rotulo("Marca"), campo_readonly(peca.marca or ""))
        id_form.addRow(campo_rotulo("Categoria"), campo_readonly(peca.categoria or ""))
        id_form.addRow(campo_rotulo("Fornecedor"), campo_readonly(peca.fornecedor or ""))
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
        tornar_interativa(mov_tabela)
        mov_tabela.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
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
            tornar_interativa(tabela)
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
