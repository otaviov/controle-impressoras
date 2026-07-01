from __future__ import annotations

from typing import Any

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
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.utils.ui_helpers import tratar_erro
from app.utils.validacao import ValidadorCampo, email_opcional, obrigatorio
from app.views.styles.theme import (
    COR,
    ESTILO_BOTAO_AVISO,
    ESTILO_BOTAO_ERRO,
    ESTILO_BOTAO_FECHAR,
    ESTILO_BOTAO_PRIMARIO,
    ESTILO_BOTAO_SECUNDARIO,
    ESTILO_BOTAO_SUCESSO,
    ESTILO_SUBTITULO,
    configurar_combo,
    configurar_combo_colorido,
    ESTILO_COMBO,
    ESTILO_DIALOG,
    ESTILO_INPUT,
    ESTILO_LABEL_CAMPO,
    ESTILO_TABELA_SIMPLES,
    ESTILO_TITULO_PAGINA,
    TIPO_CLIENTE_CORES,
    group_box,
    input_label,
    campo_rotulo,
    campo_readonly,
)
from app.views.widgets import ToastManager
from app.views.widgets.confirm_dialog import ConfirmacaoDigitarDialog
from app.views.widgets.import_dialog import ImportDialog
from app.views.widgets.pagination import PaginacaoWidget
from app.views.widgets.table_widget import TabelaPadrao


