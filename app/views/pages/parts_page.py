from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from app.views.styles.theme import (COR, ESTILO_TITULO_PAGINA, ESTILO_BOTAO_SUCESSO, ESTILO_BOTAO_ERRO, ESTILO_BOTAO_FECHAR, ESTILO_INPUT, ESTILO_COMBO, ESTILO_TABELA, ESTILO_DIALOG, ESTILO_INPUT_READONLY, ESTILO_BOTAO_AVISO)
from app.views.widgets.card_widget import CardMiniWidget
from app.views.widgets.table_widget import TabelaPadrao


class PartsPage(QWidget):
    def __init__(self, session, part_service, printer_service, parent=None):
        super().__init__(parent)
        self.session = session
        self.part_service = part_service
        self.printer_service = printer_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        titulo = QLabel("\U0001f527 Peças / Estoque")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        header.addWidget(titulo)
        header.addStretch()

        self.btn_nova = QPushButton("\u2795 Nova Peça")
        self.btn_nova.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        self.btn_nova.clicked.connect(self._nova)
        header.addWidget(self.btn_nova)
        layout.addLayout(header)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.card_total = CardMiniWidget("\U0001f4e6", "Total Peças", "0", COR["roxo_claro"])
        cards.addWidget(self.card_total)
        self.card_em_estoque = CardMiniWidget("\u2705", "Em Estoque", "0", COR["sucesso"])
        cards.addWidget(self.card_em_estoque)
        self.card_sem_estoque = CardMiniWidget("\u274c", "Sem Estoque", "0", COR["erro"])
        cards.addWidget(self.card_sem_estoque)
        layout.addLayout(cards)

        self.tabela = TabelaPadrao(["Código", "Nome", "Descrição", "Modelo Compatível", "Estoque"])
        self.tabela.cellDoubleClicked.connect(self._editar)
        layout.addWidget(self.tabela)

        self.recarregar()

    def recarregar(self):
        pecas = self.part_service.listar_todas()
        self.tabela.limpar()
        self.tabela.setRowCount(len(pecas))

        total = len(pecas)
        soma_estoque = 0
        sem_estoque = 0

        for i, p in enumerate(pecas):
            items = [
                (p.codigo, None),
                (p.nome, None),
                (p.descricao, None),
                (p.modelo_compativel, None),
                (str(p.quantidade_estoque), None),
            ]
            for j, (texto, _) in enumerate(items):
                item = QTableWidgetItem(texto)
                item.setTextAlignment(Qt.AlignCenter if j == 4 else Qt.AlignLeft)
                self.tabela.setItem(i, j, item)

            qtd = p.quantidade_estoque
            soma_estoque += qtd
            if qtd <= 0:
                sem_estoque += 1

            if qtd > 10:
                cor = COR["status_ok"]
            elif qtd > 0:
                cor = COR["status_alerta"]
            else:
                cor = COR["status_ruim"]

            self.tabela.item(i, 4).setForeground(QColor(cor))
            self.tabela.item(i, 4).setTextAlignment(Qt.AlignCenter)

        self.tabela.redimensionar()

        self.card_total.atualizar_valor(total)
        self.card_em_estoque.atualizar_valor(soma_estoque)
        self.card_sem_estoque.atualizar_valor(sem_estoque)

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
        edit_nome.setPlaceholderText("* Obrigatório")
        form.addRow("Nome:", edit_nome)

        edit_descricao = QLineEdit()
        edit_descricao.setStyleSheet(ESTILO_INPUT)
        form.addRow("Descrição:", edit_descricao)

        combo_modelo = QComboBox()
        combo_modelo.setStyleSheet(ESTILO_COMBO)
        combo_modelo.setEditable(True)
        combo_modelo.setInsertPolicy(QComboBox.NoInsert)
        modelos = self.printer_service.modelos_distintos()
        combo_modelo.addItems(modelos)
        form.addRow("Modelo Compatível:", combo_modelo)

        edit_qtd = QLineEdit("0")
        edit_qtd.setStyleSheet(ESTILO_INPUT)
        form.addRow("Quantidade:", edit_qtd)

        botoes = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botoes.button(QDialogButtonBox.Save).setText("Salvar")
        botoes.button(QDialogButtonBox.Save).setStyleSheet(ESTILO_BOTAO_SUCESSO)
        botoes.button(QDialogButtonBox.Cancel).setStyleSheet(ESTILO_BOTAO_FECHAR)
        form.addRow(botoes)

        botoes.accepted.connect(lambda: self._salvar_nova(dialog, codigo, edit_nome, edit_descricao, combo_modelo, edit_qtd))
        botoes.rejected.connect(dialog.reject)

        dialog.exec()

    def _salvar_nova(self, dialog, codigo, edit_nome, edit_descricao, combo_modelo, edit_qtd):
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
        self.part_service.criar(codigo=codigo, nome=nome, descricao=descricao, modelo_compativel=modelo, quantidade=quantidade)
        dialog.accept()
        self.recarregar()

    def _editar(self, row):
        if row < 0:
            return

        peca = self.part_service.listar_todas()[row]

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
        form.addRow("Nome:", edit_nome)

        edit_descricao = QLineEdit(peca.descricao)
        edit_descricao.setStyleSheet(ESTILO_INPUT)
        form.addRow("Descrição:", edit_descricao)

        edit_qtd = QLineEdit(str(peca.quantidade_estoque))
        edit_qtd.setStyleSheet(ESTILO_INPUT)
        form.addRow("Quantidade:", edit_qtd)

        botoes = QDialogButtonBox()
        btn_salvar = botoes.addButton("Salvar", QDialogButtonBox.AcceptRole)
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_excluir = botoes.addButton("Excluir", QDialogButtonBox.DestructiveRole)
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_cancelar = botoes.addButton("Cancelar", QDialogButtonBox.RejectRole)
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        form.addRow(botoes)

        def salvar():
            nome = edit_nome.text().strip()
            if not nome:
                QMessageBox.warning(dialog, "Aviso", "O campo Nome é obrigatório.")
                return
            descricao = edit_descricao.text().strip()
            try:
                quantidade = int(edit_qtd.text().strip())
            except ValueError:
                quantidade = 0
            self.part_service.atualizar(peca, nome=nome, descricao=descricao, quantidade_estoque=quantidade)
            dialog.accept()
            self.recarregar()

        def excluir():
            resp = QMessageBox.question(
                dialog, "Confirmar", f"Excluir a peça '{peca.nome}'?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if resp == QMessageBox.Yes:
                self.part_service.excluir(peca)
                dialog.accept()
                self.recarregar()

        botoes.accepted.connect(salvar)
        if hasattr(botoes, 'clicked'):
            btn_excluir.clicked.connect(excluir)
        else:
            for btn in botoes.buttons():
                if botoes.buttonRole(btn) == QDialogButtonBox.DestructiveRole:
                    btn.clicked.connect(excluir)

        dialog.exec()
