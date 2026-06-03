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
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.utils.ui_helpers import tratar_erro
from app.views.styles.theme import (
    COR,
    ESTILO_BOTAO_AVISO,
    ESTILO_BOTAO_ERRO,
    ESTILO_BOTAO_FECHAR,
    ESTILO_BOTAO_PRIMARIO,
    ESTILO_BOTAO_SUCESSO,
    ESTILO_SUBTITULO,
    configurar_combo,
    ESTILO_DIALOG,
    ESTILO_INPUT,
    ESTILO_INPUT_READONLY,
    ESTILO_TITULO_PAGINA,
)
from app.views.widgets.card_widget import CardMiniWidget
from app.views.widgets.import_dialog import ImportDialog
from app.views.widgets.pagination import PaginacaoWidget
from app.views.widgets.search_bar import SearchBar
from app.views.widgets.table_widget import TabelaPadrao


class PartsPage(QWidget):
    abrir_atividade = Signal(int)

    def __init__(self, session, part_service, printer_service, activity_service=None, parent=None):
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
        self.btn_nova.clicked.connect(self._nova)
        header.addWidget(self.btn_nova)

        btn_importar = QPushButton("  Importar")
        btn_importar.setStyleSheet(ESTILO_BOTAO_AVISO)
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
        self.tabela.cellDoubleClicked.connect(self._editar)
        layout.addWidget(self.tabela)

        self._paginacao = PaginacaoWidget()
        self._paginacao.pagina_alterada.connect(lambda p: self._carregar())
        layout.addWidget(self._paginacao)

        self._carregar()

    def recarregar(self):
        self._filtro_atual = None
        self._carregar()

    def _carregar(self):
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

    def _filtrar(self, texto):
        self._filtro_atual = texto if texto else None
        self._carregar()

    def _nova(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nova Peça")
        dialog.setStyleSheet(ESTILO_DIALOG)
        dialog.setMinimumWidth(400)

        form = QFormLayout(dialog)
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(12)
        form.setContentsMargins(20, 20, 20, 20)

        codigo = self.part_service.gerar_codigo()

        edit_codigo = QLineEdit(codigo)
        edit_codigo.setStyleSheet(ESTILO_INPUT_READONLY)
        edit_codigo.setReadOnly(True)
        form.addRow("Código:", edit_codigo)

        edit_nome = QLineEdit()
        edit_nome.setStyleSheet(ESTILO_INPUT)
        edit_nome.setMaxLength(150)
        edit_nome.setPlaceholderText("* Obrigatório")
        form.addRow("Nome:", edit_nome)

        edit_descricao = QLineEdit()
        edit_descricao.setStyleSheet(ESTILO_INPUT)
        form.addRow("Descrição:", edit_descricao)

        combo_modelo = QComboBox()
        configurar_combo(combo_modelo)
        combo_modelo.setEditable(True)
        combo_modelo.setInsertPolicy(QComboBox.NoInsert)
        modelos = self.printer_service.modelos_distintos()
        combo_modelo.addItems(modelos)
        form.addRow("Modelo Compatível:", combo_modelo)

        edit_qtd = QLineEdit("0")
        edit_qtd.setStyleSheet(ESTILO_INPUT)
        edit_qtd.setValidator(QIntValidator(0, 999999, edit_qtd))
        form.addRow("Quantidade:", edit_qtd)

        edit_minimo = QLineEdit("1")
        edit_minimo.setStyleSheet(ESTILO_INPUT)
        edit_minimo.setValidator(QIntValidator(0, 999999, edit_minimo))
        form.addRow("Estoque Mín.:", edit_minimo)

        botoes = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botoes.button(QDialogButtonBox.Save).setText("Salvar")
        botoes.button(QDialogButtonBox.Save).setStyleSheet(ESTILO_BOTAO_SUCESSO)
        botoes.button(QDialogButtonBox.Cancel).setStyleSheet(ESTILO_BOTAO_FECHAR)
        form.addRow(botoes)

        botoes.accepted.connect(lambda: self._salvar_nova(dialog, codigo, edit_nome, edit_descricao, combo_modelo, edit_qtd, edit_minimo))
        botoes.rejected.connect(dialog.reject)

        dialog.exec()

    def _salvar_nova(self, dialog, codigo, edit_nome, edit_descricao, combo_modelo, edit_qtd, edit_minimo):
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

    def _editar(self, row):
        if row < 0 or row >= len(self._partes_visiveis):
            return

        peca = self._partes_visiveis[row]

        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Peça")
        dialog.setStyleSheet(ESTILO_DIALOG)
        dialog.setMinimumWidth(400)

        form = QFormLayout(dialog)
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(12)
        form.setContentsMargins(20, 20, 20, 20)

        edit_codigo = QLineEdit(peca.codigo)
        edit_codigo.setStyleSheet(ESTILO_INPUT_READONLY)
        edit_codigo.setReadOnly(True)
        form.addRow("Código:", edit_codigo)

        edit_nome = QLineEdit(peca.nome)
        edit_nome.setStyleSheet(ESTILO_INPUT)
        edit_nome.setMaxLength(150)
        form.addRow("Nome:", edit_nome)

        edit_descricao = QLineEdit(peca.descricao)
        edit_descricao.setStyleSheet(ESTILO_INPUT)
        form.addRow("Descrição:", edit_descricao)

        combo_modelo = QComboBox()
        configurar_combo(combo_modelo)
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
        form.addRow("Modelo Compatível:", combo_modelo)

        edit_qtd = QLineEdit(str(peca.quantidade_estoque))
        edit_qtd.setStyleSheet(ESTILO_INPUT)
        edit_qtd.setValidator(QIntValidator(0, 999999, edit_qtd))
        form.addRow("Quantidade:", edit_qtd)

        edit_minimo = QLineEdit(str(peca.estoque_minimo))
        edit_minimo.setStyleSheet(ESTILO_INPUT)
        edit_minimo.setValidator(QIntValidator(0, 999999, edit_minimo))
        form.addRow("Estoque Mín.:", edit_minimo)

        botoes = QDialogButtonBox()
        btn_salvar = botoes.addButton("Salvar", QDialogButtonBox.AcceptRole)
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_excluir = botoes.addButton("Excluir", QDialogButtonBox.DestructiveRole)
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_cancelar = botoes.addButton("Cancelar", QDialogButtonBox.RejectRole)
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        if self.activity_service:
            btn_historico = botoes.addButton("📋 Histórico de Uso", QDialogButtonBox.ActionRole)
            btn_historico.setStyleSheet(ESTILO_BOTAO_AVISO)
            btn_historico.clicked.connect(lambda: self._mostrar_uso(peca))
        form.addRow(botoes)

        def salvar():
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
            with tratar_erro("atualizar peça"):
                self.part_service.atualizar(peca, nome=nome, descricao=descricao, modelo_compativel=modelo, quantidade_estoque=quantidade, estoque_minimo=estoque_minimo)
                dialog.accept()
                self.recarregar()

        def excluir():
            resp = QMessageBox.question(
                dialog, "Confirmar", f"Excluir a peça '{peca.nome}'?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if resp == QMessageBox.Yes:
                with tratar_erro("excluir peça"):
                    self.part_service.excluir(peca)
                    dialog.accept()
                    self.recarregar()

        botoes.accepted.connect(salvar)
        botoes.rejected.connect(dialog.reject)
        btn_excluir.clicked.connect(excluir)

        dialog.exec()

    def _mostrar_uso(self, peca):
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

        layout.addWidget(QLabel(f"<b style='font-size:14px'>📌 Uso direto — {len(diretas)} registro(s)</b>"))
        tab_diretas = preencher_tabela(diretas)
        tab_diretas.cellDoubleClicked.connect(lambda r, c: self._abrir_atividade_historico(diretas[r].id, dialog))
        layout.addWidget(tab_diretas)

        if relacionadas:
            layout.addWidget(QLabel(f"<b style='font-size:14px'>🔗 Outras atividades nas mesmas impressoras — {len(relacionadas)} registro(s)</b>"))
            tab_rel = preencher_tabela(relacionadas)
            tab_rel.cellDoubleClicked.connect(lambda r, c: self._abrir_atividade_historico(relacionadas[r].id, dialog))
            layout.addWidget(tab_rel)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_fechar.clicked.connect(dialog.accept)
        layout.addWidget(btn_fechar, alignment=Qt.AlignCenter)

        dialog.exec()

    def _importar(self):
        dialog = ImportDialog(self, "parts", "Peças", self.part_service, self.session)
        if dialog.exec() == ImportDialog.Accepted:
            self.recarregar()

    def _abrir_atividade_historico(self, activity_id, dialog):
        self.abrir_atividade.emit(activity_id)
