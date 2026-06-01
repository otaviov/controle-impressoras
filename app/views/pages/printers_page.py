from datetime import datetime as dt

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
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
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.utils.helpers import formatar_data_hora, limpar_local, parse_data
from app.views.styles.theme import (
    COR,
    ESTILO_BOTAO_AVISO,
    ESTILO_BOTAO_ERRO,
    ESTILO_BOTAO_FECHAR,
    ESTILO_BOTAO_PRIMARIO,
    ESTILO_BOTAO_SECUNDARIO,
    ESTILO_BOTAO_SUCESSO,
    configurar_combo,
    ESTILO_DIALOG,
    ESTILO_INPUT,
    ESTILO_INPUT_READONLY,
    ESTILO_LABEL_CAMPO,
    ESTILO_SUBTITULO,
    ESTILO_TITULO_PAGINA,
    STATUS_CORES,
    estilos_dialogo_tabs,
)
from app.views.widgets.search_bar import SearchBar
from app.views.widgets.table_widget import TabelaPadrao


class PrintersPage(QWidget):
    def __init__(self, session, printer_service, company_service, technician_service, activity_service, part_service, parent=None):
        super().__init__(parent)
        self.session = session
        self.printer_service = printer_service
        self.company_service = company_service
        self.technician_service = technician_service
        self.activity_service = activity_service
        self.part_service = part_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(10)

        titulo = QLabel("Impressoras")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        sub = QLabel("Gerencie todas as impressoras cadastradas")
        sub.setStyleSheet(ESTILO_SUBTITULO)

        titulo_col = QVBoxLayout()
        titulo_col.setSpacing(2)
        titulo_col.addWidget(titulo)
        titulo_col.addWidget(sub)
        header.addLayout(titulo_col)
        header.addStretch()

        self.search = SearchBar(placeholder="Buscar por patrimônio, modelo, serial ou local...")
        self.search.textChanged().connect(lambda texto: self.filtrar(texto))
        header.addWidget(self.search)

        btn_nova = QPushButton("  Nova Impressora")
        btn_nova.setCursor(Qt.PointingHandCursor)
        btn_nova.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
        btn_nova.clicked.connect(self._nova)
        header.addWidget(btn_nova)

        btn_atualizar = QPushButton("  Atualizar")
        btn_atualizar.setCursor(Qt.PointingHandCursor)
        btn_atualizar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_atualizar.clicked.connect(self.recarregar)
        header.addWidget(btn_atualizar)

        layout.addLayout(header)

        colunas = ["Patrimônio", "Modelo", "Serial", "Marca", "Status", "Local Atual", "Atividades"]
        self.tabela = TabelaPadrao(colunas)
        self.tabela.cellDoubleClicked.connect(self._detalhes)
        layout.addWidget(self.tabela)

        self.recarregar()

    def recarregar(self, filtro=None):
        impressoras = self.printer_service.listar_todos(filtro)
        ids = [p.id for p in impressoras]
        counts = self.printer_service.contar_atividades(ids) if ids else {}

        self.tabela.setRowCount(len(impressoras))

        for i, p in enumerate(impressoras):
            pat_item = QTableWidgetItem(p.patrimonio)
            pat_item.setForeground(QColor(COR["texto"]))
            self.tabela.setItem(i, 0, pat_item)

            self.tabela.setItem(i, 1, QTableWidgetItem(p.modelo))
            self.tabela.setItem(i, 2, QTableWidgetItem(p.serial or "-"))
            self.tabela.setItem(i, 3, QTableWidgetItem(p.marca or "-"))

            cor = STATUS_CORES.get(p.status, "#94949f")
            self.tabela.definir_badge(i, 4, p.status, cor)

            self.tabela.setItem(i, 5, QTableWidgetItem(p.local_atual or "-"))

            cnt_item = QTableWidgetItem(str(counts.get(p.id, 0)))
            cnt_item.setTextAlignment(Qt.AlignCenter)
            cnt_item.setForeground(QColor(COR["texto_sec"]))
            self.tabela.setItem(i, 6, cnt_item)

        self.tabela.redimensionar()

    def filtrar(self, texto):
        self.recarregar(texto if texto else None)

    def _nova(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nova Impressora")
        dialog.setFixedSize(500, 520)
        dialog.setStyleSheet(ESTILO_DIALOG)
        layout = QFormLayout(dialog)
        layout.setSpacing(8)

        patrimonio_input = QLineEdit()
        patrimonio_input.setPlaceholderText("Número do patrimônio")
        layout.addRow("Patrimônio *:", patrimonio_input)

        modelo_input = QLineEdit()
        modelo_input.setPlaceholderText("Modelo da impressora")
        layout.addRow("Modelo:", modelo_input)

        marca_input = QLineEdit()
        marca_input.setPlaceholderText("Marca (HP, Brother, etc)")
        layout.addRow("Marca:", marca_input)

        serial_input = QLineEdit()
        serial_input.setPlaceholderText("Número de série")
        layout.addRow("Serial:", serial_input)

        tipo_combo = QComboBox()
        configurar_combo(tipo_combo)
        tipo_combo.addItems(["", "Laser", "Jato de tinta", "Multifuncional"])
        layout.addRow("Tipo:", tipo_combo)

        local_combo = QComboBox()
        local_combo.setEditable(True)
        configurar_combo(local_combo)
        local_combo.addItem("")
        empresas = self.company_service.listar_todas()
        for emp in empresas:
            local_combo.addItem(f"\U0001f3e2 {emp.nome}")
        locais_existentes = self.printer_service.locais_distintos()
        nomes_empresas = {emp.nome for emp in empresas}
        for nome in locais_existentes:
            if nome and nome not in nomes_empresas:
                local_combo.addItem(f"\U0001f4cd {nome}")
        local_combo.setCurrentText("")
        layout.addRow("Local Atual:", local_combo)

        status_combo = QComboBox()
        configurar_combo(status_combo)
        status_combo.addItems(["Operacional", "Em uso", "Em manutenção", "Parada", "Aguardando peça", "Sucata"])
        layout.addRow("Status:", status_combo)

        ip_input = QLineEdit()
        ip_input.setPlaceholderText("192.168.0.100")
        layout.addRow("IP Rede:", ip_input)

        tec_combo = QComboBox()
        tec_combo.setEditable(True)
        configurar_combo(tec_combo)
        tec_combo.addItem("")
        tecnicos = self.technician_service.listar_ativos()
        for t in tecnicos:
            tec_combo.addItem(t.nome_exibicao)
        layout.addRow("Técnico:", tec_combo)

        obs_input = QTextEdit()
        obs_input.setMaximumHeight(60)
        obs_input.setPlaceholderText("Observações gerais...")
        obs_input.setStyleSheet(ESTILO_INPUT)
        layout.addRow("Observação:", obs_input)

        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.setStyleSheet("QPushButton { border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }")
        botoes.accepted.connect(lambda: self._salvar_nova(dialog, patrimonio_input, modelo_input, marca_input, serial_input, tipo_combo, local_combo, status_combo, ip_input, tec_combo, obs_input))
        botoes.rejected.connect(dialog.reject)
        layout.addRow(botoes)
        dialog.exec()

    def _salvar_nova(self, dialog, pat, mod, marca, serial, tipo, local, status, ip, tec, obs):
        patrimonio = pat.text().strip()
        if not patrimonio:
            QMessageBox.warning(dialog, "Aviso", "Preencha o patrimônio!")
            return

        existente = self.printer_service.verificar_patrimonio_existe(patrimonio)
        if existente:
            QMessageBox.warning(dialog, "Patrimônio Duplicado",
                f"Já existe uma impressora com o patrimônio '{patrimonio}'!\n\n"
                f"Modelo: {existente.modelo}\n"
                f"Local: {existente.local_atual or 'N/A'}\n"
                f"Status: {existente.status or 'N/A'}")
            return

        self.printer_service.criar(
            patrimonio=patrimonio,
            modelo=mod.text().strip(),
            marca=marca.text().strip(),
            serial=serial.text().strip(),
            tipo=tipo.currentText(),
            local_atual=limpar_local(local.currentText()),
            status=status.currentText(),
            ip_rede=ip.text().strip(),
            tecnico=tec.currentText().strip(),
            observacao=obs.toPlainText().strip()
        )
        self.recarregar()
        dialog.accept()

    def _detalhes(self, row):
        patrimonio = self.tabela.item(row, 0).text()
        printer = self.printer_service.buscar_por_patrimonio(patrimonio)
        if not printer:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"\U0001f5a8 Impressora {printer.patrimonio} - {printer.modelo}")
        dialog.setMinimumSize(750, 550)
        dialog.setStyleSheet(ESTILO_DIALOG + """
            QLineEdit, QTextEdit { background-color: #1a1a2e; color: #e2e8f0; border: 1px solid #2e2e4a; border-radius: 6px; padding: 6px; font-size: 13px; }
            QLineEdit[readOnly="true"], QTextEdit[readOnly="true"] { background-color: #0f0f1a; color: #475569; border: 1px solid #1e1e30; }
            QComboBox { background-color: #1a1a2e; color: #e2e8f0; border: 1px solid #2e2e4a; border-radius: 6px; padding: 6px; }
            QComboBox:disabled { background-color: #0f0f1a; color: #475569; }
            QTableWidget { background-color: #1a1a2e; color: #e2e8f0; border: 1px solid #2e2e4a; border-radius: 8px; gridline-color: #2a2a3e; font-size: 12px; }
            QTableWidget::item { padding: 6px; }
            QHeaderView::section { background-color: #0f0f1a; color: #60a5fa; font-weight: bold; padding: 8px; border: none; border-bottom: 1px solid #2e2e4a; }
        """ + estilos_dialogo_tabs() + """
            QPushButton { border: none; border-radius: 8px; padding: 10px 20px; font-size: 13px; font-weight: bold; }
        """)

        layout = QVBoxLayout(dialog)
        tabs = QTabWidget()
        tabs.setStyleSheet(estilos_dialogo_tabs())

        tab_dados = QWidget()
        dados_layout = QGridLayout(tab_dados)
        dados_layout.setSpacing(8)
        dados_layout.setContentsMargins(15, 15, 15, 15)

        dados_layout.addWidget(QLabel("Patrimônio:"), 0, 0)
        pat_input = QLineEdit(printer.patrimonio)
        pat_input.setReadOnly(True)
        pat_input.setStyleSheet(ESTILO_INPUT_READONLY)
        dados_layout.addWidget(pat_input, 0, 1)

        dados_layout.addWidget(QLabel("Status:"), 0, 2)
        status_combo = QComboBox()
        configurar_combo(status_combo)
        status_combo.addItems(["Operacional", "Em uso", "Em manutenção", "Parada", "Aguardando peça", "Sucata"])
        status_combo.setCurrentText(printer.status or "Operacional")
        status_combo.setEnabled(False)
        dados_layout.addWidget(status_combo, 0, 3)

        dados_layout.addWidget(QLabel("Modelo:"), 1, 0)
        modelo_input = QLineEdit(printer.modelo or "")
        modelo_input.setReadOnly(True)
        dados_layout.addWidget(modelo_input, 1, 1)

        dados_layout.addWidget(QLabel("Marca:"), 1, 2)
        marca_input = QLineEdit(printer.marca or "")
        marca_input.setReadOnly(True)
        dados_layout.addWidget(marca_input, 1, 3)

        dados_layout.addWidget(QLabel("Serial:"), 2, 0)
        serial_input = QLineEdit(printer.serial or "")
        serial_input.setReadOnly(True)
        dados_layout.addWidget(serial_input, 2, 1)

        dados_layout.addWidget(QLabel("Tipo:"), 2, 2)
        tipo_combo = QComboBox()
        configurar_combo(tipo_combo)
        tipo_combo.addItems(["", "Laser", "Jato de tinta", "Multifuncional"])
        tipo_combo.setCurrentText(printer.tipo or "")
        tipo_combo.setEnabled(False)
        dados_layout.addWidget(tipo_combo, 2, 3)

        dados_layout.addWidget(QLabel("Local Atual:"), 3, 0)
        local_combo = QComboBox()
        local_combo.setEditable(True)
        configurar_combo(local_combo)
        local_combo.addItem("")
        empresas = self.company_service.listar_todas()
        for emp in empresas:
            local_combo.addItem(f"\U0001f3e2 {emp.nome}")
        locais = self.printer_service.locais_distintos()
        nomes_emp = {e.nome for e in empresas}
        for nome in locais:
            if nome and nome not in nomes_emp:
                local_combo.addItem(f"\U0001f4cd {nome}")
        atual = printer.local_atual or ""
        idx = local_combo.findText(f"\U0001f3e2 {atual}")
        if idx < 0:
            idx = local_combo.findText(f"\U0001f4cd {atual}")
        if idx >= 0:
            local_combo.setCurrentIndex(idx)
        else:
            local_combo.setCurrentText(atual)
        local_combo.setEnabled(False)
        dados_layout.addWidget(local_combo, 3, 1)

        dados_layout.addWidget(QLabel("IP Rede:"), 3, 2)
        ip_input = QLineEdit(printer.ip_rede or "")
        ip_input.setReadOnly(True)
        dados_layout.addWidget(ip_input, 3, 3)

        dados_layout.addWidget(QLabel("Técnico:"), 4, 0)
        tec_combo = QComboBox()
        tec_combo.setEditable(True)
        configurar_combo(tec_combo)
        tec_combo.addItem("")
        tecnicos = self.technician_service.listar_ativos()
        for t in tecnicos:
            tec_combo.addItem(t.nome_exibicao)
        tec_combo.setCurrentText(printer.tecnico or "")
        tec_combo.setEnabled(False)
        dados_layout.addWidget(tec_combo, 4, 1)

        ultima_manutencao = self.activity_service.listar_por_impressora(printer.id)
        ultima_manut = None
        for a in ultima_manutencao:
            if a.kind == "MANUTENCAO":
                ultima_manut = a
                break

        dados_layout.addWidget(QLabel("Última Revisão:"), 4, 2)
        rev_text = ""
        if printer.proxima_revisao:
            rev_text = printer.proxima_revisao.strftime("%d/%m/%Y")
        elif ultima_manut and ultima_manut.event_at:
            rev_text = ultima_manut.event_at.strftime("%d/%m/%Y")
        if not rev_text:
            rev_text = dt.now().strftime("%d/%m/%Y")
        rev_input = QLineEdit(rev_text)
        rev_input.setPlaceholderText("dd/mm/aaaa")
        rev_input.setReadOnly(True)
        dados_layout.addWidget(rev_input, 4, 3)

        dados_layout.addWidget(QLabel("Observação:"), 5, 0)
        obs_input = QTextEdit()
        obs_input.setMaximumHeight(80)
        obs_input.setPlainText(printer.observacao or "")
        obs_input.setReadOnly(True)
        obs_input.setStyleSheet(ESTILO_INPUT_READONLY)
        dados_layout.addWidget(obs_input, 5, 1, 1, 3)

        lbl_pecas = QLabel("Peças Faltantes:")
        lbl_pecas.setStyleSheet("color: #fbbf24; font-weight: bold;")
        dados_layout.addWidget(lbl_pecas, 6, 0)
        pecas_input = QTextEdit()
        pecas_input.setMaximumHeight(60)
        pecas_input.setPlainText(printer.pecas_faltantes or "")
        pecas_input.setReadOnly(True)
        pecas_input.setStyleSheet(ESTILO_INPUT_READONLY)
        dados_layout.addWidget(pecas_input, 6, 1, 1, 3)

        for i in range(dados_layout.count()):
            item = dados_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if isinstance(w, QLabel) and w.text().endswith(":") and "Peças" not in w.text():
                    w.setStyleSheet(ESTILO_LABEL_CAMPO)
                elif isinstance(w, QLineEdit) and not w.isReadOnly():
                    w.setStyleSheet(ESTILO_INPUT)

        tabs.addTab(tab_dados, "\U0001f4cb Dados Gerais")

        tab_historico = QWidget()
        hist_layout = QVBoxLayout(tab_historico)
        atividades = self.activity_service.listar_por_impressora(printer.id)
        hist_label = QLabel(f"Total de atividades: {len(atividades)}")
        hist_label.setStyleSheet("color: #60a5fa; font-weight: bold; font-size: 13px;")
        hist_layout.addWidget(hist_label)

        hist_tabela = QTableWidget()
        hist_tabela.setColumnCount(6)
        hist_tabela.setHorizontalHeaderLabels(["Data", "Tipo", "Descrição", "Peças", "Origem", "Destino"])
        hist_tabela.setRowCount(len(atividades))
        for i, a in enumerate(atividades):
            hist_tabela.setItem(i, 0, QTableWidgetItem(formatar_data_hora(a.event_at) if a.event_at else "-"))
            tipo = "\U0001f527 Manutenção" if a.kind == "MANUTENCAO" else "\U0001f69a Movimentação"
            tipo_item = QTableWidgetItem(tipo)
            tipo_item.setForeground(QColor("#f59e0b") if a.kind == "MANUTENCAO" else QColor("#6366f1"))
            hist_tabela.setItem(i, 1, tipo_item)
            hist_tabela.setItem(i, 2, QTableWidgetItem(a.notes or "-"))
            hist_tabela.setItem(i, 3, QTableWidgetItem(a.parts_used or "-"))
            hist_tabela.setItem(i, 4, QTableWidgetItem(a.from_location or "-"))
            hist_tabela.setItem(i, 5, QTableWidgetItem(a.to_location or "-"))

        hist_tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        hist_tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        hist_tabela.verticalHeader().setVisible(False)
        hist_tabela.verticalHeader().setDefaultSectionSize(44)
        for i in range(hist_tabela.columnCount()):
            hist_tabela.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        hist_tabela.cellDoubleClicked.connect(lambda r, c: self._editar_atividade(r, atividades, printer, dialog))
        hist_layout.addWidget(hist_tabela)

        tabs.addTab(tab_historico, "\U0001f4dc Histórico")

        layout.addWidget(tabs)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_editar = QPushButton("\u270f Editar")
        btn_editar.setCursor(Qt.PointingHandCursor)
        btn_editar.setStyleSheet(ESTILO_BOTAO_AVISO)

        btn_salvar = QPushButton("\U0001f4be Salvar Alterações")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_salvar.setVisible(False)

        btn_cancelar = QPushButton("\u274c Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_cancelar.setVisible(False)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setCursor(Qt.PointingHandCursor)
        btn_fechar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_fechar.clicked.connect(dialog.accept)

        widgets_editaveis = [pat_input, status_combo, modelo_input, marca_input, serial_input, tipo_combo, local_combo, ip_input, tec_combo, rev_input, obs_input, pecas_input]

        def entrar_modo_edicao():
            btn_editar.setVisible(False)
            btn_salvar.setVisible(True)
            btn_cancelar.setVisible(True)
            for w in widgets_editaveis:
                if isinstance(w, QLineEdit):
                    w.setReadOnly(False)
                    w.setStyleSheet(ESTILO_INPUT)
                elif isinstance(w, QTextEdit):
                    w.setReadOnly(False)
                    w.setStyleSheet(ESTILO_INPUT)
                elif isinstance(w, QComboBox):
                    w.setEnabled(True)

        def sair_modo_edicao():
            btn_editar.setVisible(True)
            btn_salvar.setVisible(False)
            btn_cancelar.setVisible(False)
            for w in widgets_editaveis:
                if isinstance(w, QLineEdit):
                    w.setReadOnly(True)
                    w.setStyleSheet(ESTILO_INPUT_READONLY)
                elif isinstance(w, QTextEdit):
                    w.setReadOnly(True)
                    w.setStyleSheet(ESTILO_INPUT_READONLY)
                elif isinstance(w, QComboBox):
                    w.setEnabled(False)

        btn_editar.clicked.connect(entrar_modo_edicao)
        btn_cancelar.clicked.connect(sair_modo_edicao)
        btn_salvar.clicked.connect(lambda: self._salvar_edicao(dialog, printer, pat_input, status_combo, modelo_input, marca_input, serial_input, tipo_combo, local_combo, ip_input, tec_combo, rev_input, obs_input, pecas_input, sair_modo_edicao))

        btn_layout.addWidget(btn_editar)
        btn_layout.addWidget(btn_salvar)
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_fechar)

        layout.addLayout(btn_layout)
        dialog.exec()

    def _salvar_edicao(self, dialog, printer, pat_input, status, modelo, marca, serial, tipo, local, ip, tecnico, revisao, obs, pecas, callback=None):
        novo_pat = pat_input.text().strip()
        if novo_pat and novo_pat != printer.patrimonio:
            existente = self.printer_service.verificar_patrimonio_existe(novo_pat)
            if existente:
                QMessageBox.warning(dialog, "Patrimônio Duplicado", f"Já existe uma impressora com o patrimônio '{novo_pat}'!")
                return

        self.printer_service.atualizar(
            printer,
            patrimonio=novo_pat,
            status=status.currentText(),
            modelo=modelo.text().strip(),
            marca=marca.text().strip(),
            serial=serial.text().strip(),
            tipo=tipo.currentText(),
            local_atual=limpar_local(local.currentText()),
            ip_rede=ip.text().strip(),
            tecnico=tecnico.currentText().strip(),
            proxima_revisao=parse_data(revisao.text()) or printer.proxima_revisao or dt.now(),
            observacao=obs.toPlainText().strip(),
            pecas_faltantes=pecas.toPlainText().strip()
        )
        self.recarregar()
        if callback:
            callback()

    def _editar_atividade(self, row, atividades, printer, parent_dialog):
        atividade = atividades[row]

        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle("\u270f Editar Atividade")
        dialog.setMinimumWidth(520)
        dialog.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        todos_printers = self.printer_service.listar_todos()
        cmb_printer = QComboBox()
        configurar_combo(cmb_printer)
        cmb_printer.setInsertPolicy(QComboBox.NoInsert)
        for p in todos_printers:
            cmb_printer.addItem(p.patrimonio)
        printer_atual = self.printer_service.buscar_por_id(atividade.printer_id)
        if printer_atual:
            idx = cmb_printer.findText(printer_atual.patrimonio)
            if idx >= 0:
                cmb_printer.setCurrentIndex(idx)
            else:
                cmb_printer.setCurrentText(printer_atual.patrimonio)
        form.addRow("Impressora:", cmb_printer)

        cmb_tipo = QComboBox()
        configurar_combo(cmb_tipo)
        cmb_tipo.addItems(["MANUTENCAO", "MOVIMENTACAO"])
        cmb_tipo.setCurrentText(atividade.kind)
        form.addRow("Tipo:", cmb_tipo)

        edt_data = QLineEdit()
        edt_data.setText(formatar_data_hora(atividade.event_at) if atividade.event_at else "")
        edt_data.setStyleSheet(ESTILO_INPUT)
        form.addRow("Data/Hora:", edt_data)

        txt_descricao = QTextEdit()
        txt_descricao.setMaximumHeight(80)
        txt_descricao.setPlainText(atividade.notes or "")
        txt_descricao.setStyleSheet(ESTILO_INPUT)
        form.addRow("Descrição:", txt_descricao)

        txt_pecas = QTextEdit()
        txt_pecas.setMaximumHeight(60)
        txt_pecas.setPlainText(atividade.parts_used or "")
        txt_pecas.setStyleSheet(ESTILO_INPUT)
        form.addRow("Peças Trocadas:", txt_pecas)

        estoque_combo = QComboBox()
        configurar_combo(estoque_combo)
        estoque_combo.addItem("-- Nenhuma --", None)
        for p in self.part_service.listar_todas():
            if p.quantidade_estoque > 0:
                estoque_combo.addItem(f"{p.nome} ({p.quantidade_estoque} un.)", p.id)

        def _preencher_pecas(idx):
            if idx <= 0:
                return
            try:
                pid = estoque_combo.currentData()
                if pid is None:
                    return
                part = self.part_service.buscar_por_id(pid)
                if part:
                    atual = txt_pecas.toPlainText().strip()
                    txt_pecas.setPlainText(
                        f"{part.nome}" if not atual else f"{atual}, {part.nome}"
                    )
            except RuntimeError:
                pass
        estoque_combo.currentIndexChanged.connect(_preencher_pecas)
        form.addRow("Peça do Estoque:", estoque_combo)

        empresas = self.company_service.listar_nomes() if self.company_service else []

        cmb_origem = QComboBox()
        cmb_origem.setEditable(True)
        configurar_combo(cmb_origem)
        cmb_origem.setInsertPolicy(QComboBox.NoInsert)
        cmb_origem.addItems(empresas)
        if atividade.from_location:
            idx = cmb_origem.findText(atividade.from_location)
            if idx >= 0:
                cmb_origem.setCurrentIndex(idx)
            else:
                cmb_origem.setCurrentText(atividade.from_location)
        form.addRow("Origem:", cmb_origem)
        lbl_origem = form.labelForField(cmb_origem)

        cmb_destino = QComboBox()
        cmb_destino.setEditable(True)
        configurar_combo(cmb_destino)
        cmb_destino.setInsertPolicy(QComboBox.NoInsert)
        cmb_destino.addItems(empresas)
        if atividade.to_location:
            idx = cmb_destino.findText(atividade.to_location)
            if idx >= 0:
                cmb_destino.setCurrentIndex(idx)
            else:
                cmb_destino.setCurrentText(atividade.to_location)
        form.addRow("Destino:", cmb_destino)
        lbl_destino = form.labelForField(cmb_destino)

        def _toggle_origem_destino(tipo):
            visivel = tipo == "MOVIMENTACAO"
            lbl_origem.setVisible(visivel)
            cmb_origem.setVisible(visivel)
            lbl_destino.setVisible(visivel)
            cmb_destino.setVisible(visivel)
        cmb_tipo.currentTextChanged.connect(_toggle_origem_destino)
        _toggle_origem_destino(cmb_tipo.currentText())

        cmb_tecnico = QComboBox()
        cmb_tecnico.setEditable(True)
        configurar_combo(cmb_tecnico)
        cmb_tecnico.setInsertPolicy(QComboBox.NoInsert)
        if self.technician_service:
            cmb_tecnico.addItems(self.technician_service.nomes_exibicao())
        form.addRow("Técnico:", cmb_tecnico)

        cmb_status = QComboBox()
        configurar_combo(cmb_status)
        cmb_status.addItems(["Concluida", "Pendente", "Em Andamento"])
        cmb_status.setCurrentText(atividade.status_atividade or "Concluida")
        form.addRow("Status:", cmb_status)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_salvar = QPushButton("\U0001f4be Salvar")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_salvar.clicked.connect(lambda: self._salvar_edicao_atividade(
            dialog, atividade, cmb_printer, cmb_tipo, edt_data,
            txt_descricao, txt_pecas, cmb_origem, cmb_destino,
            cmb_tecnico, cmb_status))
        btn_layout.addWidget(btn_salvar)

        btn_excluir = QPushButton("\U0001f5d1 Excluir")
        btn_excluir.setCursor(Qt.PointingHandCursor)
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_excluir.clicked.connect(lambda: self._excluir_atividade(dialog, atividade))
        btn_layout.addWidget(btn_excluir)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_cancelar.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancelar)

        layout.addLayout(btn_layout)
        dialog.exec()

    def _salvar_edicao_atividade(self, dialog, atividade, printer_combo, tipo, data,
                                  desc, pecas, origem, destino, tecnico, status):
        data_text = data.text().strip()
        event_at = atividade.event_at
        if data_text:
            try:
                event_at = dt.strptime(data_text, "%d/%m/%Y %H:%M")
            except ValueError:
                try:
                    event_at = dt.strptime(data_text, "%d/%m/%Y")
                except ValueError:
                    pass

        printer_pat = printer_combo.currentText().strip()
        printer_obj = self.printer_service.buscar_por_patrimonio(printer_pat)

        self.activity_service.atualizar(
            atividade,
            printer_id=printer_obj.id if printer_obj else atividade.printer_id,
            kind=tipo.currentText(),
            event_at=event_at,
            notes=desc.toPlainText().strip(),
            parts_used=pecas.toPlainText().strip(),
            from_location=origem.currentText().strip() if origem.isVisible() else "",
            to_location=destino.currentText().strip() if destino.isVisible() else "",
            status_atividade=status.currentText()
        )
        self.recarregar()
        dialog.accept()

    def _excluir_atividade(self, dialog, atividade):
        resposta = QMessageBox.question(
            dialog,
            "Confirmar Exclusão",
            "Deseja realmente excluir esta atividade?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if resposta == QMessageBox.Yes:
            self.activity_service.excluir(atividade)
            self.recarregar()
            dialog.accept()
