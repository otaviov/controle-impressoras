from __future__ import annotations

import csv
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import os
import sys


from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QMessageBox,
    QComboBox, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QDialog, QDialogButtonBox,
    QFileDialog, QTabWidget, QAbstractItemView, QGroupBox, QInputDialog
)

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from models import Printer, Activity, simple_uuid

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# garantir que o executavel encontre a logo
def resource_path(relative_path):
    try:
        # cria uma pasta temporária e armazena
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

STATUSES = ["Operacional", "Em Manutenção", "Parada", "Aguardando peça", "Em uso", "Sucata"]


class MainWindow(QWidget):
    def __init__(self, session: Session):
        super().__init__()

        self.session = session
        self.current_id: str | None = None

        self.setWindowTitle("Controle de Impressoras")
        self.resize(1250, 720)

        # temas 
        self.base_dir = Path(__file__).resolve().parent
        self.themes_dir = self.base_dir / "themes"

        # ROOT
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        # TOP BAR
        top = QFrame()
        top.setObjectName("TopBar")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(12, 10, 12, 10)
        top_layout.setSpacing(10)

        title_box = QVBoxLayout()
        self.lbl_title = QLabel("Controle de Impressoras")
        self.lbl_title.setObjectName("TopTitle")
        self.lbl_hint = QLabel("Selecione uma impressora → veja histórico, registre atividades e gere relatório.")
        self.lbl_hint.setObjectName("TopHint")
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_hint)

        top_layout.addLayout(title_box)
        top_layout.addStretch()

        top_layout.addWidget(QLabel("Tema:"))
        self.theme_combo = QComboBox()
        self.theme_combo.setFixedWidth(180)
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        top_layout.addWidget(self.theme_combo)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar por patrimônio, modelo, serial ou local…")
        self.search.textChanged.connect(self.refresh_table)
        self.search.setMinimumWidth(360)
        top_layout.addWidget(self.search)

        root.addWidget(top)

        # BODY
        body = QHBoxLayout()
        body.setSpacing(12)
        root.addLayout(body)

        # LEFT
        left_card = QFrame()
        left_card.setObjectName("Card")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        left_layout.addWidget(self._section_title("Impressoras"))

        self.table = QTableWidget(0, 5)
        self.table.setObjectName("PrintersTable")
        self.table.setHorizontalHeaderLabels(["Patrimônio", "Modelo", "Serial", "Status", "Local"])
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.cellClicked.connect(self.on_select_row)

        left_layout.addWidget(self.table)
        body.addWidget(left_card, 3)

        # RIGHT
        right_card = QFrame()
        right_card.setObjectName("Card")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("MainTabs")
        right_layout.addWidget(self.tabs)

        self.tab_details = QWidget()
        self.tab_history = QWidget()
        self.tab_reports = QWidget()

        self.tabs.addTab(self.tab_details, "Detalhes")
        self.tabs.addTab(self.tab_history, "Histórico")
        self.tabs.addTab(self.tab_reports, "Relatórios")

        body.addWidget(right_card, 2)

        # DETALHES
        details = QVBoxLayout(self.tab_details)
        details.setContentsMargins(10, 10, 10, 10)
        details.setSpacing(10)

        self.lbl_counter = QLabel("Manutenções: 0")
        self.lbl_counter.setObjectName("Counter")
        details.addWidget(self.lbl_counter)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        self.patrimonio = QLineEdit()
        self.modelo = QLineEdit()
        self.serial = QLineEdit()

        self.status = QComboBox()
        self.status.addItems(STATUSES)

        self.local = QLineEdit()
        
        # Teste de novos campos
        self.pecas_faltantes = QLineEdit()
        self.pecas_faltantes.setPlaceholderText("Ex: Flat do Scanner, ADF Motor...")

        self.tecnico_revisao = QLineEdit()
        self.tecnico_revisao.setPlaceholderText("Nome do técnico que revisou")

        self.data_revisao = QLineEdit()
        self.data_revisao.setPlaceholderText("DD/MM/AAAA")
        self.data_revisao.setText(datetime.now().strftime("%d/%m/%Y"))

        self.obs = QTextEdit()
        self.obs.setPlaceholderText("Observações gerais da máquina…")

        form.addRow("Patrimônio/Tag", self.patrimonio)
        form.addRow("Modelo", self.modelo)
        form.addRow("Serial", self.serial)
        form.addRow("Status", self.status)
        form.addRow("Local atual", self.local)

        # --- Teste de novos campos ---
        form.addRow("Peças Faltantes:", self.pecas_faltantes)
        form.addRow("Técnico Revisor:", self.tecnico_revisao)
        form.addRow("Data da Revisão:", self.data_revisao)

        form.addRow("Observação", self.obs)

        details.addLayout(form)

        btns = QHBoxLayout()
        btns.setSpacing(24)

        self.btn_new = QPushButton("Novo")
        self.btn_save = QPushButton("Salvar")
        self.btn_delete = QPushButton("Excluir")

        self.btn_save.setObjectName("Primary")
        self.btn_delete.setObjectName("Danger")

        self.btn_new.clicked.connect(self.clear_form)
        self.btn_save.clicked.connect(self.save)
        self.btn_delete.clicked.connect(self.delete)

        btns.addWidget(self.btn_new)
        btns.addWidget(self.btn_save)
        btns.addWidget(self.btn_delete)
        btns.setAlignment(Qt.AlignCenter)

        details.addLayout(btns)

        # HISTORICO
        history = QVBoxLayout(self.tab_history)
        history.setContentsMargins(10, 10, 10, 10)
        history.setSpacing(10)

        top_hist = QHBoxLayout()
        top_hist.setSpacing(10)

        self.btn_add_activity = QPushButton("Registrar atividade")
        self.btn_add_activity.setObjectName("Primary")
        self.btn_add_activity.clicked.connect(self.open_activity_dialog)

        self.btn_edit_activity = QPushButton("Editar atividade")
        self.btn_edit_activity.clicked.connect(self.edit_selected_activity)

        self.btn_delete_activity = QPushButton("Excluir atividade")
        self.btn_delete_activity.setObjectName("Danger")
        self.btn_delete_activity.clicked.connect(self.delete_selected_activity)

        top_hist.addWidget(self.btn_add_activity)
        top_hist.addWidget(self.btn_edit_activity)
        top_hist.addWidget(self.btn_delete_activity)
        top_hist.addStretch()
        history.addLayout(top_hist)

        self.history_table = QTableWidget(0, 6)
        self.history_table.setObjectName("HistoryTable")
        self.history_table.setHorizontalHeaderLabels(["Data/Hora", "Tipo", "Descrição", "Peças", "De", "Para"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setAlternatingRowColors(True)

        # Deixa a tabela mais limpa
        self.history_table.setShowGrid(False)
        self.history_table.setWordWrap(True)
        self.history_table.setSelectionMode(QAbstractItemView.SingleSelection)

        hh = self.history_table.horizontalHeader()
        hh.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Data
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Tipo
        hh.setSectionResizeMode(2, QHeaderView.Stretch)           # Descrição
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Peças
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # De
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Para

        self.history_table.verticalHeader().setDefaultSectionSize(44)

        history.addWidget(self.history_table)

        # RELATORIOS
        reports = QVBoxLayout(self.tab_reports)
        reports.setContentsMargins(20, 20, 20, 20)
        reports.setSpacing(20)

        reports.addWidget(self._section_title("Exportação de Relatórios"))

        desc = QLabel(
            "Exporte relatórios da impressora selecionada ou gere relatórios completos do sistema."
        )
        desc.setWordWrap(True)
        reports.addWidget(desc)

        # ---------- RELATORIO DA IMPRESSORA ----------
        box_printer = QGroupBox("Relatórios da Impressora Selecionada")
        layout_printer = QVBoxLayout(box_printer)
        layout_printer.setSpacing(10)

        self.btn_export_csv = QPushButton("Baixar Relatório (CSV)")
        self.btn_export_pdf = QPushButton("Baixar Relatório (PDF)")

        self.btn_export_csv.setMinimumHeight(36)
        self.btn_export_pdf.setMinimumHeight(36)

        layout_printer.addWidget(self.btn_export_csv)
        layout_printer.addWidget(self.btn_export_pdf)

        reports.addWidget(box_printer)

        # ---------- RELATORIOS COMPLETOS ----------
        box_all = QGroupBox("Relatórios Completos do Sistema (Todas Impressoras)")
        layout_all = QVBoxLayout(box_all)
        layout_all.setSpacing(10)

        self.btn_export_all_csv = QPushButton("Baixar Relatório Completo (CSV)")
        self.btn_export_all_pdf = QPushButton("Baixar Relatório Completo (PDF)")

        self.btn_export_all_csv.setMinimumHeight(36)
        self.btn_export_all_pdf.setMinimumHeight(36)

        layout_all.addWidget(self.btn_export_all_csv)
        layout_all.addWidget(self.btn_export_all_pdf)

        reports.addWidget(box_all)

        # conexões
        self.btn_export_csv.clicked.connect(self.export_history_csv)
        self.btn_export_pdf.clicked.connect(self.export_pdf)

        self.btn_export_all_csv.clicked.connect(self.export_all_csv)
        self.btn_export_all_pdf.clicked.connect(self.export_all_pdf)

        # aviso
        self.lbl_report_hint = QLabel(
            "Selecione uma impressora na tabela para gerar relatório individual."
        )
        self.lbl_report_hint.setObjectName("TopHint")
        reports.addWidget(self.lbl_report_hint)

        reports.addStretch()

        # temas + data
        self._populate_themes()
        self.apply_theme(self.theme_combo.currentText() or "dark")
        self.refresh_table()

    # ---------------- UI ----------------
    def _section_title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        #lbl.setObjectName("SectionTitle")
        lbl.setAlignment(Qt.AlignCenter) # para centralizar
        font = lbl.font()
        font.setPointSize(16) # aumentar a fonte
        font.setBold(True)
        lbl.setFont(font)

        lbl.setContentsMargins(0, 0, 0, 0) # Remove o espaço entre o titulo e o QLabel
        lbl.setMinimumHeight(30)
        lbl.setMaximumHeight(30)
        return lbl


    def _populate_themes(self):
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()

        themes = sorted([p.stem for p in self.themes_dir.glob("*.qss")])
        if not themes:
            themes = ["dark", "light", "blue", "hacker", "dracula", "nord", "tokyo_night"]

        self.theme_combo.addItems(themes)

        if "dark" in themes:
            self.theme_combo.setCurrentText("dark")
        else:
            self.theme_combo.setCurrentIndex(0)

        self.theme_combo.blockSignals(False)

    def apply_theme(self, theme_name: str):
        qss_path = self.themes_dir / f"{theme_name}.qss"
        if qss_path.exists():
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    # ---------------- Impressoras ----------------
    def refresh_table(self):
        self.table.setSortingEnabled(False)

        q = (self.search.text() or "").strip().lower()
        printers = self.session.query(Printer).order_by(Printer.updated_at.desc()).all()

        if q:

            def hit(p: Printer) -> bool:
                fields = [
                    p.patrimonio or "",
                    p.modelo or "",
                    p.serial or "",
                    p.status or "",
                    p.local_atual or "",
                ]
                return any(q in f.lower() for f in fields)

            printers = [p for p in printers if hit(p)]

        self.table.setRowCount(0)

        for p in printers:
            row = self.table.rowCount()
            self.table.insertRow(row)

            values = [p.patrimonio, p.modelo, p.serial, p.status, p.local_atual]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val or "")
                item.setData(Qt.UserRole, p.id)
                self.table.setItem(row, col, item)

            # CORES AUTOMATICAS PARA OS STATUS
            status = (p.status or ""). lower()
            cor_fundo = None
            cor_texto = QColor(255, 255, 255)  # branco padrão

            if "Operacional" in status or "operacional" in status: 
                cor_fundo = QColor(46, 204, 113) # Verde
                cor_texto = QColor(0,0,0)
            elif "Manut" in status or "manut" in status:
                cor_fundo = QColor(255, 238, 140) # Amarelo
                cor_texto = QColor(0,0,0)
            elif "Parada" in status or "parada" in status:
                cor_fundo = QColor(231, 76, 60) # Vermelho
                cor_texto = QColor(0,0,0)
            elif "Sucata" in status or "sucata" in status: 
                cor_fundo = QColor(120, 120, 120) # Cinza
            elif "Uso" in status or "uso" in status:
                cor_fundo = QColor(85, 169, 220) # Azul
                cor_texto = QColor(0,0,0)
            elif "Aguardando" in status or "aguardando" in status:
                cor_fundo = QColor(255, 165, 0) # Laranja
                cor_texto = QColor(0,0,0)

            if cor_fundo:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    item.setBackground(cor_fundo)
                    item.setForeground(cor_texto)
 
        self.table.setSortingEnabled(True)
        self.table.resizeRowsToContents()

    def on_select_row(self, row: int, col: int):
        item = self.table.item(row, 0)
        if not item:
            return

        pid = item.data(Qt.UserRole)
        p = self.session.get(Printer, pid)
        if not p:
            return

        self.current_id = p.id
        self.patrimonio.setText(p.patrimonio)
        self.modelo.setText(p.modelo)
        self.serial.setText(p.serial)
        self.status.setCurrentText(p.status)
        self.local.setText(p.local_atual)
        self.pecas_faltantes.setText(p.pecas_faltantes or "")
        self.tecnico_revisao.setText(p.tecnico_revisao or "")
        if p.ultima_revisao_data:
            self.data_revisao.setText(p.ultima_revisao_data.strftime("%d/%m/%Y"))
        else:
            self.data_revisao.setText(datetime.now().strftime("%d/%m/%Y"))
        self.obs.setPlainText(p.observacao or "")

        self.update_counter()
        self.load_history()

    def clear_form(self):
        self.current_id = None
        self.patrimonio.clear()
        self.modelo.clear()
        self.serial.clear()
        self.status.setCurrentText("Operacional")
        self.local.clear()
        self.pecas_faltantes.clear()
        self.tecnico_revisao.clear()
        self.data_revisao.setText(datetime.now().strftime("%d/%m/%Y"))
        self.obs.clear()
        self.history_table.setRowCount(0)
        self.lbl_counter.setText("Manutenções: 0")

    def brasil_now(self):
        return datetime.now(ZoneInfo("America/Sao_Paulo"))

    def save(self):
        pat = self.patrimonio.text().strip()
        mod = self.modelo.text().strip()
        ser = self.serial.text().strip()

        print("CURRENT ID:", self.current_id)

        if not (pat or mod or ser):
            QMessageBox.warning(
                self,
                "Atenção",
                "Preencha pelo menos Patrimônio OU Modelo OU Serial."
            )
            return

        if pat:
            existente = (
                self.session.query(Printer)
                .filter(Printer.patrimonio == pat)
                .first()
            )

            if existente and (not self.current_id or existente.id != self.current_id):
                QMessageBox.warning(
                    self,
                    "Atenção",
                    "Já existe uma impressora com esse patrimônio."
                )
                return

        now = self.brasil_now()

        # Busca ou Cria a impressora
        if self.current_id:
            p = self.session.get(Printer, self.current_id)
            if not p:
                QMessageBox.warning(self, "Atenção", "Registro não encontrado.")
                return
        else:
            from models import simple_uuid
            p = Printer(id=simple_uuid(), created_at=now)
            self.session.add(p)

        # --- ATUALIZACAO DOS CAMPOS ---
        p.patrimonio = pat
        p.modelo = mod
        p.serial = ser
        p.status = self.status.currentText()
        p.local_atual = self.local.text().strip()
        p.observacao = self.obs.toPlainText().strip()
        p.pecas_faltantes = self.pecas_faltantes.text().strip()
        p.tecnico_revisao = self.tecnico_revisao.text().strip()
        
        # Converte o texto "DD/MM/AAAA" para objeto datetime
        data_texto = self.data_revisao.text().strip()
        if data_texto:
            try:
                p.ultima_revisao_data = datetime.strptime(data_texto, "%d/%m/%Y")
            except ValueError:
                QMessageBox.warning(self, "Data Inválida", "Use o formato DD/MM/AAAA na data de revisão.")
                return
        else:
            p.ultima_revisao_data = None

        p.updated_at = now

        try:
            self.session.commit()
            self.current_id = p.id

            self.refresh_table()
            self.update_counter()
            self.load_history()

            QMessageBox.information(self, "OK", "Salvo com sucesso!")
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao salvar no banco: {str(e)}")

    def delete(self):
        if not self.current_id:
            QMessageBox.information(self, "Atenção", "Selecione uma impressora para excluir.")
            return

        confirm = QMessageBox.question(self, "Confirmar", "Tem certeza que quer excluir esta impressora?")
        if confirm != QMessageBox.Yes:
            return

        self.session.query(Activity).filter(Activity.printer_id == self.current_id).delete()
        p = self.session.get(Printer, self.current_id)
        if p:
            self.session.delete(p)

        self.session.commit()
        self.clear_form()
        self.refresh_table()


    # ---------------- Contador ----------------
    def update_counter(self):
        if not self.current_id:
            self.lbl_counter.setText("Manutenções: 0")
            return

        cnt = (
            self.session.query(Activity)
            .filter(Activity.printer_id == self.current_id)
            .filter(Activity.kind == "MANUTENCAO")
            .count()
        )
        self.lbl_counter.setText(f"Manutenções: {cnt}")

    # ---------------- Histórico ----------------
    def load_history(self):
        self.history_table.setRowCount(0)
        if not self.current_id:
            return

        acts = (
            self.session.query(Activity)
            .filter(Activity.printer_id == self.current_id)
            .order_by(Activity.event_at.desc())
            .all()
        )

        for a in acts:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)

            dt = a.event_at.strftime("%d/%m/%Y %H:%M")
            kind = "Manutenção" if a.kind == "MANUTENCAO" else "Movimentação"

            it0 = QTableWidgetItem(dt)
            it0.setData(Qt.UserRole, a.id)
            self.history_table.setItem(row, 0, it0)

            self.history_table.setItem(row, 1, QTableWidgetItem(kind))

            desc = (a.notes or "").strip()
            desc_preview = desc if len(desc) <= 90 else desc[:90] + "…"
            item_desc = QTableWidgetItem(desc_preview)
            item_desc.setToolTip(desc)
            self.history_table.setItem(row, 2, item_desc)

            parts_txt = (a.parts_used or "").strip()
            parts_preview = parts_txt if len(parts_txt) <= 60 else parts_txt[:60] + "…"
            item_parts = QTableWidgetItem(parts_preview)
            item_parts.setToolTip(parts_txt)
            self.history_table.setItem(row, 3, item_parts)

            self.history_table.setItem(row, 4, QTableWidgetItem((a.from_location or "").strip()))
            self.history_table.setItem(row, 5, QTableWidgetItem((a.to_location or "").strip()))

            self.history_table.setRowHeight(row, 44)

    def get_selected_activity_id(self) -> int | None:
        row = self.history_table.currentRow()
        if row < 0:
            return None
        item = self.history_table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)

    def open_activity_dialog(self):
        if not self.current_id:
            QMessageBox.information(self, "Atenção", "Selecione uma impressora primeiro.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Registrar atividade")
        layout = QVBoxLayout(dlg)

        form = QFormLayout()
        layout.addLayout(form)

        kind = QComboBox()
        kind.addItems(["MANUTENCAO", "MOVIMENTACAO"])
        form.addRow("Tipo:", kind)

        notes = QTextEdit()
        notes.setPlaceholderText("Descreva o que foi feito / motivo / detalhes…")
        form.addRow("Descrição (obrigatório):", notes)

        parts = QLineEdit()
        parts.setPlaceholderText("Opcional: peças trocadas (ex: fusor, rolo, placa fonte)")
        form.addRow("Peças trocadas:", parts)

        dt_manual = QLineEdit()
        dt_manual.setPlaceholderText("Opcional: DD/MM/AAAA HH:MM  (ex: 09/02/2026 14:30)")
        form.addRow("Data/Hora manual:", dt_manual)

        from_loc = QLineEdit()
        to_loc = QLineEdit()
        from_loc.setPlaceholderText("Ex: Direção, RH, Sala 02…")
        to_loc.setPlaceholderText("Ex: Manutenção, Depósito, Unidade Natal…")
        form.addRow("De (movimentação):", from_loc)
        form.addRow("Para (movimentação):", to_loc)

        def toggle_move_fields():
            is_move = kind.currentText() == "MOVIMENTACAO"
            from_loc.setEnabled(is_move)
            to_loc.setEnabled(is_move)

        kind.currentTextChanged.connect(toggle_move_fields)
        toggle_move_fields()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)

        if dlg.exec() != QDialog.Accepted:
            return

        desc = notes.toPlainText().strip()
        if not desc:
            QMessageBox.warning(self, "Atenção", "A descrição é obrigatória.")
            return

        manual_txt = dt_manual.text().strip()
        if manual_txt:
            try:
                event_at = datetime.strptime(manual_txt, "%d/%m/%Y %H:%M")
            except ValueError:
                QMessageBox.warning(self, "Atenção", "Data/hora inválida. Use: DD/MM/AAAA HH:MM")
                return
        else:
            event_at = datetime.utcnow()

        k = kind.currentText()

        act = Activity(
            printer_id=self.current_id,
            kind=k,
            event_at=event_at,
            notes=desc,
            parts_used=parts.text().strip(),
            from_location=from_loc.text().strip() if k == "MOVIMENTACAO" else "",
            to_location=to_loc.text().strip() if k == "MOVIMENTACAO" else "",
        )

        if k == "MOVIMENTACAO":
            if not act.to_location:
                QMessageBox.warning(self, "Atenção", "Em movimentação, o campo 'Para' é obrigatório.")
                return

            p = self.session.get(Printer, self.current_id)
            if p:
                p.local_atual = act.to_location
                p.updated_at = datetime.utcnow()
                self.session.add(p)

        try:
            self.session.add(act)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erro ao salvar atividade", f"{e}")
            return

        self.refresh_table()
        self.update_counter()
        self.load_history()
        QMessageBox.information(self, "OK", "Atividade registrada!")

    def edit_selected_activity(self):
        act_id = self.get_selected_activity_id()
        if not act_id:
            QMessageBox.information(self, "Atenção", "Selecione uma atividade no histórico.")
            return

        a = self.session.get(Activity, act_id)
        if not a:
            QMessageBox.warning(self, "Atenção", "Atividade não encontrada.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Editar atividade")
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        layout.addLayout(form)

        kind = QComboBox()
        kind.addItems(["MANUTENCAO", "MOVIMENTACAO"])
        kind.setCurrentText(a.kind)

        notes = QTextEdit()
        notes.setPlainText(a.notes or "")

        parts = QLineEdit()
        parts.setText(a.parts_used or "")

        dt_manual = QLineEdit()
        dt_manual.setText(a.event_at.strftime("%d/%m/%Y %H:%M"))

        from_loc = QLineEdit()
        from_loc.setText(a.from_location or "")

        to_loc = QLineEdit()
        to_loc.setText(a.to_location or "")

        form.addRow("Tipo:", kind)
        form.addRow("Descrição:", notes)
        form.addRow("Peças trocadas:", parts)
        form.addRow("Data/Hora (DD/MM/AAAA HH:MM):", dt_manual)
        form.addRow("De (movimentação):", from_loc)
        form.addRow("Para (movimentação):", to_loc)

        def toggle_move_fields():
            is_move = kind.currentText() == "MOVIMENTACAO"
            from_loc.setEnabled(is_move)
            to_loc.setEnabled(is_move)

        kind.currentTextChanged.connect(toggle_move_fields)
        toggle_move_fields()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)

        if dlg.exec() != QDialog.Accepted:
            return

        desc = notes.toPlainText().strip()
        if not desc:
            QMessageBox.warning(self, "Atenção", "A descrição é obrigatória.")
            return

        try:
            event_at = datetime.strptime(dt_manual.text().strip(), "%d/%m/%Y %H:%M")
        except ValueError:
            QMessageBox.warning(self, "Atenção", "Data/hora inválida. Use: DD/MM/AAAA HH:MM")
            return

        a.kind = kind.currentText()
        a.notes = desc
        a.parts_used = parts.text().strip()
        a.event_at = event_at
        a.from_location = from_loc.text().strip() if a.kind == "MOVIMENTACAO" else ""
        a.to_location = to_loc.text().strip() if a.kind == "MOVIMENTACAO" else ""

        if a.kind == "MOVIMENTACAO" and a.to_location:
            p = self.session.get(Printer, self.current_id)
            if p:
                p.local_atual = a.to_location
                p.updated_at = datetime.utcnow()
                self.session.add(p)

        try:
            self.session.add(a)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erro", f"Falha ao editar atividade:\n{e}")
            return

        self.refresh_table()
        self.update_counter()
        self.load_history()
        QMessageBox.information(self, "OK", "Atividade atualizada!")

    def delete_selected_activity(self):
        act_id = self.get_selected_activity_id()
        if not act_id:
            QMessageBox.information(self, "Atenção", "Selecione uma atividade no histórico.")
            return

        confirm = QMessageBox.question(self, "Confirmar", "Tem certeza que quer excluir essa atividade?")
        if confirm != QMessageBox.Yes:
            return

        a = self.session.get(Activity, act_id)
        if not a:
            QMessageBox.warning(self, "Atenção", "Atividade não encontrada.")
            return

        try:
            self.session.delete(a)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erro", f"Falha ao excluir atividade:\n{e}")
            return

        self.update_counter()
        self.load_history()
        QMessageBox.information(self, "OK", "Atividade excluída!")


    # ---------------- Export CSV ----------------
    def export_history_csv(self):
        if not self.current_id:
            QMessageBox.information(self, "Atenção", "Selecione uma impressora primeiro.")
            return

        p = self.session.get(Printer, self.current_id)
        if not p:
            QMessageBox.warning(self, "Atenção", "Impressora não encontrada.")
            return

        default_name = f"historico_{(p.patrimonio or 'sem_tag')}.csv".replace(" ", "_")
        path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", default_name, "CSV (*.csv)")
        if not path:
            return

        acts = (
            self.session.query(Activity)
            .filter(Activity.printer_id == self.current_id)
            .order_by(Activity.event_at.asc())
            .all()
        )

        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Patrimônio", "Modelo", "Serial", "Data/Hora", "Tipo", "Descrição", "Peças", "De", "Para"])
            for a in acts:
                w.writerow(
                    [
                        p.patrimonio,
                        p.modelo,
                        p.serial,
                        a.event_at.strftime("%d/%m/%Y %H:%M"),
                        "Manutenção" if a.kind == "MANUTENCAO" else "Movimentação",
                        a.notes or "",
                        a.parts_used or "",
                        a.from_location or "",
                        a.to_location or "",
                    ]
                )

        QMessageBox.information(self, "OK", f"CSV salvo em:\n{path}")


    # --------------- Logo no TOPO --------------

    def draw_header(self, canvas, doc):
        canvas.saveState()

        largura, altura = A4
        
        logo_path = resource_path("2.PNG") 
    
        if os.path.exists(logo_path):
        # A4[1] é o topo da folha (~29.7cm). 
        # Vamos colocar a logo a 2cm do topo (A4[1] - 2.5cm)
            canvas.drawImage(logo_path, 1.5*cm, A4[1]-2.5*cm, width=2.5*cm, preserveAspectRatio=True)

        largura_logo = 4 * cm
        altura_logo = 2 * cm

        canvas.drawImage(
            logo_path,
            doc.leftMargin,
            altura - 2.5 * cm,
            width=largura_logo,
            height=altura_logo,
            preserveAspectRatio=True,
            mask='auto'
        )

        canvas.restoreState()

    # ---------------- Export PDF ----------------
    def export_pdf(self):
        if not self.current_id:
            QMessageBox.information(self, "Atenção", "Selecione uma impressora primeiro.")
            return

        p = self.session.get(Printer, self.current_id)
        if not p:
            QMessageBox.warning(self, "Atenção", "Impressora não encontrada.")
            return

        # Pergunta o nome do técnico
        tecnico, ok = QInputDialog.getText(self, "Técnico responsável", "Nome do técnico responsável")
        if not ok: 
            return

        default_name = f"relatorio_{(p.patrimonio or 'sem_tag')}.pdf".replace(" ", "_")
        path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", default_name, "PDF (*.pdf)")
        if not path:
            return

        # Busca atividades e contagem de manutenção
        acts = (
            self.session.query(Activity)
            .filter(Activity.printer_id == self.current_id)
            .order_by(Activity.event_at.desc()) # Ordenado por data mais recente primeiro
            .all()
        )

        maint_count = (
            self.session.query(Activity)
            .filter(Activity.printer_id == self.current_id, Activity.kind == "MANUTENCAO")
            .count()
        )

        styles = getSampleStyleSheet()
        
        # Cores Personalizadas
        cor_primaria = colors.HexColor("#1A3C6C") # Azul Marinho Corporativo
        cor_fundo_zebra = colors.HexColor("#F8F9FA") # Cinza quase branco

        doc = SimpleDocTemplate(
            path, 
            pagesize=A4, 
            leftMargin=28, 
            rightMargin=28, 
            topMargin=28, 
            bottomMargin=45 # Aumentado para o rodapé novo
        )

        elems = []

        # ESPAÇAMENTO PARA A LOGO (Para não colar no título)
        elems.append(Spacer(1, 40)) 

        # TÍTULO ESTILIZADO
        style_title = styles["Title"]
        style_title.textColor = cor_primaria
        style_title.fontSize = 18
        elems.append(Paragraph(f"Relatório de Impressora - Patrimônio: {p.patrimonio}", style_title))
        elems.append(Spacer(1, 20))

        # TABELA DE DETALHES (Header do Relatório)
        header_data = [
            ["Patrimônio", p.patrimonio or "-"],
            ["Modelo", p.modelo or "-"],
            ["Serial", p.serial or "-"],
            ["Status", p.status or "-"],
            ["Peças Faltantes", p.pecas_faltantes or "-"],
            ["Local atual", p.local_atual or "-"],
            ["Contador de Manutenções", str(maint_count)],
            ["Última Revisão", p.ultima_revisao_data.strftime("%d/%m/%Y") if p.ultima_revisao_data else "-"],
            ["Técnico Revisor", p.tecnico_revisao or "-"]
        ]

        t_header = Table(header_data, colWidths=[140, 380])
        t_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), cor_fundo_zebra),
            ('TEXTCOLOR', (0, 0), (0, -1), cor_primaria),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elems.append(t_header)
        elems.append(Spacer(1, 20))

        # OBSERVAÇÃO GERAL
        if (p.observacao or "").strip():
            elems.append(Paragraph("<b>Observação geral:</b>", styles["Normal"]))
            elems.append(Paragraph((p.observacao or "").replace("\n", "<br/>"), styles["BodyText"]))
            elems.append(Spacer(1, 15))

        # TABELA DE HISTÓRICO 
        elems.append(Paragraph("<b>Histórico de atividades:</b>", styles["Normal"]))
        elems.append(Spacer(1, 8))

        data_hist = [["Data/Hora", "Tipo", "Descrição", "Peças", "De", "Para"]]

        for a in acts:
            # descrição para não quebrar a tabela 
            desc = Paragraph((a.notes or "")[:1200], styles["BodyText"])
            pecas = Paragraph((a.parts_used or "")[:400], styles["BodyText"])
            
            data_hist.append([
                a.event_at.strftime("%d/%m/%Y %H:%M"),
                "Manutenção" if a.kind == "MANUTENCAO" else "Movimentação",
                desc,
                pecas,
                a.from_location or "",
                a.to_location or "",
            ])

        # Larguras ajustadas para as colunas
        t_hist = Table(data_hist, colWidths=[75, 75, 175, 90, 52, 52], repeatRows=1)

        t_hist.setStyle(TableStyle([
            # Cabeçalho da tabela
            ('BACKGROUND', (0, 0), (-1, 0), cor_primaria),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            
            # Corpo da tabela (Efeito Zebra)
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, cor_fundo_zebra]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))

        elems.append(t_hist)

        # CONSTRUÇÃO DO PDF
        doc.build(
            elems,
            onFirstPage=lambda canvas, doc: (
                self.draw_header(canvas, doc),
                self.draw_footer(canvas, doc, tecnico)
            ),
            onLaterPages=lambda canvas, doc: (
                self.draw_header(canvas, doc),
                self.draw_footer(canvas, doc, tecnico)
            ),
        )
        QMessageBox.information(self, "Sucesso", f"Relatório PDF gerado com sucesso!")
        

    # ---------------- Rodapé Ass Tecnico -------------
    def draw_footer(self, canvas, doc, tecnico):
        canvas.saveState()
        largura, altura = A4
        y_assinatura = 2.5 * cm  # Sobe um pouco a assinatura para dar espaço

        # --- AREA DE ASSINATURA  ---
        centro = largura / 2
        linha_largura = 9 * cm
        x1 = centro - linha_largura / 2
        x2 = centro + linha_largura / 2

        canvas.setFont("Helvetica", 10)
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(1)
        
        # Linha de assinatura
        canvas.line(x1, y_assinatura + 18, x2, y_assinatura + 18)

        # Nome do técnico centralizado
        canvas.drawCentredString(centro, y_assinatura + 4, f"Técnico Responsável: {tecnico}")

        # Data abaixo do técnico
        canvas.setFont("Helvetica", 8)
        data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
        canvas.drawCentredString(centro, y_assinatura - 10, f"Data: {data_atual}")

        # --- DIVISORIA ABAIXO DA ASSINATURA ---
        y_divisoria = 1.2 * cm
        canvas.setStrokeColor(colors.lightgrey)
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, y_divisoria, largura - doc.rightMargin, y_divisoria)

        # --- INFORMACOES FINAIS  ---
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.gray)

        # Brasil Toner a esquerda
        canvas.drawString(doc.leftMargin, y_divisoria - 12, "Brasil Toner - Recife PE")

        # Contador de páginas a direita
        num_pagina = canvas.getPageNumber()
        canvas.drawRightString(largura - doc.rightMargin, y_divisoria - 12, f"Página {num_pagina}")

        canvas.restoreState()

        # ---------------- Export ALL CSV ----------------
    def export_all_csv(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar planilha completa",
            "impressoras_completo.csv",
            "CSV Files (*.csv)"
    )

        if not path:
            return

        printers = self.session.query(Printer).all()

        with open(path, "w", newline="", encoding="utf-8") as f:

            writer = csv.writer(f)

            writer.writerow([
                "Patrimonio",
                "Modelo",
                "Serial",
                "Status",
                "Local",
                "Observacao"
            ])

            for p in printers:

                writer.writerow([
                    p.patrimonio,
                    p.modelo,
                    p.serial,
                    p.status,
                    p.local_atual,
                    p.observacao
                ])

        QMessageBox.information(self, "OK", "Planilha completa exportada!")

    # ---------------- Export ALL CSV ----------------
    def export_all_pdf(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar relatório completo",
            "relatorio_completo_impressoras.pdf",
            "PDF Files (*.pdf)"
        )

        if not path:
            return

        printers = self.session.query(Printer).all()

        styles = getSampleStyleSheet()

        elements = []

        elements.append(Paragraph("Relatório Completo de Impressoras", styles["Title"]))
        elements.append(Spacer(1, 20))

        data = [
            ["Patrimônio", "Modelo", "Serial", "Status", "Local"]
        ]

        for p in printers:

            data.append([
                p.patrimonio or "",
                p.modelo or "",
                p.serial or "",
                p.status or "",
                p.local_atual or ""
            ])

        table = Table(data)

        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("GRID", (0,0), (-1,-1), 1, colors.black),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ]))

        elements.append(table)

        doc = SimpleDocTemplate(path, pagesize=A4)
        doc.build(elements)

        QMessageBox.information(self, "OK", "PDF completo exportado!")

        self.showMaximized()
