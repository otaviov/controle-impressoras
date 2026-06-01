from datetime import datetime as dt

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models import Part
from app.services.part_service import PartService
from app.utils.helpers import formatar_data_hora, parse_data
from app.views.styles.theme import (
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
)
from app.views.widgets.card_widget import CardMiniClicavel
from app.views.widgets.search_bar import SearchBar
from app.views.widgets.table_widget import TabelaPadrao


class OSPage(QWidget):
    def __init__(self, session, printer_service, activity_service, company_service, technician_service, parent=None):
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

    def _setup_ui(self):
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
        self.btn_nova.clicked.connect(self._nova)
        header.addWidget(self.btn_nova)

        self.btn_manut = QPushButton("Manutenções")
        self.btn_manut.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        self.btn_manut.clicked.connect(lambda: self._filtrar_tipo("MANUTENCAO"))
        header.addWidget(self.btn_manut)

        self.btn_mov = QPushButton("Movimentações")
        self.btn_mov.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        self.btn_mov.clicked.connect(lambda: self._filtrar_tipo("MOVIMENTACAO"))
        header.addWidget(self.btn_mov)

        self.btn_todas = QPushButton("Todas")
        self.btn_todas.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        self.btn_todas.clicked.connect(lambda: self._filtrar_tipo("TODAS"))
        header.addWidget(self.btn_todas)

        self.btn_atualizar = QPushButton("Atualizar")
        self.btn_atualizar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
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
        self.tabela.cellDoubleClicked.connect(self._editar)
        layout.addWidget(self.tabela)

    def recarregar(self, filtro_tipo=None):
        if filtro_tipo:
            self._filtro_tipo_atual = filtro_tipo
        atividades = self.activity_service.listar(filtro_tipo=self._filtro_tipo_atual)
        self._atividades = atividades
        self._preencher_tabela(atividades)
        self._atualizar_cards()

    def _preencher_tabela(self, atividades):
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

    def _filtrar_tipo(self, tipo):
        self.recarregar(filtro_tipo=tipo)

    def _filtrar_status(self, status):
        atividades = self.activity_service.listar_por_status(status)
        self._atividades = atividades
        self._preencher_tabela(atividades)

    def _filtrar_busca(self, texto):
        if not texto.strip():
            self.recarregar()
            return
        atividades = self.activity_service.buscar_por_filtro_busca(texto)
        self._atividades = atividades
        self._preencher_tabela(atividades)

    def _atualizar_cards(self):
        total = self.activity_service.contar_total()
        andamento = self.activity_service.contar_por_status("Em Andamento")
        pendentes = self.activity_service.contar_por_status("Pendente")
        concluidas = self.activity_service.contar_por_status("Concluida")
        self.card_total.atualizar_valor(total)
        self.card_andamento.atualizar_valor(andamento)
        self.card_pendentes.atualizar_valor(pendentes)
        self.card_concluidas.atualizar_valor(concluidas)

    def _nova(self):
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
        data_texto = campos["data"].text().strip()
        event_at = parse_data(data_texto) if data_texto else dt.now()
        notes = campos["descricao"].toPlainText().strip()
        parts_used = campos["pecas"].toPlainText().strip()
        from_location = campos["origem"].currentText().strip()
        to_location = campos["destino"].currentText().strip()
        status_atividade = campos["status"].currentText()

        from_company_id = self._resolver_empresa(from_location)
        to_company_id = self._resolver_empresa(to_location)
        tecnico_id = self._resolver_tecnico(campos["tecnico"].currentText().strip())

        try:
            self.activity_service.criar(
                printer_id=printer.id,
                kind=kind,
                notes=notes,
                parts_used=parts_used,
                from_location=from_location,
                to_location=to_location,
                status_atividade=status_atividade,
                event_at=event_at,
                tecnico_id=tecnico_id,
            )
            self._dar_baixa_estoque(parts_used)
            atividade = self.activity_service.buscar_por_descricao(printer.id, notes)
            if atividade:
                self.activity_service.atualizar(
                    atividade,
                    from_company_id=from_company_id,
                    to_company_id=to_company_id,
                )
            self.recarregar()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao criar OS: {e}")

    def _editar(self, row):
        if row < 0 or row >= len(self._atividades):
            return
        atividade = self._atividades[row]

        dialog, campos = self._criar_form_dialog("Editar OS", atividade)

        botoes = QHBoxLayout()
        btn_salvar = QPushButton("Salvar")
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_excluir = QPushButton("Excluir")
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)
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
            data_texto = campos["data"].text().strip()
            event_at = parse_data(data_texto) if data_texto else dt.now()
            notes = campos["descricao"].toPlainText().strip()
            parts_used = campos["pecas"].toPlainText().strip()
            from_location = campos["origem"].currentText().strip()
            to_location = campos["destino"].currentText().strip()
            status_atividade = campos["status"].currentText()
            from_company_id = self._resolver_empresa(from_location)
            to_company_id = self._resolver_empresa(to_location)
            tecnico_id = self._resolver_tecnico(campos["tecnico"].currentText().strip())

            try:
                self.activity_service.atualizar(
                    atividade,
                    printer_id=printer.id,
                    kind=kind,
                    event_at=event_at,
                    notes=notes,
                    parts_used=parts_used,
                    from_location=from_location,
                    to_location=to_location,
                    status_atividade=status_atividade,
                    from_company_id=from_company_id,
                    to_company_id=to_company_id,
                    tecnico_id=tecnico_id,
                )
                self._dar_baixa_estoque(parts_used)
                resultado["acao"] = "salvar"
                dialog.accept()
                self.recarregar()
            except Exception as e:
                QMessageBox.critical(dialog, "Erro", f"Erro ao salvar: {e}")

        def excluir():
            resp = QMessageBox.question(
                dialog, "Confirmar", "Deseja realmente excluir esta OS?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if resp == QMessageBox.Yes:
                try:
                    self.activity_service.excluir(atividade)
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

    def _criar_form_dialog(self, titulo, atividade=None):
        dialog = QDialog(self)
        dialog.setWindowTitle(titulo)
        dialog.setMinimumWidth(520)
        dialog.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        printers = self.printer_service.listar_todos()
        nomes_impressoras = [p.patrimonio for p in printers]

        cmb_printer = QComboBox()
        cmb_printer.setEditable(True)
        configurar_combo(cmb_printer)
        cmb_printer.addItems(nomes_impressoras)
        cmb_printer.setInsertPolicy(QComboBox.NoInsert)
        form.addRow("Impressora:", cmb_printer)

        cmb_tipo = QComboBox()
        configurar_combo(cmb_tipo)
        cmb_tipo.addItems(["MANUTENCAO", "MOVIMENTACAO"])
        form.addRow("Tipo:", cmb_tipo)

        data_atual = dt.now().strftime("%d/%m/%Y %H:%M")
        edt_data = QLineEdit(data_atual)
        edt_data.setStyleSheet(ESTILO_INPUT)
        form.addRow("Data/Hora:", edt_data)

        txt_descricao = QTextEdit()
        txt_descricao.setStyleSheet(ESTILO_INPUT)
        txt_descricao.setMaximumHeight(80)
        form.addRow("Descrição:", txt_descricao)

        txt_pecas = QTextEdit()
        txt_pecas.setStyleSheet(ESTILO_INPUT)
        txt_pecas.setMaximumHeight(60)
        form.addRow("Peças Trocadas:", txt_pecas)

        estoque_combo_os = QComboBox()
        configurar_combo(estoque_combo_os)
        estoque_combo_os.addItem("-- Nenhuma --", None)
        for p in self.part_service.listar_todas():
            if p.quantidade_estoque > 0:
                estoque_combo_os.addItem(f"{p.nome} ({p.quantidade_estoque} un.)", p.id)
        form.addRow("Peça do Estoque:", estoque_combo_os)

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

        empresas = self.company_service.listar_nomes() if self.company_service else []

        cmb_origem = QComboBox()
        cmb_origem.setEditable(True)
        configurar_combo(cmb_origem)
        cmb_origem.addItems(empresas)
        cmb_origem.setInsertPolicy(QComboBox.NoInsert)
        cmb_origem.setCurrentText("")
        form.addRow("Origem:", cmb_origem)
        lbl_origem = form.labelForField(cmb_origem)

        cmb_destino = QComboBox()
        cmb_destino.setEditable(True)
        configurar_combo(cmb_destino)
        cmb_destino.addItems(empresas)
        cmb_destino.setInsertPolicy(QComboBox.NoInsert)
        cmb_destino.setCurrentText("")
        form.addRow("Destino:", cmb_destino)
        lbl_destino = form.labelForField(cmb_destino)

        def _toggle_origem_destino(tipo):
            visivel = tipo == "MOVIMENTACAO"
            lbl_origem.setVisible(visivel)
            cmb_origem.setVisible(visivel)
            lbl_destino.setVisible(visivel)
            cmb_destino.setVisible(visivel)
            if not visivel:
                cmb_origem.setCurrentText("")
                cmb_destino.setCurrentText("")
        cmb_tipo.currentTextChanged.connect(_toggle_origem_destino)
        _toggle_origem_destino(cmb_tipo.currentText())

        cmb_tecnico = QComboBox()
        cmb_tecnico.setEditable(True)
        configurar_combo(cmb_tecnico)
        if self.technician_service:
            cmb_tecnico.addItems(self.technician_service.nomes_exibicao())
        cmb_tecnico.setInsertPolicy(QComboBox.NoInsert)
        form.addRow("Técnico:", cmb_tecnico)

        cmb_status = QComboBox()
        configurar_combo(cmb_status)
        cmb_status.addItems(["Concluida", "Pendente", "Em Andamento"])
        form.addRow("Status:", cmb_status)

        layout.addLayout(form)

        campos = {
            "printer": cmb_printer,
            "tipo": cmb_tipo,
            "data": edt_data,
            "descricao": txt_descricao,
            "pecas": txt_pecas,
            "origem": cmb_origem,
            "destino": cmb_destino,
            "tecnico": cmb_tecnico,
            "status": cmb_status,
        }

        if atividade:
            self._preencher_campos(atividade, campos)

        if not atividade:
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            btn_box.button(QDialogButtonBox.Ok).setText("OK")
            btn_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
            btn_box.accepted.connect(dialog.accept)
            btn_box.rejected.connect(dialog.reject)
            layout.addWidget(btn_box)

        return dialog, campos

    def _preencher_campos(self, atividade, campos):
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

        campos["data"].setText(formatar_data_hora(atividade.event_at))
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

    def _resolver_empresa(self, nome):
        if not nome or not self.company_service:
            return None
        empresa = self.company_service.buscar_por_nome(nome)
        return empresa.id if empresa else None

    def _resolver_tecnico(self, nome):
        if not nome or not self.technician_service:
            return None
        tecnicos = self.technician_service.listar_ativos()
        for t in tecnicos:
            if t.nome_exibicao == nome or t.nome_completo == nome:
                return t.id
        return None

    def _dar_baixa_estoque(self, pecas_texto):
        if not pecas_texto:
            return
        nome_peca = pecas_texto.split(",")[0].strip()
        part = self.part_service.buscar_por_nome(nome_peca)
        if part and part.quantidade_estoque > 0:
            self.part_service.atualizar(part, quantidade_estoque=part.quantidade_estoque - 1)
