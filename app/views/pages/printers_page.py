from __future__ import annotations

import os
import shutil
from datetime import datetime as dt
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.utils.helpers import formatar_data, formatar_data_hora, limpar_local, parse_data
from app.utils.ui_helpers import tratar_erro
from app.utils.validacao import ValidadorCampo, obrigatorio, minimo, alfanumerico
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
)
from app.views.widgets import ToastManager
from app.views.widgets.confirm_dialog import ConfirmacaoDigitarDialog
from app.views.widgets.import_dialog import ImportDialog
from app.views.widgets.pagination import PaginacaoWidget
from app.views.widgets.search_bar import SearchBar
from app.views.widgets.table_widget import TabelaPadrao


PHOTO_DIR = Path("uploads/printer_photos")


class PrintersPage(QWidget):
    session: Any
    printer_service: Any
    company_service: Any
    technician_service: Any
    activity_service: Any
    part_service: Any
    printer_location_service: Any
    _filtro_atual: str | None
    search: SearchBar
    tabela: TabelaPadrao
    _paginacao: PaginacaoWidget

    def __init__(self, session: Any, printer_service: Any, company_service: Any, technician_service: Any, activity_service: Any, part_service: Any, printer_location_service: Any = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        self.printer_service = printer_service
        self.company_service = company_service
        self.technician_service = technician_service
        self.activity_service = activity_service
        self.part_service = part_service
        self.printer_location_service = printer_location_service

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

        btn_importar = QPushButton("  Importar")
        btn_importar.setCursor(Qt.PointingHandCursor)
        btn_importar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_importar.clicked.connect(lambda: self._importar())
        header.addWidget(btn_importar)

        btn_atualizar = QPushButton("  Atualizar")
        btn_atualizar.setCursor(Qt.PointingHandCursor)
        btn_atualizar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_atualizar.clicked.connect(self.recarregar)
        header.addWidget(btn_atualizar)

        layout.addLayout(header)

        colunas = ["Patrimônio", "Serial", "Modelo", "Marca", "Status", "Local Atual", "Atividades"]
        self.tabela = TabelaPadrao(colunas)
        self.tabela.cellDoubleClicked.connect(self._detalhes)
        layout.addWidget(self.tabela)

        self._paginacao = PaginacaoWidget()
        self._paginacao.pagina_alterada.connect(lambda p: self._carregar())
        layout.addWidget(self._paginacao)

        self._filtro_atual = None
        self._carregar()

    def recarregar(self) -> None:
        self._filtro_atual = None
        self._paginacao.configurar(self.printer_service.contar_todos(), pagina_atual=1)
        self._carregar()

    def _carregar(self) -> None:
        impressoras = self.printer_service.listar_todos(
            filtro=self._filtro_atual, limite=self._paginacao.limit, offset=self._paginacao.offset
        )
        self._impressoras_visiveis = impressoras
        total = self.printer_service.contar_todos(filtro=self._filtro_atual)
        self._paginacao.configurar(total, pagina_atual=self._paginacao.pagina,
                                   itens_por_pagina=self._paginacao.limit)

        ids = [p.id for p in impressoras]
        counts = self.printer_service.contar_atividades(ids) if ids else {}

        self.tabela.setRowCount(len(impressoras))

        for i, p in enumerate(impressoras):
            pat_item = QTableWidgetItem(p.patrimonio)
            pat_item.setForeground(QColor(COR["texto"]))
            self.tabela.setItem(i, 0, pat_item)

            self.tabela.setItem(i, 1, QTableWidgetItem(p.serial or "-"))
            self.tabela.setItem(i, 2, QTableWidgetItem(p.modelo))
            self.tabela.setItem(i, 3, QTableWidgetItem(p.marca or "-"))

            cor = STATUS_CORES.get(p.status, "#94949f")
            self.tabela.definir_badge(i, 4, p.status, cor)

            self.tabela.setItem(i, 5, QTableWidgetItem(p.local_atual or "-"))

            cnt_item = QTableWidgetItem(str(counts.get(p.id, 0)))
            cnt_item.setTextAlignment(Qt.AlignCenter)
            cnt_item.setForeground(QColor(COR["texto_sec"]))
            self.tabela.setItem(i, 6, cnt_item)

        self.tabela.redimensionar()

    def filtrar(self, texto: str) -> None:
        self._filtro_atual = texto if texto else None
        self._carregar()

    def _detalhes(self, row: int) -> None:
        if row < 0 or row >= len(self._impressoras_visiveis):
            return
        printer = self._impressoras_visiveis[row]

        self._detalhes_dialog = QDialog(self)
        dialog = self._detalhes_dialog
        dialog.setWindowTitle(f"Impressora - {printer.patrimonio}")
        dialog.setMinimumSize(750, 550)
        dialog.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #2a2a3e; background: transparent; border-radius: 6px; }
            QTabBar::tab { color: #94949f; font-weight: 600; padding: 8px 16px; }
            QTabBar::tab:selected { color: #a78bfa; border-bottom-color: #a78bfa; }
            QTabBar::tab:hover { color: #e8e8f0; }
        """)
        layout.addWidget(tabs)

        # ── Tab Dados Gerais ──────────────────────────────────────
        tab_geral = QWidget()
        tabs.addTab(tab_geral, "  Dados Gerais")
        geral_layout = QVBoxLayout(tab_geral)
        geral_layout.setContentsMargins(16, 16, 16, 16)

        hbody = QWidget()
        hbox = QHBoxLayout(hbody)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(16)
        geral_layout.addWidget(hbody)

        grid_w = QWidget()
        grid = QGridLayout(grid_w)
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setColumnStretch(1, 1)
        hbox.addWidget(grid_w, stretch=1)

        for i, (label, valor) in enumerate([
            ("Patrimônio:", printer.patrimonio or "-"),
            ("Serial:", printer.serial or "-"),
            ("Modelo:", printer.modelo or "-"),
            ("Marca:", printer.marca or "-"),
            ("Status:", printer.status or "-"),
            ("Tipo:", printer.tipo or "-"),
            ("Local Atual:", printer.local_atual or "-"),
            ("IP Rede:", printer.ip_rede or "-"),
            ("Técnico:", printer.tecnico or "-"),
            ("Última Revisão:", formatar_data(printer.proxima_revisao) if printer.proxima_revisao else "-"),
            ("Observação:", printer.observacao or "-"),
            ("Peças Faltantes:", printer.pecas_faltantes or "-"),
        ]):
            lbl = QLabel(label)
            lbl.setStyleSheet(ESTILO_LABEL_CAMPO)
            val = QLabel(valor)
            val.setWordWrap(True)
            val.setStyleSheet("color: #e2e8f0; font-size: 13px;")
            grid.addWidget(lbl, i, 0, Qt.AlignTop)
            grid.addWidget(val, i, 1)

        # ── Foto ──────────────────────────────────────────────────
        foto_w = QWidget()
        foto_w.setFixedWidth(220)
        foto_col = QVBoxLayout(foto_w)
        foto_col.setContentsMargins(0, 0, 0, 0)
        foto_col.setSpacing(8)
        hbox.addWidget(foto_w)

        foto_label = QLabel()
        foto_label.setFixedSize(200, 200)
        foto_label.setAlignment(Qt.AlignCenter)
        foto_label.setStyleSheet(
            "background-color: #1e1e32; border: 1px solid #2a2a3e; border-radius: 8px;"
            " font-size: 12px; color: #6b7280;"
        )
        foto_col.addWidget(foto_label, alignment=Qt.AlignCenter)

        if printer.foto_path and Path(printer.foto_path).exists():
            pixmap = QPixmap(printer.foto_path)
            if not pixmap.isNull():
                foto_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                foto_label.setStyleSheet("border-radius: 8px; background: transparent;")
        else:
            foto_label.setText("Sem foto")

        geral_layout.addStretch()

        # ── Tab Atividades ────────────────────────────────────────
        tab_atv = QWidget()
        tabs.addTab(tab_atv, "  Atividades")
        atv_l = QVBoxLayout(tab_atv)
        atv_l.setContentsMargins(16, 16, 16, 16)
        atv_l.setSpacing(8)

        t_atv = TabelaPadrao(["Data", "Tipo", "Descrição", "Status", "Técnico"])
        atv_l.addWidget(t_atv)
        atividades = self.activity_service.listar_por_impressora(printer.id)
        t_atv.setRowCount(len(atividades))
        for i, a in enumerate(atividades):
            t_atv.setItem(i, 0, QTableWidgetItem(formatar_data_hora(a.event_at) if a.event_at else "-"))
            t_atv.setItem(i, 1, QTableWidgetItem(a.kind or "-"))
            t_atv.setItem(i, 2, QTableWidgetItem(a.notes or "-"))
            t_atv.setItem(i, 3, QTableWidgetItem(a.status_atividade or "-"))
            t_atv.setItem(i, 4, QTableWidgetItem(str(a.tecnico) if hasattr(a, "tecnico") and a.tecnico else "-"))
        t_atv.redimensionar()
        t_atv.cellDoubleClicked.connect(lambda r: self._editar_atividade(r, atividades, printer, dialog))

        # ── Tab Histórico de Locais ──────────────────────────────
        tab_loc = QWidget()
        tabs.addTab(tab_loc, "  Histórico de Locais")
        loc_l = QVBoxLayout(tab_loc)
        loc_l.setContentsMargins(16, 16, 16, 16)
        loc_l.setSpacing(8)

        registros = self.printer_location_service.listar_por_impressora(printer.id) if self.printer_location_service else []
        t_loc = TabelaPadrao(["Data", "Local", "Observação", "Registrado em"])
        loc_l.addWidget(t_loc)
        t_loc.setRowCount(len(registros))
        for i, r in enumerate(registros):
            t_loc.setItem(i, 0, QTableWidgetItem(formatar_data(r.data) if r.data else "-"))
            t_loc.setItem(i, 1, QTableWidgetItem(r.local or "-"))
            t_loc.setItem(i, 2, QTableWidgetItem(r.observacao or "-"))
            t_loc.setItem(i, 3, QTableWidgetItem(formatar_data_hora(r.created_at) if r.created_at else "-"))
        t_loc.redimensionar()

        btn_imp = QPushButton("  Importar CSV/XLSX")
        btn_imp.setCursor(Qt.PointingHandCursor)
        btn_imp.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_imp.clicked.connect(lambda: self._importar_locais(dialog, printer))
        loc_l.addWidget(btn_imp)

        # ── Botões ────────────────────────────────────────────────
        botoes = QHBoxLayout()
        botoes.setSpacing(10)

        btn_edit = QPushButton("\u270f Editar")
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setStyleSheet(ESTILO_BOTAO_AVISO)
        btn_edit.clicked.connect(lambda: self._editar_impressora(printer, row))
        botoes.addWidget(btn_edit)

        btn_del = QPushButton("\U0001f5d1 Excluir")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_del.clicked.connect(lambda: self._excluir_impressora(dialog, printer, row))
        botoes.addWidget(btn_del)

        botoes.addStretch()

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setCursor(Qt.PointingHandCursor)
        btn_fechar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_fechar.clicked.connect(dialog.accept)
        botoes.addWidget(btn_fechar)

        layout.addLayout(botoes)
        dialog.exec()

    def _editar_impressora(self, printer: Any, row: int) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Editar Impressora - {printer.patrimonio}")
        dialog.setMinimumSize(920, 560)
        dialog.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        hbody = QWidget()
        hbox = QHBoxLayout(hbody)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(16)
        layout.addWidget(hbody, stretch=1)

        # ── Grade 2 colunas ───────────────────────────────────────
        grid_w = QWidget()
        grid = QGridLayout(grid_w)
        grid.setSpacing(2)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(3, 3)
        hbox.addWidget(grid_w, stretch=1)

        def _erro_label() -> QLabel:
            lbl = QLabel()
            lbl.setStyleSheet("color: #ef4444; font-size: 9px; background: transparent; padding: 0; margin: 0;")
            lbl.hide()
            return lbl

        def _par(r: int, text_a: str, w_a, err_a: QLabel, text_b: str, w_b, err_b: QLabel) -> None:
            la = QLabel(text_a); la.setStyleSheet(ESTILO_LABEL_CAMPO)
            lb = QLabel(text_b); lb.setStyleSheet(ESTILO_LABEL_CAMPO)
            grid.addWidget(la, r, 0); grid.addWidget(w_a, r, 1)
            grid.addWidget(lb, r, 2); grid.addWidget(w_b, r, 3)
            grid.addWidget(err_a, r + 1, 1)
            grid.addWidget(err_b, r + 1, 3)

        pat = QLineEdit(); pat.setText(printer.patrimonio); pat.setMaxLength(80); pat.setStyleSheet(ESTILO_INPUT)
        err_pat = _erro_label()
        ValidadorCampo(pat, obrigatorio, err_pat)
        serial = QLineEdit(); serial.setText(printer.serial or ""); serial.setMaxLength(80); serial.setStyleSheet(ESTILO_INPUT)
        err_serial = _erro_label()
        ValidadorCampo(serial, minimo(3), err_serial)
        _par(0, "Patrimônio *:", pat, err_pat, "Serial:", serial, err_serial)

        mod = QLineEdit(); mod.setText(printer.modelo or ""); mod.setMaxLength(80); mod.setStyleSheet(ESTILO_INPUT)
        err_mod = _erro_label()
        ValidadorCampo(mod, minimo(2), err_mod)
        marca = QLineEdit(); marca.setText(printer.marca or ""); marca.setMaxLength(80); marca.setStyleSheet(ESTILO_INPUT)
        err_marca = _erro_label()
        ValidadorCampo(marca, minimo(2), err_marca)
        _par(2, "Modelo:", mod, err_mod, "Marca:", marca, err_marca)

        status = QComboBox(); configurar_combo(status)
        status.addItems(["Operacional", "Em uso", "Em manutenção", "Parada", "Aguardando peça", "Sucata"])
        if printer.status: status.setCurrentText(printer.status)
        err_status = _erro_label()
        tipo = QComboBox(); configurar_combo(tipo)
        tipo.addItems(["", "Laser", "Jato de tinta", "Multifuncional"])
        if printer.tipo in ["Laser", "Jato de tinta", "Multifuncional"]: tipo.setCurrentText(printer.tipo)
        err_tipo = _erro_label()
        _par(4, "Status:", status, err_status, "Tipo:", tipo, err_tipo)

        local = QComboBox(); local.setEditable(True); configurar_combo(local)
        local.addItem("")
        for emp in self.company_service.listar_todas(): local.addItem(f"\U0001f3e2 {emp.nome}")
        for nome in self.printer_service.locais_distintos():
            if nome and nome not in {e.nome for e in self.company_service.listar_todas()}:
                local.addItem(f"\U0001f4cd {nome}")
        if printer.local_atual:
            idx = local.findText(printer.local_atual)
            if idx >= 0: local.setCurrentIndex(idx)
            else: local.setCurrentText(printer.local_atual)
        err_local = _erro_label()
        ip = QLineEdit(); ip.setText(printer.ip_rede or ""); ip.setMaxLength(45); ip.setStyleSheet(ESTILO_INPUT)
        err_ip = _erro_label()
        _par(6, "Local Atual:", local, err_local, "IP Rede:", ip, err_ip)

        tec = QComboBox(); tec.setEditable(True); configurar_combo(tec)
        tec.addItem("")
        for t in self.technician_service.listar_ativos(): tec.addItem(t.nome_exibicao)
        if printer.tecnico: tec.setCurrentText(printer.tecnico)
        err_tec = _erro_label()
        rev = QLineEdit()
        rev.setText(formatar_data(printer.proxima_revisao) if printer.proxima_revisao else "")
        rev.setPlaceholderText("dd/mm/aaaa"); rev.setStyleSheet(ESTILO_INPUT)
        err_rev = _erro_label()
        _par(8, "Técnico:", tec, err_tec, "Última Revisão:", rev, err_rev)

        obs = QTextEdit(); obs.setPlaceholderText("Observações gerais...")
        obs.setPlainText(printer.observacao or ""); obs.setStyleSheet(ESTILO_INPUT)
        obs.setMaximumHeight(60)
        err_obs = _erro_label()
        grid.addWidget(QLabel("Observação:"), 10, 0, Qt.AlignTop); grid.addWidget(obs, 10, 1, 1, 3)
        grid.addWidget(err_obs, 11, 1, 1, 3)

        pecas = QTextEdit(); pecas.setPlaceholderText("Peças faltantes...")
        pecas.setPlainText(printer.pecas_faltantes or ""); pecas.setStyleSheet(ESTILO_INPUT)
        pecas.setMaximumHeight(60)
        err_pecas = _erro_label()
        grid.addWidget(QLabel("Peças Faltantes:"), 12, 0, Qt.AlignTop); grid.addWidget(pecas, 12, 1, 1, 3)
        grid.addWidget(err_pecas, 13, 1, 1, 3)

        # ── Foto ──────────────────────────────────────────────────
        foto_w = QWidget()
        foto_w.setFixedWidth(220)
        foto_col = QVBoxLayout(foto_w)
        foto_col.setContentsMargins(0, 0, 0, 0)
        foto_col.setSpacing(8)
        hbox.addWidget(foto_w)

        foto_label = QLabel()
        foto_label.setFixedSize(200, 200)
        foto_label.setAlignment(Qt.AlignCenter)
        foto_label.setStyleSheet(
            "background-color: #1e1e32; border: 1px solid #2a2a3e; border-radius: 8px;"
            " font-size: 12px; color: #6b7280;"
        )
        foto_col.addWidget(foto_label, alignment=Qt.AlignCenter)

        foto_ref: list[str | None] = [printer.foto_path]

        def _att_foto(path: str | None) -> None:
            if path and Path(path).exists():
                pm = QPixmap(path)
                if not pm.isNull():
                    foto_label.setPixmap(pm.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    foto_label.setStyleSheet("border-radius: 8px; background: transparent;")
                    return
            foto_label.setText("Sem foto")
            foto_label.setStyleSheet(
                "background-color: #1e1e32; border: 1px solid #2a2a3e; border-radius: 8px;"
                " font-size: 12px; color: #6b7280;"
            )

        _att_foto(printer.foto_path)

        def _trocar() -> None:
            p, _ = QFileDialog.getOpenFileName(dialog, "Selecionar Foto", "", "Imagens (*.png *.jpg *.jpeg *.bmp)")
            if p:
                ext = Path(p).suffix
                dest = PHOTO_DIR / f"{printer.id}{ext}"
                PHOTO_DIR.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, str(dest))
                foto_ref[0] = str(dest)
                _att_foto(str(dest))

        def _remover() -> None:
            foto_ref[0] = None
            _att_foto(None)

        btn_trocar = QPushButton("\U0001f4c1 Trocar Foto")
        btn_trocar.setCursor(Qt.PointingHandCursor)
        btn_trocar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_trocar.clicked.connect(_trocar)
        foto_col.addWidget(btn_trocar)

        btn_rem = QPushButton("\U0001f5d1 Remover Foto")
        btn_rem.setCursor(Qt.PointingHandCursor)
        btn_rem.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_rem.clicked.connect(_remover)
        foto_col.addWidget(btn_rem)

        # ── Botões ────────────────────────────────────────────────
        botoes = QHBoxLayout()
        botoes.setSpacing(10)

        def _salvar() -> None:
            novo_pat = pat.text().strip()
            if novo_pat and novo_pat != printer.patrimonio:
                existente = self.printer_service.verificar_patrimonio_existe(novo_pat)
                if existente:
                    QMessageBox.warning(dialog, "Patrimônio Duplicado",
                        f"Já existe uma impressora com o patrimônio '{novo_pat}'!")
                    return
            with tratar_erro("atualizar impressora"):
                self.printer_service.atualizar(
                    printer,
                    patrimonio=novo_pat,
                    status=status.currentText(),
                    modelo=mod.text().strip(),
                    marca=marca.text().strip(),
                    serial=serial.text().strip(),
                    tipo=tipo.currentText(),
                    local_atual=limpar_local(local.currentText()),
                    ip_rede=ip.text().strip(),
                    tecnico=tec.currentText().strip(),
                    proxima_revisao=parse_data(rev.text()) or printer.proxima_revisao or dt.now(),
                    observacao=obs.toPlainText().strip(),
                    pecas_faltantes=pecas.toPlainText().strip(),
                    foto_path=foto_ref[0] if foto_ref else printer.foto_path
                )
                dialog.accept()
                self.recarregar()
                d = getattr(self, '_detalhes_dialog', None)
                if d is not None:
                    d.close()
                self._detalhes(row)

        btn_salvar = QPushButton("\U0001f4be Salvar")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_salvar.clicked.connect(_salvar)
        botoes.addWidget(btn_salvar)

        botoes.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_cancelar.clicked.connect(dialog.reject)
        botoes.addWidget(btn_cancelar)

        layout.addLayout(botoes)
        dialog.exec()

    def _excluir_impressora(self, parent_dialog: QDialog, printer: Any, row: int) -> None:
        if ConfirmacaoDigitarDialog.confirmar(
            "Excluir Impressora",
            f"Tem certeza que deseja excluir a impressora {printer.patrimonio}?",
            parent_dialog,
        ):
            with tratar_erro("excluir impressora"):
                self.printer_service.excluir(printer)
                ToastManager.mostrar("Impressora excluída.", "sucesso", duracao=5000)
                parent_dialog.accept()
                self.recarregar()

    def _nova(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Nova Impressora")
        dialog.setMinimumSize(920, 560)
        dialog.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        hbody = QWidget()
        hbox = QHBoxLayout(hbody)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(16)
        layout.addWidget(hbody, stretch=1)

        grid_w = QWidget()
        grid = QGridLayout(grid_w)
        grid.setSpacing(2)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(3, 3)
        hbox.addWidget(grid_w, stretch=1)

        def _erro_label() -> QLabel:
            lbl = QLabel()
            lbl.setStyleSheet("color: #ef4444; font-size: 9px; background: transparent; padding: 0; margin: 0;")
            lbl.hide()
            return lbl

        def _par(r: int, text_a: str, w_a, err_a: QLabel, text_b: str, w_b, err_b: QLabel) -> None:
            la = QLabel(text_a); la.setStyleSheet(ESTILO_LABEL_CAMPO)
            lb = QLabel(text_b); lb.setStyleSheet(ESTILO_LABEL_CAMPO)
            grid.addWidget(la, r, 0); grid.addWidget(w_a, r, 1)
            grid.addWidget(lb, r, 2); grid.addWidget(w_b, r, 3)
            grid.addWidget(err_a, r + 1, 1)
            grid.addWidget(err_b, r + 1, 3)

        pat = QLineEdit(); pat.setPlaceholderText("Número do patrimônio"); pat.setMaxLength(80); pat.setStyleSheet(ESTILO_INPUT)
        err_pat = _erro_label()
        ValidadorCampo(pat, obrigatorio, err_pat)
        serial = QLineEdit(); serial.setPlaceholderText("Número de série"); serial.setMaxLength(80); serial.setStyleSheet(ESTILO_INPUT)
        err_serial = _erro_label()
        ValidadorCampo(serial, minimo(3), err_serial)
        _par(0, "Patrimônio *:", pat, err_pat, "Serial:", serial, err_serial)

        mod = QLineEdit(); mod.setPlaceholderText("Modelo da impressora"); mod.setMaxLength(80); mod.setStyleSheet(ESTILO_INPUT)
        err_mod = _erro_label()
        ValidadorCampo(mod, minimo(2), err_mod)
        marca = QLineEdit(); marca.setPlaceholderText("Marca (HP, Brother, etc)"); marca.setMaxLength(80); marca.setStyleSheet(ESTILO_INPUT)
        err_marca = _erro_label()
        ValidadorCampo(marca, minimo(2), err_marca)
        _par(2, "Modelo:", mod, err_mod, "Marca:", marca, err_marca)

        status = QComboBox(); configurar_combo(status)
        status.addItems(["Operacional", "Em uso", "Em manutenção", "Parada", "Aguardando peça", "Sucata"])
        err_status = _erro_label()
        tipo = QComboBox(); configurar_combo(tipo)
        tipo.addItems(["", "Laser", "Jato de tinta", "Multifuncional"])
        err_tipo = _erro_label()
        _par(4, "Status:", status, err_status, "Tipo:", tipo, err_tipo)

        local = QComboBox(); local.setEditable(True); configurar_combo(local)
        local.addItem("")
        for emp in self.company_service.listar_todas(): local.addItem(f"\U0001f3e2 {emp.nome}")
        for nome in self.printer_service.locais_distintos():
            if nome and nome not in {e.nome for e in self.company_service.listar_todas()}:
                local.addItem(f"\U0001f4cd {nome}")
        err_local = _erro_label()
        ip = QLineEdit(); ip.setPlaceholderText("192.168.0.100"); ip.setMaxLength(45); ip.setStyleSheet(ESTILO_INPUT)
        err_ip = _erro_label()
        _par(6, "Local Atual:", local, err_local, "IP Rede:", ip, err_ip)

        tec = QComboBox(); tec.setEditable(True); configurar_combo(tec)
        tec.addItem("")
        for t in self.technician_service.listar_ativos(): tec.addItem(t.nome_exibicao)
        err_tec = _erro_label()
        rev = QLineEdit(); rev.setPlaceholderText("dd/mm/aaaa"); rev.setStyleSheet(ESTILO_INPUT)
        err_rev = _erro_label()
        _par(8, "Técnico:", tec, err_tec, "Última Revisão:", rev, err_rev)

        obs = QTextEdit(); obs.setPlaceholderText("Observações gerais..."); obs.setStyleSheet(ESTILO_INPUT)
        obs.setMaximumHeight(60)
        err_obs = _erro_label()
        grid.addWidget(QLabel("Observação:"), 10, 0, Qt.AlignTop); grid.addWidget(obs, 10, 1, 1, 3)
        grid.addWidget(err_obs, 11, 1, 1, 3)

        pecas = QTextEdit(); pecas.setPlaceholderText("Peças faltantes..."); pecas.setStyleSheet(ESTILO_INPUT)
        pecas.setMaximumHeight(60)
        err_pecas = _erro_label()
        grid.addWidget(QLabel("Peças Faltantes:"), 12, 0, Qt.AlignTop); grid.addWidget(pecas, 12, 1, 1, 3)
        grid.addWidget(err_pecas, 13, 1, 1, 3)

        # ── Foto ──────────────────────────────────────────────────
        foto_w = QWidget()
        foto_w.setFixedWidth(220)
        foto_col = QVBoxLayout(foto_w)
        foto_col.setContentsMargins(0, 0, 0, 0)
        foto_col.setSpacing(8)
        hbox.addWidget(foto_w)

        foto_label = QLabel("Sem foto")
        foto_label.setFixedSize(200, 200)
        foto_label.setAlignment(Qt.AlignCenter)
        foto_label.setStyleSheet(
            "background-color: #1e1e32; border: 1px solid #2a2a3e; border-radius: 8px;"
            " font-size: 12px; color: #6b7280;"
        )
        foto_col.addWidget(foto_label, alignment=Qt.AlignCenter)

        foto_ref: list[str | None] = [None]

        def _trocar() -> None:
            p, _ = QFileDialog.getOpenFileName(dialog, "Selecionar Foto", "", "Imagens (*.png *.jpg *.jpeg *.bmp)")
            if p:
                foto_ref[0] = p
                pm = QPixmap(p)
                if not pm.isNull():
                    foto_label.setPixmap(pm.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    foto_label.setStyleSheet("border-radius: 8px; background: transparent;")

        def _remover() -> None:
            foto_ref[0] = None
            foto_label.setText("Sem foto")
            foto_label.setStyleSheet(
                "background-color: #1e1e32; border: 1px solid #2a2a3e; border-radius: 8px;"
                " font-size: 12px; color: #6b7280;"
            )

        btn_trocar = QPushButton("\U0001f4c1 Trocar Foto")
        btn_trocar.setCursor(Qt.PointingHandCursor)
        btn_trocar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_trocar.clicked.connect(_trocar)
        foto_col.addWidget(btn_trocar)

        btn_rem = QPushButton("\U0001f5d1 Remover Foto")
        btn_rem.setCursor(Qt.PointingHandCursor)
        btn_rem.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_rem.clicked.connect(_remover)
        foto_col.addWidget(btn_rem)

        # ── Botões ────────────────────────────────────────────────
        botoes = QHBoxLayout()
        botoes.setSpacing(10)

        def _salvar() -> None:
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
            with tratar_erro("criar impressora"):
                foto_dest = None
                if foto_ref[0]:
                    ext = Path(foto_ref[0]).suffix
                    import uuid
                    temp_id = str(uuid.uuid4())
                    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
                    foto_dest = str(PHOTO_DIR / f"{temp_id}{ext}")
                    shutil.copy2(foto_ref[0], foto_dest)
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
                    observacao=obs.toPlainText().strip(),
                    pecas_faltantes=pecas.toPlainText().strip(),
                    foto_path=foto_dest
                )
                self.recarregar()
                dialog.accept()

        btn_salvar = QPushButton("\U0001f4be Salvar")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_salvar.clicked.connect(_salvar)
        botoes.addWidget(btn_salvar)

        botoes.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_cancelar.clicked.connect(dialog.reject)
        botoes.addWidget(btn_cancelar)

        layout.addLayout(botoes)
        dialog.exec()

    def _salvar_nova(self, dialog: QDialog, pat: QLineEdit, mod: QLineEdit, marca: QLineEdit, serial: QLineEdit, tipo: QComboBox, local: QComboBox, status: QComboBox, ip: QLineEdit, tec: QComboBox, obs: QTextEdit) -> None:
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

        with tratar_erro("criar impressora"):
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

    def _importar_locais(self, parent_dialog: QDialog, printer: Any) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            parent_dialog, "Importar Histórico de Locais", "",
            "CSV (*.csv);;XLSX (*.xlsx)"
        )
        if not path_str:
            return
        path = Path(path_str)
        registros: list[dict[str, Any]] = []
        if path.suffix.lower() == ".csv":
            import csv
            with open(str(path), encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    registros.append(row)
        elif path.suffix.lower() == ".xlsx":
            try:
                import openpyxl
                wb = openpyxl.load_workbook(str(path), read_only=True)
                ws = wb.active
                headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
                for row in ws.iter_rows(min_row=2, values_only=True):
                    registros.append(dict(zip(headers, [v or "" for v in row])))
            except Exception as e:
                QMessageBox.warning(parent_dialog, "Erro", f"Não foi possível ler o arquivo:\n{e}")
                return

        if not registros:
            QMessageBox.information(parent_dialog, "Importar", "Nenhum registro encontrado no arquivo.")
            return

        try:
            importados = self.printer_location_service.importar(printer.id, registros)
            QMessageBox.information(parent_dialog, "Importado",
                f"{importados} registro(s) de localização importado(s) com sucesso.")
            # refresh the tab
            parent_dialog.close()
            self._detalhes(self.tabela.currentRow() if self.tabela.currentRow() >= 0 else 0)
        except Exception as e:
            QMessageBox.warning(parent_dialog, "Erro", f"Erro ao importar:\n{e}")


    def _salvar_edicao(self, dialog: QDialog, printer: Any, pat_input: QLineEdit, status: QComboBox, modelo: QLineEdit, marca: QLineEdit, serial: QLineEdit, tipo: QComboBox, local: QComboBox, ip: QLineEdit, tecnico: QComboBox, revisao: QLineEdit, obs: QTextEdit, pecas: QTextEdit, callback: Any = None, foto_ref: list[Any | None] | None = None) -> None:
        novo_pat = pat_input.text().strip()
        if novo_pat and novo_pat != printer.patrimonio:
            existente = self.printer_service.verificar_patrimonio_existe(novo_pat)
            if existente:
                QMessageBox.warning(dialog, "Patrimônio Duplicado", f"Já existe uma impressora com o patrimônio '{novo_pat}'!")
                return

        with tratar_erro("atualizar impressora"):
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
                pecas_faltantes=pecas.toPlainText().strip(),
                foto_path=foto_ref[0] if foto_ref else printer.foto_path
            )
            self.recarregar()
            if callback:
                callback()

    def _editar_atividade(self, row: int, atividades: list[Any], printer: Any, parent_dialog: QDialog) -> None:
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

        def _preencher_pecas(idx: int) -> None:
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

        def _toggle_origem_destino(tipo: str) -> None:
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

    def _salvar_edicao_atividade(self, dialog: QDialog, atividade: Any, printer_combo: QComboBox, tipo: QComboBox, data: QLineEdit,
                                  desc: QTextEdit, pecas: QTextEdit, origem: QComboBox, destino: QComboBox, tecnico: QComboBox, status: QComboBox) -> None:
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

        with tratar_erro("atualizar atividade"):
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

    def _importar(self) -> None:
        dialog = ImportDialog(self, "printers", "Impressoras", self.printer_service, self.session)
        if dialog.exec() == ImportDialog.Accepted:
            self.recarregar()

    def _excluir_atividade(self, dialog: QDialog, atividade: Any) -> None:
        if ConfirmacaoDigitarDialog.confirmar(
            "Confirmar Exclusão",
            "Deseja realmente excluir esta atividade?",
            dialog,
        ):
            with tratar_erro("excluir atividade"):
                self.activity_service.excluir(atividade)
                ToastManager.mostrar(
                    "Atividade excluída.",
                    "aviso", duracao=8000,
                    acao=("Desfazer", lambda o=atividade, svc=self.activity_service, pag=self: (svc.restaurar(o), pag.recarregar())),
                )
                self.recarregar()
                dialog.accept()
