from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
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
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models import Printer
from app.views.styles.theme import (
    COR,
    ESTILO_BOTAO_ERRO,
    ESTILO_BOTAO_FECHAR,
    ESTILO_BOTAO_SUCESSO,
    ESTILO_COMBO,
    ESTILO_DIALOG,
    ESTILO_INPUT,
    ESTILO_LABEL_CAMPO,
    ESTILO_TABELA_SIMPLES,
    ESTILO_TITULO_PAGINA,
    estilos_dialogo_tabs,
)
from app.views.widgets.table_widget import TabelaPadrao


class ClientsPage(QWidget):
    abrir_impressora = Signal(str)

    def __init__(self, session, company_service, printer_service, parent=None):
        super().__init__(parent)
        self.session = session
        self.company_service = company_service
        self.printer_service = printer_service
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QHBoxLayout()
        titulo = QLabel("\U0001f465 Clientes / Empresas")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        header.addWidget(titulo)
        header.addStretch()

        btn_nova = QPushButton("\u2795 Nova Empresa")
        btn_nova.setCursor(Qt.PointingHandCursor)
        btn_nova.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_nova.clicked.connect(self._nova)
        header.addWidget(btn_nova)

        layout.addLayout(header)
        layout.addSpacing(10)

        self.tabela = TabelaPadrao(["Nome", "CNPJ", "Cidade/UF", "Telefone", "Email", "Impressoras"])
        self.tabela.cellDoubleClicked.connect(self._editar)
        layout.addWidget(self.tabela)

    def recarregar(self):
        empresas = self.company_service.listar_todas()
        self.tabela.setRowCount(len(empresas))
        for i, emp in enumerate(empresas):
            self.tabela.setItem(i, 0, QTableWidgetItem(emp.nome))
            self.tabela.setItem(i, 1, QTableWidgetItem(emp.cnpj or "-"))
            cidade_uf = f"{emp.cidade or ''}/{emp.uf or ''}".strip("/")
            self.tabela.setItem(i, 2, QTableWidgetItem(cidade_uf if cidade_uf else "-"))
            self.tabela.setItem(i, 3, QTableWidgetItem(emp.telefone or "-"))
            self.tabela.setItem(i, 4, QTableWidgetItem(emp.email or "-"))
            num = self.printer_service.contar_por_local(emp.nome)
            self.tabela.setItem(i, 5, QTableWidgetItem(str(num)))
        self.tabela.redimensionar()

    def _nova(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nova Empresa")
        dialog.setFixedSize(400, 300)
        dialog.setStyleSheet(ESTILO_DIALOG + ESTILO_INPUT + ESTILO_COMBO)

        layout = QFormLayout(dialog)
        layout.setSpacing(8)

        nome_input = QLineEdit()
        nome_input.setPlaceholderText("Nome da empresa")
        layout.addRow("Nome:", nome_input)

        cnpj_input = QLineEdit()
        cnpj_input.setPlaceholderText("00.000.000/0000-00")
        layout.addRow("CNPJ:", cnpj_input)

        telefone_input = QLineEdit()
        telefone_input.setPlaceholderText("(00) 00000-0000")
        layout.addRow("Telefone:", telefone_input)

        email_input = QLineEdit()
        email_input.setPlaceholderText("email@empresa.com")
        layout.addRow("Email:", email_input)

        tipo_input = QComboBox()
        tipo_input.addItems(["Cliente", "Filial", "Parceiro"])
        layout.addRow("Tipo:", tipo_input)

        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.accepted.connect(lambda: self._salvar_nova(dialog, nome_input, cnpj_input, telefone_input, email_input, tipo_input))
        botoes.rejected.connect(dialog.reject)
        layout.addRow(botoes)

        dialog.exec()

    def _salvar_nova(self, dialog, nome, cnpj, telefone, email, tipo):
        nome_text = nome.text().strip()
        if not nome_text:
            return
        self.company_service.criar(
            nome=nome_text,
            cnpj=cnpj.text().strip(),
            telefone=telefone.text().strip(),
            email=email.text().strip(),
            tipo=tipo.currentText()
        )
        self.recarregar()
        dialog.accept()

    def _editar(self, row):
        nome_empresa = self.tabela.item(row, 0).text()
        empresa = self.company_service.buscar_por_nome(nome_empresa)

        if not empresa:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"\u270f\ufe0f Editar Empresa: {empresa.nome}")
        dialog.setMinimumSize(600, 500)
        dialog.setStyleSheet(ESTILO_DIALOG + ESTILO_INPUT + ESTILO_COMBO + ESTILO_TABELA_SIMPLES + estilos_dialogo_tabs())

        tabs = QTabWidget()

        tab_dados = QWidget()
        form = QFormLayout(tab_dados)
        form.setSpacing(8)

        nome_input = QLineEdit(empresa.nome or "")
        form.addRow("Nome:", nome_input)

        cnpj_input = QLineEdit(empresa.cnpj or "")
        cnpj_input.setPlaceholderText("00.000.000/0000-00")
        form.addRow("CNPJ:", cnpj_input)

        tipo_combo = QComboBox()
        tipo_combo.addItems(["Cliente", "Filial", "Parceiro"])
        tipo_combo.setCurrentText(empresa.tipo or "Cliente")
        form.addRow("Tipo:", tipo_combo)

        tel_input = QLineEdit(empresa.telefone or "")
        tel_input.setPlaceholderText("(00) 00000-0000")
        form.addRow("Telefone:", tel_input)

        email_input = QLineEdit(empresa.email or "")
        email_input.setPlaceholderText("email@empresa.com")
        form.addRow("Email:", email_input)

        end_input = QLineEdit(empresa.endereco or "")
        end_input.setPlaceholderText("Rua/Av, n\u00famero")
        form.addRow("Endere\u00e7o:", end_input)

        cidade_input = QLineEdit(empresa.cidade or "")
        cidade_input.setPlaceholderText("Cidade")
        form.addRow("Cidade:", cidade_input)

        uf_input = QLineEdit(empresa.uf or "")
        uf_input.setPlaceholderText("UF")
        uf_input.setMaxLength(2)
        form.addRow("UF:", uf_input)

        obs_input = QTextEdit()
        obs_input.setMaximumHeight(60)
        obs_input.setPlainText(empresa.observacao or "")
        form.addRow("Observa\u00e7\u00e3o:", obs_input)

        btn_form_layout = QHBoxLayout()
        btn_form_layout.setSpacing(10)

        btn_salvar = QPushButton("\U0001f4be Salvar")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_salvar.clicked.connect(lambda: self._salvar_edicao(
            dialog, empresa, nome_input, cnpj_input, tipo_combo,
            tel_input, email_input, end_input, cidade_input, uf_input, obs_input
        ))
        btn_form_layout.addWidget(btn_salvar)

        btn_excluir = QPushButton("\U0001f5d1\ufe0f Excluir")
        btn_excluir.setCursor(Qt.PointingHandCursor)
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_excluir.clicked.connect(lambda: self._excluir(dialog, empresa))
        btn_form_layout.addWidget(btn_excluir)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_cancelar.clicked.connect(dialog.reject)
        btn_form_layout.addWidget(btn_cancelar)

        form.addRow(btn_form_layout)
        tabs.addTab(tab_dados, "\U0001f4cb Dados")

        tab_impressoras = QWidget()
        imp_layout = QVBoxLayout(tab_impressoras)

        impressoras = self.session.query(Printer).filter(
            Printer.local_atual == empresa.nome
        ).order_by(Printer.patrimonio).all()

        imp_label = QLabel(f"\U0001f5a8\ufe0f Impressoras em '{empresa.nome}' ({len(impressoras)})")
        imp_label.setStyleSheet(ESTILO_LABEL_CAMPO.replace("font-size: 12px;", "font-size: 14px;"))
        imp_layout.addWidget(imp_label)

        if impressoras:
            imp_tabela = QTableWidget()
            imp_tabela.setColumnCount(5)
            imp_tabela.setHorizontalHeaderLabels(["Patrim\u00f4nio", "Modelo", "Serial", "Status", "\u00daltima Revis\u00e3o"])
            imp_tabela.setRowCount(len(impressoras))
            imp_tabela.setStyleSheet(ESTILO_TABELA_SIMPLES)
            imp_tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
            imp_tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
            imp_tabela.verticalHeader().setVisible(False)

            for i, p in enumerate(impressoras):
                imp_tabela.setItem(i, 0, QTableWidgetItem(p.patrimonio))
                imp_tabela.setItem(i, 1, QTableWidgetItem(p.modelo))
                imp_tabela.setItem(i, 2, QTableWidgetItem(p.serial or "-"))

                status_item = QTableWidgetItem(p.status)
                if p.status in ["Operacional", "Em uso"]:
                    status_item.setForeground(QColor(COR["sucesso"]))
                elif p.status in ["Em manuten\u00e7\u00e3o", "Manuten\u00e7\u00e3o", "Aguardando pe\u00e7a"]:
                    status_item.setForeground(QColor(COR["aviso"]))
                elif p.status in ["Parada", "Sucata"]:
                    status_item.setForeground(QColor(COR["erro"]))
                imp_tabela.setItem(i, 3, status_item)

                rev_text = p.proxima_revisao.strftime("%d/%m/%Y") if p.proxima_revisao else "-"
                imp_tabela.setItem(i, 4, QTableWidgetItem(rev_text))

            imp_tabela.verticalHeader().setDefaultSectionSize(44)
            for i in range(imp_tabela.columnCount()):
                imp_tabela.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

            imp_tabela.cellDoubleClicked.connect(lambda r, c: self._abrir_impressora_por_patrimonio(
                imp_tabela.item(r, 0).text(), dialog
            ))

            imp_layout.addWidget(imp_tabela)
        else:
            sem = QLabel("Nenhuma impressora vinculada a esta empresa.")
            sem.setStyleSheet("color: #94949f; font-size: 13px; padding: 30px;")
            sem.setAlignment(Qt.AlignCenter)
            imp_layout.addWidget(sem)

        tabs.addTab(tab_impressoras, "\U0001f5a8\ufe0f Impressoras")

        main_layout = QVBoxLayout(dialog)
        main_layout.addWidget(tabs)
        dialog.exec()

    def _salvar_edicao(self, dialog, empresa, nome, cnpj, tipo, telefone, email, endereco, cidade, uf, obs):
        nome_antigo = empresa.nome
        nome_novo = nome.text().strip()

        empresa.cnpj = cnpj.text().strip()
        empresa.tipo = tipo.currentText()
        empresa.telefone = telefone.text().strip()
        empresa.email = email.text().strip()
        empresa.endereco = endereco.text().strip()
        empresa.cidade = cidade.text().strip()
        empresa.uf = uf.text().strip().upper()
        empresa.observacao = obs.toPlainText().strip()

        if nome_antigo != nome_novo and nome_novo:
            impressoras = self.session.query(Printer).filter(
                Printer.local_atual == nome_antigo
            ).all()
            for p in impressoras:
                p.local_atual = nome_novo

        empresa.nome = nome_novo
        self.session.commit()
        self.recarregar()
        dialog.accept()

    def _excluir(self, dialog, empresa):
        resposta = QMessageBox.question(
            dialog,
            "Confirmar Exclus\u00e3o",
            f"Deseja realmente excluir a empresa '{empresa.nome}'?\n\n"
            "As impressoras associadas N\u00c3O ser\u00e3o exclu\u00eddas, apenas ficar\u00e3o sem empresa vinculada.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if resposta == QMessageBox.Yes:
            self.company_service.excluir(empresa)
            self.recarregar()
            dialog.accept()

    def _abrir_impressora_por_patrimonio(self, patrimonio, parent_dialog):
        parent_dialog.accept()
        self.abrir_impressora.emit(patrimonio)
