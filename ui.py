from __future__ import annotations

import csv
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path


from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QMessageBox,
    QComboBox, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QDialog, QDialogButtonBox,
    QFileDialog, QTabWidget, QAbstractItemView, QGroupBox
)

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from models import Printer, Activity, simple_uuid

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors



STATUSES = ["Operacional", "Em manutenção", "Parada", "Aguardando peça", "Em uso", "Sucata"]


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
        self.obs = QTextEdit()
        self.obs.setPlaceholderText("Observações gerais da máquina…")

        form.addRow("Patrimônio/Tag", self.patrimonio)
        form.addRow("Modelo", self.modelo)
        form.addRow("Serial", self.serial)
        form.addRow("Status", self.status)
        form.addRow("Local atual", self.local)
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

        # HISTÓRICO
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

        # RELATÓRIOS
        reports = QVBoxLayout(self.tab_reports)
        reports.setContentsMargins(20, 20, 20, 20)
        reports.setSpacing(20)

        reports.addWidget(self._section_title("Exportação de Relatórios"))

        desc = QLabel(
            "Exporte relatórios da impressora selecionada ou gere relatórios completos do sistema."
        )
        desc.setWordWrap(True)
        reports.addWidget(desc)

        # ---------- RELATÓRIO DA IMPRESSORA ----------
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

        # ---------- RELATÓRIOS COMPLETOS ----------
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

        if self.current_id:
            p = self.session.get(Printer, self.current_id)
            if not p:
                QMessageBox.warning(self, "Atenção", "Registro não encontrado.")
                return
        else:
            p = Printer(id=simple_uuid(), created_at=now)
            self.session.add(p)

        p.patrimonio = pat
        p.modelo = mod
        p.serial = ser
        p.status = self.status.currentText()
        p.local_atual = self.local.text().strip()
        p.observacao = self.obs.toPlainText().strip()
        p.updated_at = now

        self.session.commit()

        self.current_id = p.id

        self.refresh_table()
        self.update_counter()
        self.load_history()

        QMessageBox.information(self, "OK", "Salvo!")

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

    # ---------------- Export PDF ----------------
    def export_pdf(self):
        if not self.current_id:
            QMessageBox.information(self, "Atenção", "Selecione uma impressora primeiro.")
            return

        p = self.session.get(Printer, self.current_id)
        if not p:
            QMessageBox.warning(self, "Atenção", "Impressora não encontrada.")
            return

        default_name = f"relatorio_{(p.patrimonio or 'sem_tag')}.pdf".replace(" ", "_")
        path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", default_name, "PDF (*.pdf)")
        if not path:
            return

        acts = (
            self.session.query(Activity)
            .filter(Activity.printer_id == self.current_id)
            .order_by(Activity.event_at.asc())
            .all()
        )

        maint_count = (
            self.session.query(Activity)
            .filter(Activity.printer_id == self.current_id, Activity.kind == "MANUTENCAO")
            .count()
        )

        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=28, rightMargin=28, topMargin=28, bottomMargin=28)

        elems = []
        elems.append(Paragraph(f"Relatório de Impressora - Patrimônio: {p.patrimonio}", styles["Title"]))
        elems.append(Spacer(1, 12))

        header = [
            ["Patrimônio", p.patrimonio or "-"],
            ["Modelo", p.modelo or "-"],
            ["Serial", p.serial or "-"],
            ["Status", p.status or "-"],
            ["Local atual", p.local_atual or "-"],
            ["Manutenções (contador)", str(maint_count)],
        ]

        t_header = Table(header, colWidths=[130, 360])
        t_header.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.grey),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elems.append(t_header)
        elems.append(Spacer(1, 14))

        if (p.observacao or "").strip():
            elems.append(Paragraph("Observação geral:", styles["Heading3"]))
            elems.append(Paragraph((p.observacao or "").replace("\n", "<br/>"), styles["BodyText"]))
            elems.append(Spacer(1, 10))

        elems.append(Paragraph("Histórico de atividades:", styles["Heading3"]))
        elems.append(Spacer(1, 6))

        data = [["Data/Hora", "Tipo", "Descrição", "Peças", "De", "Para"]]
        for a in acts:
            data.append(
                [
                    a.event_at.strftime("%d/%m/%Y %H:%M"),
                    "Manutenção" if a.kind == "MANUTENCAO" else "Movimentação",
                    (a.notes or "")[:1200],
                    (a.parts_used or "")[:400],
                    a.from_location or "",
                    a.to_location or "",
                ]
            )

        t = Table(data, colWidths=[75, 70, 170, 90, 55, 55])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.grey),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        elems.append(t)
        elems.append(Spacer(1, 10))
        elems.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))

        doc.build(elems)
        QMessageBox.information(self, "OK", f"PDF salvo em:\n{path}")

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