class ClientsPage(QWidget):
    abrir_impressora: Signal = Signal(str)

    session: Any
    company_service: Any
    printer_service: Any
    _empresas_visiveis: list[Any]
    tabela: TabelaPadrao
    _paginacao: PaginacaoWidget

    def __init__(self, session: Any, company_service: Any, printer_service: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        self.company_service = company_service
        self.printer_service = printer_service
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        titulo = QLabel("\U0001f465 Clientes / Empresas")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        header.addWidget(titulo)
        header.addStretch()

        btn_nova = QPushButton("\u2795 Nova Empresa")
        btn_nova.setToolTip("Cadastrar nova empresa")
        btn_nova.setCursor(Qt.PointingHandCursor)
        btn_nova.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
        btn_nova.clicked.connect(self._nova)
        header.addWidget(btn_nova)

        btn_importar = QPushButton("  Importar")
        btn_importar.setToolTip("Importar empresas de arquivo CSV ou XLSX")
        btn_importar.setCursor(Qt.PointingHandCursor)
        btn_importar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_importar.clicked.connect(lambda: self._importar())
        header.addWidget(btn_importar)

        layout.addLayout(header)

        subtitulo = QLabel("Gerencie as empresas e clientes")
        subtitulo.setStyleSheet(ESTILO_SUBTITULO)
        layout.addWidget(subtitulo)

        self._empresas_visiveis = []
        self.tabela = TabelaPadrao(["Nome", "CNPJ", "Cidade/UF", "Telefone", "Email", "Impressoras"])
        self.tabela.cellDoubleClicked.connect(self._detalhes)
        layout.addWidget(self.tabela)

        self._paginacao = PaginacaoWidget()
        self._paginacao.pagina_alterada.connect(lambda p: self._carregar())
        layout.addWidget(self._paginacao)

        self._carregar()

    def recarregar(self) -> None:
        self._carregar()

    def _carregar(self) -> None:
        empresas = self.company_service.listar_todas(
            limite=self._paginacao.limit, offset=self._paginacao.offset
        )
        total = self.company_service.contar_todas()
        self._paginacao.configurar(total, pagina_atual=self._paginacao.pagina,
                                   itens_por_pagina=self._paginacao.limit)
        self._empresas_visiveis = empresas
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

    def _detalhes(self, row: int) -> None:
        nome_empresa = self.tabela.item(row, 0).text()
        empresa = self.company_service.buscar_por_nome(nome_empresa)
        if not empresa:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(empresa.nome)
        dialog.setMinimumSize(650, 500)
        dialog.setStyleSheet(ESTILO_DIALOG + ESTILO_TABELA_SIMPLES)

        tabs = QTabWidget()

        # ── Tab Dados (read-only) ──
        tab_dados = QWidget()
        tab_dados_layout = QVBoxLayout(tab_dados)
        tab_dados_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        content = QVBoxLayout(container)
        content.setContentsMargins(20, 16, 20, 16)
        content.setSpacing(16)

        # Identificação
        id_box, id_layout = group_box("Identificação")
        id_form = QFormLayout()
        id_form.setSpacing(8)
        id_form.addRow(campo_rotulo("Nome"), campo_readonly(empresa.nome))
        id_form.addRow(campo_rotulo("CNPJ"), campo_readonly(empresa.cnpj or "—"))
        id_form.addRow(campo_rotulo("Tipo"), campo_readonly(empresa.tipo or "—"))
        id_layout.addLayout(id_form)
        content.addWidget(id_box)

        # Contato
        cont_box, cont_layout = group_box("Contato")
        cont_form = QFormLayout()
        cont_form.setSpacing(8)
        cont_form.addRow(campo_rotulo("Telefone"), campo_readonly(empresa.telefone or "—"))
        cont_form.addRow(campo_rotulo("Email"), campo_readonly(empresa.email or "—"))
        cont_layout.addLayout(cont_form)
        content.addWidget(cont_box)

        # Endereço
        end_box, end_layout = group_box("Endereço")
        end_form = QFormLayout()
        end_form.setSpacing(8)
        end_form.addRow(campo_rotulo("Endereço"), campo_readonly(empresa.endereco or "—"))
        end_form.addRow(campo_rotulo("Cidade"), campo_readonly(empresa.cidade or "—"))
        end_form.addRow(campo_rotulo("UF"), campo_readonly(empresa.uf or "—"))
        end_layout.addLayout(end_form)
        content.addWidget(end_box)

        # Observações
        obs_box, obs_layout = group_box("Observações")
        obs_layout.addWidget(campo_readonly(empresa.observacao or "—"))
        content.addWidget(obs_box)

        content.addStretch()
        scroll.setWidget(container)
        tab_dados_layout.addWidget(scroll)

        # Buttons at bottom of Dados tab
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(20, 8, 20, 12)
        btn_layout.setSpacing(10)

        btn_editar = QPushButton("✏️  Editar")
        btn_editar.setCursor(Qt.PointingHandCursor)
        btn_editar.setStyleSheet(ESTILO_BOTAO_AVISO)
        btn_editar.clicked.connect(lambda: (dialog.accept(), self._editar(row)))
        btn_layout.addWidget(btn_editar)

        btn_excluir = QPushButton("🗑️ Excluir")
        btn_excluir.setCursor(Qt.PointingHandCursor)
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_excluir.clicked.connect(lambda: self._excluir(dialog, empresa))
        btn_layout.addWidget(btn_excluir)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setCursor(Qt.PointingHandCursor)
        btn_fechar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_fechar.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_fechar)

        tab_dados_layout.addLayout(btn_layout)

        tabs.addTab(tab_dados, "\U0001f4cb Dados")

        # ── Tab Impressoras (read-only, same as _editar) ──
        tab_impressoras = QWidget()
        imp_layout = QVBoxLayout(tab_impressoras)

        impressoras = self.printer_service.listar_por_local(empresa.nome)

        imp_label = QLabel(f"\U0001f5a8\ufe0f Impressoras em '{empresa.nome}' ({len(impressoras)})")
        imp_label.setStyleSheet(ESTILO_LABEL_CAMPO.replace("font-size: 12px;", "font-size: 14px;"))
        imp_layout.addWidget(imp_label)

        if impressoras:
            imp_tabela = QTableWidget()
            imp_tabela.setColumnCount(5)
            imp_tabela.setHorizontalHeaderLabels(["Patrimônio", "Modelo", "Serial", "Status", "Última Revisão"])
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
                elif p.status in ["Em manutenção", "Manutenção", "Aguardando peça"]:
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

    def _nova(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Nova Empresa")
        dialog.setMinimumSize(600, 500)
        dialog.setStyleSheet(ESTILO_DIALOG + ESTILO_INPUT + ESTILO_COMBO)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        content = QVBoxLayout(container)
        content.setContentsMargins(16, 8, 16, 8)
        content.setSpacing(16)

        id_box, id_layout = group_box("Identificação")
        id_form = QFormLayout()
        id_form.setSpacing(12)

        nome_input = QLineEdit()
        nome_input.setPlaceholderText("Nome da empresa")
        nome_input.setMaxLength(150)
        id_form.addRow("Nome:", nome_input)

        erro_nome = QLabel()
        erro_nome.setStyleSheet("color: #ef4444; font-size: 10px; background: transparent;")
        erro_nome.hide()
        id_form.addRow("", erro_nome)
        ValidadorCampo(nome_input, obrigatorio, erro_nome)

        cnpj_input = QLineEdit()
        cnpj_input.setPlaceholderText("00.000.000/0000-00")
        cnpj_input.setMaxLength(18)
        id_form.addRow("CNPJ:", cnpj_input)

        tipo_input = QComboBox()
        configurar_combo(tipo_input)
        cmp = tipo_input.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        tipo_input.addItems(["Cliente", "Filial", "Parceiro"])
        configurar_combo_colorido(tipo_input, TIPO_CLIENTE_CORES)
        id_form.addRow("Tipo:", tipo_input)

        id_layout.addLayout(id_form)
        content.addWidget(id_box)

        cont_box, cont_layout = group_box("Contato")
        cont_form = QFormLayout()
        cont_form.setSpacing(12)

        telefone_input = QLineEdit()
        telefone_input.setPlaceholderText("(00) 00000-0000")
        telefone_input.setMaxLength(20)
        cont_form.addRow("Telefone:", telefone_input)

        email_input = QLineEdit()
        email_input.setPlaceholderText("email@empresa.com")
        email_input.setMaxLength(120)
        cont_form.addRow("Email:", email_input)

        erro_email = QLabel()
        erro_email.setStyleSheet("color: #ef4444; font-size: 10px; background: transparent;")
        erro_email.hide()
        cont_form.addRow("", erro_email)
        ValidadorCampo(email_input, email_opcional, erro_email)

        cont_layout.addLayout(cont_form)
        content.addWidget(cont_box)

        end_box, end_layout = group_box("Endereço")
        end_form = QFormLayout()
        end_form.setSpacing(12)

        endereco_input = QLineEdit()
        endereco_input.setPlaceholderText("Rua/Av, número")
        endereco_input.setMaxLength(255)
        end_form.addRow("Endereço:", endereco_input)

        cidade_input = QLineEdit()
        cidade_input.setPlaceholderText("Cidade")
        cidade_input.setMaxLength(100)
        end_form.addRow("Cidade:", cidade_input)

        uf_input = QLineEdit()
        uf_input.setPlaceholderText("UF")
        uf_input.setMaxLength(2)
        end_form.addRow("UF:", uf_input)

        end_layout.addLayout(end_form)
        content.addWidget(end_box)

        obs_box, obs_lay = group_box("Observações")
        obs_input = QTextEdit()
        obs_input.setPlaceholderText("Observações sobre a empresa...")
        obs_input.setStyleSheet(ESTILO_INPUT)
        obs_input.setMaximumHeight(100)
        obs_lay.addWidget(input_label("Observações"))
        obs_lay.addWidget(obs_input)
        content.addWidget(obs_box)

        content.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_salvar = QPushButton("💾 Salvar")
        btn_salvar.setToolTip("Salvar nova empresa")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_salvar.clicked.connect(lambda: self._salvar_nova(dialog, nome_input, cnpj_input, telefone_input, email_input, tipo_input, endereco_input, cidade_input, uf_input, obs_input))

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setToolTip("Descartar alterações e fechar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_cancelar.clicked.connect(dialog.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_salvar)
        btn_layout.addWidget(btn_cancelar)
        layout.addLayout(btn_layout)

        dialog.exec()

    def _salvar_nova(self, dialog: QDialog, nome: QLineEdit, cnpj: QLineEdit, telefone: QLineEdit, email: QLineEdit, tipo: QComboBox, endereco: QLineEdit, cidade: QLineEdit, uf: QLineEdit, obs: QTextEdit) -> None:
        nome_text = nome.text().strip()
        if not nome_text:
            return
        with tratar_erro("criar empresa"):
            self.company_service.criar(
                nome=nome_text,
                cnpj=cnpj.text().strip(),
                telefone=telefone.text().strip(),
                email=email.text().strip(),
                tipo=tipo.currentText(),
                endereco=endereco.text().strip(),
                cidade=cidade.text().strip(),
                uf=uf.text().strip().upper(),
                observacao=obs.toPlainText().strip()
            )
            self.recarregar()
            dialog.accept()

    def _editar(self, row: int) -> None:
        nome_empresa = self.tabela.item(row, 0).text()
        empresa = self.company_service.buscar_por_nome(nome_empresa)

        if not empresa:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"\u270f\ufe0f Editar Empresa: {empresa.nome}")
        dialog.setMinimumSize(600, 500)
        dialog.setStyleSheet(ESTILO_DIALOG + ESTILO_INPUT + ESTILO_COMBO + ESTILO_TABELA_SIMPLES)

        tabs = QTabWidget()

        tab_dados = QWidget()
        outer_layout = QVBoxLayout(tab_dados)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        content = QVBoxLayout(container)
        content.setContentsMargins(16, 8, 16, 8)
        content.setSpacing(16)

        id_box, id_layout = group_box("Identificação")
        id_form = QFormLayout()
        id_form.setSpacing(12)

        nome_input = QLineEdit(empresa.nome or "")
        nome_input.setMaxLength(150)
        id_form.addRow("Nome:", nome_input)

        erro_nome = QLabel()
        erro_nome.setStyleSheet("color: #ef4444; font-size: 10px; background: transparent;")
        erro_nome.hide()
        id_form.addRow("", erro_nome)
        ValidadorCampo(nome_input, obrigatorio, erro_nome)

        cnpj_input = QLineEdit(empresa.cnpj or "")
        cnpj_input.setPlaceholderText("00.000.000/0000-00")
        cnpj_input.setMaxLength(18)
        id_form.addRow("CNPJ:", cnpj_input)

        tipo_combo = QComboBox()
        configurar_combo(tipo_combo)
        cmp = tipo_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        tipo_combo.addItems(["Cliente", "Filial", "Parceiro"])
        configurar_combo_colorido(tipo_combo, TIPO_CLIENTE_CORES)
        tipo_combo.setCurrentText(empresa.tipo or "Cliente")
        id_form.addRow("Tipo:", tipo_combo)

        id_layout.addLayout(id_form)
        content.addWidget(id_box)

        cont_box, cont_layout = group_box("Contato")
        cont_form = QFormLayout()
        cont_form.setSpacing(12)

        tel_input = QLineEdit(empresa.telefone or "")
        tel_input.setPlaceholderText("(00) 00000-0000")
        tel_input.setMaxLength(20)
        cont_form.addRow("Telefone:", tel_input)

        email_input = QLineEdit(empresa.email or "")
        email_input.setPlaceholderText("email@empresa.com")
        email_input.setMaxLength(120)
        cont_form.addRow("Email:", email_input)

        erro_email = QLabel()
        erro_email.setStyleSheet("color: #ef4444; font-size: 10px; background: transparent;")
        erro_email.hide()
        cont_form.addRow("", erro_email)
        ValidadorCampo(email_input, email_opcional, erro_email)

        cont_layout.addLayout(cont_form)
        content.addWidget(cont_box)

        end_box, end_layout = group_box("Endereço")
        end_form = QFormLayout()
        end_form.setSpacing(12)

        end_input = QLineEdit(empresa.endereco or "")
        end_input.setPlaceholderText("Rua/Av, n\u00famero")
        end_input.setMaxLength(255)
        end_form.addRow("Endere\u00e7o:", end_input)

        cidade_input = QLineEdit(empresa.cidade or "")
        cidade_input.setPlaceholderText("Cidade")
        cidade_input.setMaxLength(100)
        end_form.addRow("Cidade:", cidade_input)

        uf_input = QLineEdit(empresa.uf or "")
        uf_input.setPlaceholderText("UF")
        uf_input.setMaxLength(2)
        end_form.addRow("UF:", uf_input)

        end_layout.addLayout(end_form)
        content.addWidget(end_box)

        obs_box, obs_layout = group_box("Observações")
        obs_input = QTextEdit()
        obs_input.setMaximumHeight(100)
        obs_input.setStyleSheet(ESTILO_INPUT)
        obs_input.setPlainText(empresa.observacao or "")
        obs_layout.addWidget(input_label("Observações"))
        obs_layout.addWidget(obs_input)
        content.addWidget(obs_box)

        btn_form_layout = QHBoxLayout()
        btn_form_layout.setSpacing(10)

        btn_salvar = QPushButton("\U0001f4be Salvar")
        btn_salvar.setToolTip("Salvar alterações da empresa")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_salvar.clicked.connect(lambda: self._salvar_edicao(
            dialog, empresa, nome_input, cnpj_input, tipo_combo,
            tel_input, email_input, end_input, cidade_input, uf_input, obs_input
        ))
        btn_form_layout.addWidget(btn_salvar)

        btn_excluir = QPushButton("\U0001f5d1\ufe0f Excluir")
        btn_excluir.setToolTip("Excluir esta empresa (pode ser desfeito pela Lixeira)")
        btn_excluir.setCursor(Qt.PointingHandCursor)
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_excluir.clicked.connect(lambda: self._excluir(dialog, empresa))
        btn_form_layout.addWidget(btn_excluir)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setToolTip("Descartar alterações e fechar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_cancelar.clicked.connect(dialog.reject)
        btn_form_layout.addWidget(btn_cancelar)

        content.addLayout(btn_form_layout)
        content.addStretch()
        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

        tabs.addTab(tab_dados, "\U0001f4cb Dados")

        tab_impressoras = QWidget()
        imp_layout = QVBoxLayout(tab_impressoras)

        impressoras = self.printer_service.listar_por_local(empresa.nome)

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

    def _salvar_edicao(self, dialog: QDialog, empresa: Any, nome: QLineEdit, cnpj: QLineEdit, tipo: QComboBox, telefone: QLineEdit, email: QLineEdit, endereco: QLineEdit, cidade: QLineEdit, uf: QLineEdit, obs: QTextEdit) -> None:
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

        with tratar_erro("salvar edição da empresa"):
            if nome_antigo != nome_novo and nome_novo:
                self.printer_service.atualizar_local_por_nome_antigo(nome_antigo, nome_novo)
            empresa.nome = nome_novo
            self.session.commit()
            self.recarregar()
            dialog.accept()

    def _excluir(self, dialog: QDialog, empresa: Any) -> None:
        if ConfirmacaoDigitarDialog.confirmar(
            "Confirmar Exclusão",
            f"Deseja realmente excluir a empresa '{empresa.nome}'?\n\n"
            "As impressoras associadas NÃO serão excluídas, apenas ficarão sem empresa vinculada.",
            dialog,
        ):
            with tratar_erro("excluir empresa"):
                self.company_service.excluir(empresa)
                ToastManager.mostrar(
                    f"Empresa '{empresa.nome}' excluída.",
                    "aviso", duracao=8000,
                    acao=("Desfazer", lambda o=empresa, svc=self.company_service, pag=self: (svc.restaurar(o), pag.recarregar())),
                )
                self.recarregar()
                dialog.accept()

    def _importar(self) -> None:
        dialog: ImportDialog = ImportDialog(self, "companies", "Empresas", self.company_service, self.session)
        if dialog.exec() == ImportDialog.Accepted:
            self.recarregar()

    def _abrir_impressora_por_patrimonio(self, patrimonio: str, parent_dialog: QDialog) -> None:
        parent_dialog.accept()
        self.abrir_impressora.emit(patrimonio)
