from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit, QMessageBox, QTabWidget, QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from datetime import datetime as dt
from pathlib import Path
import os
import shutil
from app.models import Activity, Printer, Attachment
from app.views.styles.theme import (COR, ESTILO_TITULO_PAGINA, ESTILO_BOTAO_SUCESSO, ESTILO_BOTAO_ERRO, ESTILO_BOTAO_FECHAR, ESTILO_INPUT, ESTILO_COMBO, ESTILO_TABELA, ESTILO_DIALOG, ESTILO_BOTAO_AVISO, ESTILO_TABELA_SIMPLES, STATUS_ATIVIDADE_OPCOES, estilos_dialogo_tabs)
from app.views.widgets.card_widget import CardMiniWidget
from app.views.widgets.table_widget import TabelaPadrao
from app.views.widgets.search_bar import SearchBar
from app.utils.helpers import formatar_data_hora, encurtar


COR_STATUS = {
    "pendente": "#f9e2af",
    "em_andamento": "#89b4fa",
    "concluida": "#a6e3a1",
}

ANEXOS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "anexos"


class TransfersPage(QWidget):
    COLUNAS = ["Data", "Patrimônio", "Origem", "Destino", "Peças/Equipamento", "Nº Recibo", "Status"]

    def __init__(self, session, printer_service, activity_service, company_service, parent=None):
        super().__init__(parent)
        self._session = session
        self.printer_service = printer_service
        self.activity_service = activity_service
        self.company_service = company_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        titulo = QLabel("\U0001f69a Transferências / Movimentações")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        header.addWidget(titulo)
        header.addStretch()

        self.btn_nova = QPushButton("➕ Nova Transferência")
        self.btn_nova.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        self.btn_nova.clicked.connect(self._nova)
        header.addWidget(self.btn_nova)
        layout.addLayout(header)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.card_total = CardMiniWidget("\U0001f4cb", "Total Transf.", "0", COR["azul"])
        self.card_saidas = CardMiniWidget("\U0001f4e4", "Saídas", "0", COR["erro"])
        self.card_entradas = CardMiniWidget("\U0001f4e5", "Entradas", "0", COR["sucesso"])
        self.card_pendentes = CardMiniWidget("\u23f3", "Pendentes", "0", COR["aviso"])
        cards.addWidget(self.card_total)
        cards.addWidget(self.card_saidas)
        cards.addWidget(self.card_entradas)
        cards.addWidget(self.card_pendentes)
        layout.addLayout(cards)

        self.search = SearchBar("Buscar por patrimônio, origem, destino...")
        self.search.textChanged().connect(self._filtrar)
        layout.addWidget(self.search)

        self.tabela = TabelaPadrao(self.COLUNAS)
        self.tabela.cellDoubleClicked.connect(self._editar)
        layout.addWidget(self.tabela)

        self._mov_cache = []
        self._mapa_cache = {}

    def recarregar(self):
        movimentacoes = self.activity_service.listar_movimentacoes(limite=200)
        printer_ids = [m.printer_id for m in movimentacoes if m.printer_id]
        self._mapa_cache = self.printer_service.mapa_patrimonio(printer_ids) if printer_ids else {}
        self._mov_cache = movimentacoes
        self._preencher_tabela(movimentacoes)

    def _preencher_tabela(self, movimentacoes):
        self.tabela.limpar()
        self.tabela.setRowCount(len(movimentacoes))
        for i, m in enumerate(movimentacoes):
            self.tabela.setItem(i, 0, QTableWidgetItem(formatar_data_hora(m.event_at)))
            patrimonio = self._mapa_cache.get(m.printer_id, m.printer_id[:8] + "...")
            self.tabela.setItem(i, 1, QTableWidgetItem(patrimonio))
            self.tabela.setItem(i, 2, QTableWidgetItem(m.from_location or "-"))
            self.tabela.setItem(i, 3, QTableWidgetItem(m.to_location or "-"))
            self.tabela.setItem(i, 4, QTableWidgetItem(encurtar(m.parts_used, 30)))
            self.tabela.setItem(i, 5, QTableWidgetItem(m.numero_recibo or "-"))
            status = (m.status_atividade or "concluida").lower()
            cor_status = COR_STATUS.get(status, "#6c7086")
            self.tabela.definir_badge(i, 6, status.capitalize(), cor_status)
        self.tabela.redimensionar()
        self._atualizar_cards(movimentacoes)

    def _atualizar_cards(self, movimentacoes):
        total = len(movimentacoes)
        saidas = sum(1 for m in movimentacoes if m.from_location and not m.to_location)
        entradas = sum(1 for m in movimentacoes if m.to_location and not m.from_location)
        pendentes = sum(1 for m in movimentacoes if (m.status_atividade or "").lower() == "pendente")
        self.card_total.atualizar_valor(total)
        self.card_saidas.atualizar_valor(saidas)
        self.card_entradas.atualizar_valor(entradas)
        self.card_pendentes.atualizar_valor(pendentes)

    def _filtrar(self, texto):
        texto = texto.strip()
        if not texto:
            self._preencher_tabela(self._mov_cache)
            return
        movimentacoes = self.activity_service.buscar_movimentacoes_por_filtro(texto, limite=200)
        printer_ids = [m.printer_id for m in movimentacoes if m.printer_id]
        self._mapa_cache = self.printer_service.mapa_patrimonio(printer_ids) if printer_ids else {}
        self._mov_cache = movimentacoes
        self._preencher_tabela(movimentacoes)

    def _nova(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nova Transferência")
        dialog.setMinimumSize(650, 550)
        dialog.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(dialog)
        tabs = QTabWidget()
        tabs.setStyleSheet(estilos_dialogo_tabs())

        tab_dados = QWidget()
        form = QFormLayout(tab_dados)
        form.setLabelAlignment(Qt.AlignRight)

        tipo_combo = QComboBox()
        tipo_combo.addItems(["Impressora Completa", "Apenas Peça(s)"])
        tipo_combo.setStyleSheet(ESTILO_COMBO)
        form.addRow("Tipo:", tipo_combo)

        printer_combo = QComboBox()
        printer_combo.setEditable(True)
        printer_combo.setStyleSheet(ESTILO_COMBO)
        printer_combo.setPlaceholderText("Digite o patrimônio")
        for p in self.printer_service.listar_todos():
            printer_combo.addItem(f"{p.patrimonio} - {p.modelo}", p.id)
        form.addRow("Impressora:", printer_combo)

        pecas_text = QTextEdit()
        pecas_text.setStyleSheet(ESTILO_INPUT)
        pecas_text.setPlaceholderText("Peças separadas por vírgula")
        pecas_text.setMaximumHeight(70)
        form.addRow("Peças:", pecas_text)

        empresas = self.company_service.listar_nomes()

        origem_combo = QComboBox()
        origem_combo.setEditable(True)
        origem_combo.setStyleSheet(ESTILO_COMBO)
        origem_combo.addItems(empresas)
        form.addRow("Origem:", origem_combo)

        destino_combo = QComboBox()
        destino_combo.setEditable(True)
        destino_combo.setStyleSheet(ESTILO_COMBO)
        destino_combo.addItems(empresas)
        form.addRow("Destino:", destino_combo)

        recibo_input = QLineEdit()
        recibo_input.setStyleSheet(ESTILO_INPUT)
        recibo_input.setPlaceholderText("Número do recibo")
        form.addRow("Nº Recibo:", recibo_input)

        obs_text = QTextEdit()
        obs_text.setStyleSheet(ESTILO_INPUT)
        obs_text.setPlaceholderText("Observações")
        obs_text.setMaximumHeight(70)
        form.addRow("Observação:", obs_text)

        status_combo = QComboBox()
        status_combo.setStyleSheet(ESTILO_COMBO)
        status_combo.addItems(STATUS_ATIVIDADE_OPCOES)
        form.addRow("Status:", status_combo)

        tabs.addTab(tab_dados, "\U0001f4cb Dados")

        tab_anexos_vazia = QWidget()
        anexos_layout = QVBoxLayout(tab_anexos_vazia)
        lbl_aviso = QLabel("Salve primeiro para anexar arquivos.")
        lbl_aviso.setStyleSheet("color: #6c7086; font-size: 13px;")
        lbl_aviso.setAlignment(Qt.AlignCenter)
        anexos_layout.addWidget(lbl_aviso)
        tabs.addTab(tab_anexos_vazia, "\U0001f4ce Anexos")

        layout.addWidget(tabs)

        btn_salvar = QPushButton("\U0001f4be Salvar")
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        layout.addWidget(btn_salvar)

        saved_id = [None]

        def salvar_nova():
            patrimonio_texto = printer_combo.currentText().split(" - ")[0].strip()
            printer = self.printer_service.buscar_por_patrimonio(patrimonio_texto)
            if not printer:
                QMessageBox.warning(dialog, "Aviso", "Impressora não encontrada. Verifique o patrimônio.")
                return

            try:
                activity = Activity(
                    printer_id=printer.id,
                    kind="MOVIMENTACAO",
                    event_at=dt.now(),
                    parts_used=pecas_text.toPlainText().strip(),
                    from_location=origem_combo.currentText().strip(),
                    to_location=destino_combo.currentText().strip(),
                    notes=obs_text.toPlainText().strip(),
                    numero_recibo=recibo_input.text().strip(),
                    status_atividade=status_combo.currentText(),
                )
                self._session.add(activity)
                self._session.commit()
                saved_id[0] = activity.id

                tabs.removeTab(1)

                def callback_fechar():
                    dialog.accept()

                real_anexos = self._criar_tab_anexos(
                    "activity", activity.id, dialog, callback_fechar, tabs
                )
                tabs.addTab(real_anexos, "\U0001f4ce Anexos")
                tabs.setCurrentIndex(0)

                QMessageBox.information(dialog, "Sucesso", "Transferência salva!")
                btn_salvar.setText("\u2705 Salvo")
                btn_salvar.setEnabled(False)
            except Exception as e:
                self._session.rollback()
                QMessageBox.critical(dialog, "Erro", f"Erro ao salvar:\n{e}")

        btn_salvar.clicked.connect(salvar_nova)

        if dialog.exec() == QDialog.Accepted:
            self.recarregar()

    def _editar(self, row):
        movimentacoes = self.activity_service.listar_movimentacoes(limite=200)
        if row < 0 or row >= len(movimentacoes):
            return
        mov = movimentacoes[row]
        printer = self.printer_service.buscar_por_id(mov.printer_id)
        patrimonio = f"{printer.patrimonio} - {printer.modelo}" if printer else mov.printer_id

        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Transferência")
        dialog.setMinimumSize(650, 550)
        dialog.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(dialog)
        tabs = QTabWidget()
        tabs.setStyleSheet(estilos_dialogo_tabs())

        tab_dados = QWidget()
        form = QFormLayout(tab_dados)
        form.setLabelAlignment(Qt.AlignRight)

        orig = {
            "printer_id": mov.printer_id,
            "parts_used": mov.parts_used,
            "from_location": mov.from_location,
            "to_location": mov.to_location,
            "notes": mov.notes,
            "numero_recibo": mov.numero_recibo,
            "status_atividade": mov.status_atividade,
        }

        lbl_printer = QLabel(patrimonio)
        lbl_printer.setStyleSheet("color: #c0c0d0; font-size: 13px; background: transparent;")
        form.addRow("Impressora:", lbl_printer)

        lbl_data = QLabel(formatar_data_hora(mov.event_at))
        lbl_data.setStyleSheet("color: #c0c0d0; font-size: 13px; background: transparent;")
        form.addRow("Data/Hora:", lbl_data)

        pecas_text = QTextEdit()
        pecas_text.setStyleSheet(ESTILO_INPUT)
        pecas_text.setText(mov.parts_used or "")
        pecas_text.setMaximumHeight(70)
        form.addRow("Peças:", pecas_text)

        empresas = self.company_service.listar_nomes()

        origem_combo = QComboBox()
        origem_combo.setEditable(True)
        origem_combo.setStyleSheet(ESTILO_COMBO)
        origem_combo.addItems(empresas)
        if mov.from_location:
            idx = origem_combo.findText(mov.from_location)
            if idx >= 0:
                origem_combo.setCurrentIndex(idx)
            else:
                origem_combo.setEditText(mov.from_location)
        form.addRow("Origem:", origem_combo)

        destino_combo = QComboBox()
        destino_combo.setEditable(True)
        destino_combo.setStyleSheet(ESTILO_COMBO)
        destino_combo.addItems(empresas)
        if mov.to_location:
            idx = destino_combo.findText(mov.to_location)
            if idx >= 0:
                destino_combo.setCurrentIndex(idx)
            else:
                destino_combo.setEditText(mov.to_location)
        form.addRow("Destino:", destino_combo)

        recibo_input = QLineEdit()
        recibo_input.setStyleSheet(ESTILO_INPUT)
        recibo_input.setText(mov.numero_recibo or "")
        form.addRow("Recibo:", recibo_input)

        obs_text = QTextEdit()
        obs_text.setStyleSheet(ESTILO_INPUT)
        obs_text.setText(mov.notes or "")
        obs_text.setMaximumHeight(70)
        form.addRow("Observação:", obs_text)

        status_combo = QComboBox()
        status_combo.setStyleSheet(ESTILO_COMBO)
        status_combo.addItems(STATUS_ATIVIDADE_OPCOES)
        sidx = status_combo.findText(mov.status_atividade or "Concluida", Qt.MatchFixedString)
        if sidx >= 0:
            status_combo.setCurrentIndex(sidx)
        form.addRow("Status:", status_combo)

        tabs.addTab(tab_dados, "\U0001f4cb Dados")

        def salvar_edicao():
            novos = {
                "parts_used": pecas_text.toPlainText().strip(),
                "from_location": origem_combo.currentText().strip(),
                "to_location": destino_combo.currentText().strip(),
                "notes": obs_text.toPlainText().strip(),
                "numero_recibo": recibo_input.text().strip(),
                "status_atividade": status_combo.currentText(),
            }
            if novos == orig:
                return
            try:
                for chave, valor in novos.items():
                    setattr(mov, chave, valor)
                self._session.commit()
                orig.update(novos)
                QMessageBox.information(dialog, "Sucesso", "Alterações salvas!")
            except Exception as e:
                self._session.rollback()
                QMessageBox.critical(dialog, "Erro", f"Erro ao salvar:\n{e}")

        tab_anexos = self._criar_tab_anexos("activity", mov.id, dialog, salvar_edicao, tabs)
        tabs.addTab(tab_anexos, "\U0001f4ce Anexos")

        layout.addWidget(tabs)

        botoes = QHBoxLayout()
        botoes.setSpacing(10)

        btn_salvar = QPushButton("\U0001f4be Salvar")
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_salvar.clicked.connect(salvar_edicao)
        botoes.addWidget(btn_salvar)

        btn_excluir = QPushButton("\U0001f5d1\ufe0f Excluir")
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_excluir.clicked.connect(lambda: self._confirmar_exclusao(dialog, mov))
        botoes.addWidget(btn_excluir)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_cancelar.clicked.connect(dialog.reject)
        botoes.addWidget(btn_cancelar)

        layout.addLayout(botoes)

        alterado = [False]

        def marcar_alterado():
            alterado[0] = True

        pecas_text.textChanged.connect(marcar_alterado)
        origem_combo.currentTextChanged.connect(marcar_alterado)
        destino_combo.currentTextChanged.connect(marcar_alterado)
        recibo_input.textChanged.connect(marcar_alterado)
        obs_text.textChanged.connect(marcar_alterado)
        status_combo.currentTextChanged.connect(marcar_alterado)

        original_close = dialog.closeEvent

        def close_event(event):
            if alterado[0]:
                resposta = QMessageBox.question(
                    dialog, "Alterações não salvas",
                    "Deseja salvar as alterações antes de fechar?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Yes,
                )
                if resposta == QMessageBox.Yes:
                    salvar_edicao()
                    event.accept()
                elif resposta == QMessageBox.No:
                    self._session.rollback()
                    event.accept()
                else:
                    event.ignore()
            else:
                event.accept()

        dialog.closeEvent = close_event

        dialog.exec()
        self.recarregar()

    def _confirmar_exclusao(self, dialog, mov):
        resposta = QMessageBox.question(
            dialog, "Confirmar Exclusão",
            "Tem certeza que deseja excluir esta transferência?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resposta == QMessageBox.Yes:
            try:
                self._session.delete(mov)
                self._session.commit()
                dialog.accept()
            except Exception as e:
                self._session.rollback()
                QMessageBox.critical(dialog, "Erro", f"Erro ao excluir:\n{e}")

    def _criar_tab_anexos(self, entity_type, entity_id, dialog, callback_salvar, tabs):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        tabela_anexos = QTableWidget()
        tabela_anexos.setColumnCount(4)
        tabela_anexos.setHorizontalHeaderLabels(["Arquivo", "Categoria", "Data", "Abrir"])
        tabela_anexos.setStyleSheet(ESTILO_TABELA_SIMPLES)
        tabela_anexos.horizontalHeader().setStretchLastSection(True)
        tabela_anexos.setSelectionBehavior(QAbstractItemView.SelectRows)
        tabela_anexos.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tabela_anexos.verticalHeader().setVisible(False)
        tabela_anexos.setAlternatingRowColors(True)

        anexos = self._session.query(Attachment).filter_by(
            entity_type=entity_type, entity_id=entity_id
        ).order_by(Attachment.created_at.desc()).all()

        tabela_anexos.setRowCount(len(anexos))
        for i, a in enumerate(anexos):
            tabela_anexos.setItem(i, 0, QTableWidgetItem(a.original_name))
            tabela_anexos.setItem(i, 1, QTableWidgetItem(a.categoria or "-"))
            tabela_anexos.setItem(i, 2, QTableWidgetItem(formatar_data_hora(a.created_at)))
            btn_abrir = QPushButton("\U0001f4c2 Abrir")
            btn_abrir.setStyleSheet("""
                QPushButton {
                    background-color: #45475a; color: #cdd6f4;
                    border: none; border-radius: 4px;
                    padding: 4px 12px; font-size: 11px;
                }
                QPushButton:hover { background-color: #585b70; }
            """)
            file_path = a.file_path
            btn_abrir.clicked.connect(lambda checked, fp=file_path: self._abrir_anexo(fp))
            tabela_anexos.setCellWidget(i, 3, btn_abrir)

        tabela_anexos.resizeColumnsToContents()
        tabela_anexos.resizeRowsToContents()
        tabela_anexos.verticalHeader().setDefaultSectionSize(32)
        layout.addWidget(tabela_anexos)

        botoes_anexos = QHBoxLayout()
        btn_adicionar = QPushButton("\U0001f4ce Adicionar Anexo")
        btn_adicionar.setStyleSheet(ESTILO_BOTAO_AVISO)

        btn_adicionar.clicked.connect(
            lambda: self._anexar_arquivo(entity_type, entity_id, dialog, callback_salvar, tabs)
        )
        botoes_anexos.addWidget(btn_adicionar)

        btn_salvar_tab = QPushButton("\U0001f4be Salvar")
        btn_salvar_tab.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        if callback_salvar:
            btn_salvar_tab.clicked.connect(callback_salvar)
        botoes_anexos.addWidget(btn_salvar_tab)

        layout.addLayout(botoes_anexos)
        return tab

    def _anexar_arquivo(self, entity_type, entity_id, dialog, callback_salvar, tabs):
        file_path, _ = QFileDialog.getOpenFileName(
            dialog, "Selecionar Arquivo",
            "",
            "Todos os arquivos (*.*)",
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
                ".pdf": "application/pdf",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".doc": "application/msword",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".xls": "application/vnd.ms-excel",
                ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".txt": "text/plain",
            }
            mime_type = mime_map.get(ext, "application/octet-stream")

            attachment = Attachment(
                entity_type=entity_type,
                entity_id=entity_id,
                filename=safe_name,
                original_name=original_name,
                file_path=dest_path,
                mime_type=mime_type,
                size_bytes=os.path.getsize(file_path),
                categoria="recibo",
            )
            self._session.add(attachment)
            self._session.commit()

            idx = tabs.currentIndex()
            tabs.removeTab(1)
            nova_tab = self._criar_tab_anexos(entity_type, entity_id, dialog, callback_salvar, tabs)
            tabs.addTab(nova_tab, "\U0001f4ce Anexos")
            tabs.setCurrentIndex(idx)
        except Exception as e:
            self._session.rollback()
            QMessageBox.critical(dialog, "Erro", f"Erro ao anexar arquivo:\n{e}")

    def _abrir_anexo(self, file_path):
        if os.path.exists(file_path):
            os.startfile(file_path)
        else:
            QMessageBox.warning(self, "Aviso", "Arquivo não encontrado:\n" + file_path)
