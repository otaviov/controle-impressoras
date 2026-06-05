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
    QCompleter,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.utils.helpers import formatar_data, formatar_data_hora, limpar_local, parse_data
from app.utils.ui_helpers import tratar_erro
from app.utils.validacao import ValidadorCampo, obrigatorio, minimo
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


# ── Helpers de UI ────────────────────────────────────────────────────────────

def _secao_label(texto: str) -> QLabel:
    """Cabeçalho de seção com linha separadora visual."""
    lbl = QLabel(texto.upper())
    lbl.setStyleSheet(
        "color: #6366f1; font-size: 9px; font-weight: 700;"
        " letter-spacing: 1.2px; background: transparent;"
    )
    return lbl


def _campo_readonly(valor: str) -> QLabel:
    """Label de valor para a tela de detalhes."""
    lbl = QLabel(valor or "—")
    lbl.setWordWrap(True)
    lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
    lbl.setStyleSheet(
        "color: #e2e8f0; font-size: 13px; background: transparent; padding: 0;"
    )
    return lbl


def _campo_rotulo(texto: str) -> QLabel:
    lbl = QLabel(texto)
    lbl.setStyleSheet(
        "color: #94949f; font-size: 11px; font-weight: 600;"
        " background: transparent; letter-spacing: 0.3px;"
    )
    return lbl


def _badge_status(status: str) -> QLabel:
    cor = STATUS_CORES.get(status, "#94949f")
    lbl = QLabel(f"● {status}")
    lbl.setStyleSheet(
        f"color: {cor}; font-size: 12px; font-weight: 600; background: transparent;"
    )
    return lbl


def _input_label(texto: str) -> QLabel:
    """Label para campos de formulário de edição/criação."""
    lbl = QLabel(texto)
    lbl.setStyleSheet(
        "color: #94949f; font-size: 10px; font-weight: 600;"
        " background: transparent; letter-spacing: 0.5px;"
        " text-transform: uppercase;"
    )
    return lbl


def _group_box(titulo: str) -> tuple[QWidget, QVBoxLayout]:
    """Retorna um widget agrupado com título e layout interno."""
    box = QWidget()
    box.setStyleSheet("background: transparent;")
    outer = QVBoxLayout(box)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(6)

    title_lbl = QLabel(titulo.upper())
    title_lbl.setStyleSheet(
        "color: #6366f1; font-size: 9px; font-weight: 700;"
        " letter-spacing: 1.2px; background: transparent;"
    )
    outer.addWidget(title_lbl)
    return box, outer


def _form_row(label_text: str, widget: QWidget, layout: QGridLayout, row: int, col_offset: int = 0) -> None:
    """Adiciona um par label+campo num QGridLayout de 2 colunas."""
    lbl = _input_label(label_text)
    lbl.setStyleSheet(lbl.styleSheet() + " border: none;")
    layout.addWidget(lbl, row * 2, col_offset)
    layout.addWidget(widget, row * 2 + 1, col_offset)


# ── Painel de Foto ────────────────────────────────────────────────────────────

class _FotoPanel(QWidget):
    """Painel reutilizável para exibir/trocar/remover foto."""

    def __init__(self, foto_path: str | None = None, read_only: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(200)
        self._foto_ref: list[str | None] = [foto_path]
        self._read_only = read_only

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._foto_label = QLabel()
        self._foto_label.setFixedSize(200, 200)
        self._foto_label.setAlignment(Qt.AlignCenter)
        self._foto_label.setStyleSheet(
            "background-color: #1a1a2e; border: 1px solid #2a2a3e;"
            " border-radius: 10px; font-size: 12px; color: #6b7280;"
        )
        layout.addWidget(self._foto_label)
        self._atualizar_foto(foto_path)

        if not read_only:
            btn_trocar = QPushButton("\U0001f4c1 Trocar Foto")
            btn_trocar.setCursor(Qt.PointingHandCursor)
            btn_trocar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
            btn_trocar.clicked.connect(self._trocar)
            layout.addWidget(btn_trocar)

            btn_rem = QPushButton("\U0001f5d1 Remover")
            btn_rem.setCursor(Qt.PointingHandCursor)
            btn_rem.setStyleSheet(ESTILO_BOTAO_ERRO)
            btn_rem.clicked.connect(self._remover)
            layout.addWidget(btn_rem)

        layout.addStretch()

    def _atualizar_foto(self, path: str | None) -> None:
        if path and Path(path).exists():
            pm = QPixmap(path)
            if not pm.isNull():
                self._foto_label.setPixmap(
                    pm.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                self._foto_label.setStyleSheet("border-radius: 10px; background: transparent;")
                return
        self._foto_label.clear()
        self._foto_label.setText("\U0001f4f7\nSem foto")
        self._foto_label.setStyleSheet(
            "background-color: #1a1a2e; border: 1px solid #2a2a3e;"
            " border-radius: 10px; font-size: 12px; color: #6b7280;"
        )

    def _trocar(self) -> None:
        p, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Foto", "", "Imagens (*.png *.jpg *.jpeg *.bmp)"
        )
        if p:
            self._foto_ref[0] = p
            self._atualizar_foto(p)

    def _remover(self) -> None:
        self._foto_ref[0] = None
        self._atualizar_foto(None)

    @property
    def foto_path(self) -> str | None:
        return self._foto_ref[0]


# ── Formulário compartilhado Criar/Editar ────────────────────────────────────

class _PrinterForm(QWidget):
    """
    Formulário de impressora usado tanto em 'Nova' quanto em 'Editar'.
    Organizado em seções visuais com scroll.
    """

    def __init__(
        self,
        printer: Any | None,
        company_service: Any,
        technician_service: Any,
        printer_service: Any,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._printer = printer
        self._company_service = company_service
        self._technician_service = technician_service
        self._printer_service = printer_service

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        content = QVBoxLayout(container)
        content.setContentsMargins(2, 4, 12, 4)
        content.setSpacing(14)

        # ── SEÇÃO: Identificação ─────────────────────────────
        id_box, id_layout = _group_box("Identificação")
        id_grid = QGridLayout()
        id_grid.setSpacing(8)
        id_grid.setHorizontalSpacing(16)

        self.pat = self._campo_texto("Número do patrimônio", 80)
        self.serial = self._campo_texto("Número de série", 80)
        self.modelo = self._campo_texto("Modelo da impressora", 80)
        self.marca = self._campo_texto("Marca (HP, Brother...)", 80)

        id_grid.addWidget(_input_label("Patrimônio *"), 0, 0)
        id_grid.addWidget(self.pat, 1, 0)
        self._err_pat = self._err_lbl()
        id_grid.addWidget(self._err_pat, 2, 0)

        id_grid.addWidget(_input_label("Serial"), 0, 1)
        id_grid.addWidget(self.serial, 1, 1)
        id_grid.addWidget(self._err_lbl(), 2, 1)

        id_grid.addWidget(_input_label("Modelo"), 3, 0)
        id_grid.addWidget(self.modelo, 4, 0)

        id_grid.addWidget(_input_label("Marca"), 3, 1)
        id_grid.addWidget(self.marca, 4, 1)

        id_grid.setColumnStretch(0, 1)
        id_grid.setColumnStretch(1, 1)
        id_layout.addLayout(id_grid)
        content.addWidget(id_box)

        # ── SEÇÃO: Status e Tipo ─────────────────────────────
        st_box, st_layout = _group_box("Status e Tipo")
        st_grid = QGridLayout()
        st_grid.setSpacing(8)
        st_grid.setHorizontalSpacing(16)

        self.status = QComboBox()
        configurar_combo(self.status)
        self.status.addItems(["Operacional", "Em uso", "Em manutenção", "Parada", "Aguardando peça", "Sucata"])

        self.tipo = QComboBox()
        configurar_combo(self.tipo)
        self.tipo.addItems(["", "Laser", "Jato de tinta", "Multifuncional"])

        st_grid.addWidget(_input_label("Status"), 0, 0)
        st_grid.addWidget(self.status, 1, 0)
        st_grid.addWidget(_input_label("Tipo"), 0, 1)
        st_grid.addWidget(self.tipo, 1, 1)
        st_grid.setColumnStretch(0, 1)
        st_grid.setColumnStretch(1, 1)
        st_layout.addLayout(st_grid)
        content.addWidget(st_box)

        # ── SEÇÃO: Localização e Rede ─────────────────────────
        loc_box, loc_layout = _group_box("Localização e Rede")
        loc_grid = QGridLayout()
        loc_grid.setSpacing(8)
        loc_grid.setHorizontalSpacing(16)

        self.local = QComboBox()
        self.local.setEditable(True)
        configurar_combo(self.local)
        cmp = self.local.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.local.addItem("")
        for emp in self._company_service.listar_todas():
            self.local.addItem(f"\U0001f3e2 {emp.nome}")
        for nome in self._printer_service.locais_distintos():
            if nome and nome not in {e.nome for e in self._company_service.listar_todas()}:
                self.local.addItem(f"\U0001f4cd {nome}")

        self.ip = self._campo_texto("192.168.0.100", 45)
        self.mac = self._campo_texto("AA:BB:CC:DD:EE:FF", 17)

        loc_grid.addWidget(_input_label("Local Atual"), 0, 0)
        loc_grid.addWidget(self.local, 1, 0)
        loc_grid.addWidget(_input_label("IP Rede"), 0, 1)
        loc_grid.addWidget(self.ip, 1, 1)
        loc_grid.addWidget(_input_label("MAC Address"), 2, 0)
        loc_grid.addWidget(self.mac, 3, 0)
        loc_grid.setColumnStretch(0, 1)
        loc_grid.setColumnStretch(1, 1)
        loc_layout.addLayout(loc_grid)
        content.addWidget(loc_box)

        # ── SEÇÃO: Técnico e Revisão ─────────────────────────
        tec_box, tec_layout = _group_box("Técnico e Revisão")
        tec_grid = QGridLayout()
        tec_grid.setSpacing(8)
        tec_grid.setHorizontalSpacing(16)

        self.tec = QComboBox()
        self.tec.setEditable(True)
        configurar_combo(self.tec)
        self.tec.addItem("")
        for t in self._technician_service.listar_ativos():
            self.tec.addItem(t.nome_exibicao)

        self.revisao = self._campo_texto("dd/mm/aaaa", 10)
        self.revisao.textChanged.connect(self._mascara_data)

        tec_grid.addWidget(_input_label("Técnico Responsável"), 0, 0)
        tec_grid.addWidget(self.tec, 1, 0)
        tec_grid.addWidget(_input_label("Última Revisão"), 0, 1)
        tec_grid.addWidget(self.revisao, 1, 1)
        tec_grid.setColumnStretch(0, 1)
        tec_grid.setColumnStretch(1, 1)
        tec_layout.addLayout(tec_grid)
        content.addWidget(tec_box)

        # ── SEÇÃO: Observações ───────────────────────────────
        obs_box, obs_layout = _group_box("Observações")

        self.obs = QTextEdit()
        self.obs.setPlaceholderText("Observações gerais sobre a impressora...")
        self.obs.setStyleSheet(ESTILO_INPUT)
        self.obs.setFixedHeight(100)

        obs_layout.addWidget(_input_label("Observações"))
        obs_layout.addWidget(self.obs)
        content.addWidget(obs_box)

        # ── SEÇÃO: Peças Faltantes ──────────────────────────
        pecas_box, pecas_layout = _group_box("Peças Faltantes")

        self.pecas = QTextEdit()
        self.pecas.setPlaceholderText("Peças faltantes ou que precisam de reposição...")
        self.pecas.setStyleSheet(ESTILO_INPUT)
        self.pecas.setFixedHeight(100)

        pecas_layout.addWidget(_input_label("Peças Faltantes"))
        pecas_layout.addWidget(self.pecas)
        content.addWidget(pecas_box)

        content.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

        # Preencher se editando
        if printer:
            self._preencher(printer)

        # Validação
        ValidadorCampo(self.pat, obrigatorio, self._err_pat)

    # ── helpers ─────────────────────────────────────────────
    def _campo_texto(self, placeholder: str, max_len: int) -> QLineEdit:
        le = QLineEdit()
        le.setPlaceholderText(placeholder)
        le.setMaxLength(max_len)
        le.setStyleSheet(ESTILO_INPUT)
        return le

    def _err_lbl(self) -> QLabel:
        lbl = QLabel()
        lbl.setStyleSheet(
            "color: #ef4444; font-size: 9px; background: transparent;"
            " padding: 0; margin: 0; border: none;"
        )
        lbl.hide()
        return lbl

    def _mascara_data(self, texto: str) -> None:
        le = self.sender()
        if not isinstance(le, QLineEdit):
            return
        old_pos = le.cursorPosition()
        digits = "".join(c for c in texto if c.isdigit())[:8]
        if not digits and texto:
            le.blockSignals(True)
            le.clear()
            le.blockSignals(False)
            return
        partes = [digits[:2]]
        if len(digits) > 2:
            partes.append(digits[2:4])
        if len(digits) > 4:
            partes.append(digits[4:8])
        nova = "/".join(partes)
        if nova != texto:
            le.blockSignals(True)
            le.setText(nova)
            le.blockSignals(False)
            le.setCursorPosition(old_pos + (len(nova) - len(texto)))

    def _preencher(self, p: Any) -> None:
        self.pat.setText(p.patrimonio or "")
        self.serial.setText(p.serial or "")
        self.modelo.setText(p.modelo or "")
        self.marca.setText(p.marca or "")
        if p.status:
            self.status.setCurrentText(p.status)
        if p.tipo in ["Laser", "Jato de tinta", "Multifuncional"]:
            self.tipo.setCurrentText(p.tipo)
        if p.local_atual:
            idx = self.local.findText(p.local_atual)
            if idx >= 0:
                self.local.setCurrentIndex(idx)
            else:
                self.local.setCurrentText(p.local_atual)
        self.ip.setText(p.ip_rede or "")
        self.mac.setText(p.mac_address or "")
        if p.tecnico:
            self.tec.setCurrentText(p.tecnico)
        if p.proxima_revisao:
            self.revisao.setText(formatar_data(p.proxima_revisao))
        self.obs.setPlainText(p.observacao or "")
        self.pecas.setPlainText(p.pecas_faltantes or "")

    def coletar(self) -> dict[str, Any]:
        return dict(
            patrimonio=self.pat.text().strip(),
            serial=self.serial.text().strip(),
            modelo=self.modelo.text().strip(),
            marca=self.marca.text().strip(),
            status=self.status.currentText(),
            tipo=self.tipo.currentText(),
            local_atual=limpar_local(self.local.currentText()),
            ip_rede=self.ip.text().strip(),
            mac_address=self.mac.text().strip(),
            tecnico=self.tec.currentText().strip(),
            proxima_revisao=parse_data(self.revisao.text()) or None,
            observacao=self.obs.toPlainText().strip(),
            pecas_faltantes=self.pecas.toPlainText().strip(),
        )

    @property
    def patrimonio_valido(self) -> bool:
        return bool(self.pat.text().strip())


# ── Dialog de Criar/Editar ────────────────────────────────────────────────────

class _PrinterDialog(QDialog):
    """Dialog unificado para criar ou editar impressora."""

    def __init__(
        self,
        printer_service: Any,
        company_service: Any,
        technician_service: Any,
        printer: Any | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._printer_service = printer_service
        self._company_service = company_service
        self._technician_service = technician_service
        self._printer = printer
        self._foto_path_final: str | None = printer.foto_path if printer else None

        is_edit = printer is not None
        self.setWindowTitle(
            f"\u270f\ufe0f  Editar \u2014 {printer.patrimonio}" if is_edit else "\u2795  Nova Impressora"
        )
        self.setMinimumSize(860, 640)
        self.setStyleSheet(ESTILO_DIALOG)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header do dialog ─────────────────────────────────
        header = QFrame()
        header.setStyleSheet(
            "QFrame { background: rgba(14,14,22,0.8);"
            " border-bottom: 1px solid rgba(42,42,62,0.7); }"
        )
        header.setFixedHeight(56)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 20, 0)

        icon = "\u270f\ufe0f" if is_edit else "\u2795"
        title_lbl = QLabel(f"{icon}  {'Editar Impressora' if is_edit else 'Nova Impressora'}")
        title_lbl.setStyleSheet(
            "color: #e8e8f0; font-size: 15px; font-weight: 700;"
            " background: transparent; border: none;"
        )
        h_layout.addWidget(title_lbl)

        if is_edit:
            badge = QLabel(printer.patrimonio)
            badge.setStyleSheet(
                "color: #6366f1; font-size: 11px; font-weight: 600;"
                " background: rgba(99,102,241,0.1);"
                " border: 1px solid rgba(99,102,241,0.3);"
                " border-radius: 6px; padding: 3px 10px;"
            )
            h_layout.addWidget(badge)

        h_layout.addStretch()
        root.addWidget(header)

        # ── Corpo: formulário + foto ─────────────────────────
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(20, 16, 20, 12)
        body_layout.setSpacing(20)

        # Formulário (esquerda)
        self._form = _PrinterForm(printer, company_service, technician_service, printer_service)
        body_layout.addWidget(self._form, stretch=1)

        # Foto (direita)
        foto_panel_container = QWidget()
        foto_panel_container.setStyleSheet("background: transparent;")
        foto_col = QVBoxLayout(foto_panel_container)
        foto_col.setContentsMargins(0, 0, 0, 0)
        foto_col.setSpacing(12)

        foto_label_title = _secao_label("Foto")
        foto_label_title.setStyleSheet(
            "color: #6366f1; font-size: 9px; font-weight: 700;"
            " letter-spacing: 1.2px; background: transparent;"
        )
        foto_col.addWidget(foto_label_title)

        self._foto_panel = _FotoPanel(
            foto_path=printer.foto_path if printer else None,
            read_only=False,
        )
        foto_col.addWidget(self._foto_panel)
        foto_col.addStretch()
        body_layout.addWidget(foto_panel_container)

        root.addWidget(body, stretch=1)

        # ── Footer com botões ────────────────────────────────
        footer = QFrame()
        footer.setStyleSheet(
            "QFrame { background: rgba(14,14,22,0.6);"
            " border-top: 1px solid rgba(42,42,62,0.7); }"
        )
        footer.setFixedHeight(60)
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(20, 0, 20, 0)
        f_layout.setSpacing(10)

        btn_salvar = QPushButton("\U0001f4be  Salvar")
        btn_salvar.setToolTip("Salvar as alterações")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_salvar.setMinimumWidth(120)
        btn_salvar.clicked.connect(self._salvar)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setToolTip("Descartar alterações e fechar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_cancelar.clicked.connect(self.reject)

        f_layout.addStretch()
        f_layout.addWidget(btn_cancelar)
        f_layout.addWidget(btn_salvar)
        root.addWidget(footer)

        self._dados_salvos: dict[str, Any] | None = None

    def _salvar(self) -> None:
        if not self._form.patrimonio_valido:
            QMessageBox.warning(self, "Aviso", "Patrimônio é obrigatório.")
            return

        dados = self._form.coletar()

        # Verificar duplicata de patrimônio
        pat = dados["patrimonio"]
        if self._printer is None or pat != self._printer.patrimonio:
            existente = self._printer_service.verificar_patrimonio_existe(pat)
            if existente:
                QMessageBox.warning(
                    self, "Patrimônio Duplicado",
                    f"Já existe uma impressora com o patrimônio '{pat}'!\n\n"
                    f"Modelo: {existente.modelo}\n"
                    f"Local: {existente.local_atual or 'N/A'}\n"
                    f"Status: {existente.status or 'N/A'}"
                )
                return

        # Processar foto
        foto_panel_path = self._foto_panel.foto_path
        if self._printer is None:
            if foto_panel_path and foto_panel_path != getattr(self._printer, "foto_path", None):
                try:
                    import uuid
                    ext = Path(foto_panel_path).suffix
                    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
                    dest = str(PHOTO_DIR / f"{uuid.uuid4()}{ext}")
                    shutil.copy2(foto_panel_path, dest)
                    dados["foto_path"] = dest
                except Exception:
                    dados["foto_path"] = None
            else:
                dados["foto_path"] = None
        else:
            if foto_panel_path != self._printer.foto_path:
                if foto_panel_path and not foto_panel_path.startswith(str(PHOTO_DIR)):
                    try:
                        ext = Path(foto_panel_path).suffix
                        PHOTO_DIR.mkdir(parents=True, exist_ok=True)
                        dest = str(PHOTO_DIR / f"{self._printer.id}{ext}")
                        shutil.copy2(foto_panel_path, dest)
                        dados["foto_path"] = dest
                    except Exception:
                        dados["foto_path"] = foto_panel_path
                else:
                    dados["foto_path"] = foto_panel_path
            else:
                dados["foto_path"] = self._printer.foto_path

        self._dados_salvos = dados
        self.accept()

    def dados(self) -> dict[str, Any] | None:
        return self._dados_salvos


# ── Dialog de Detalhes ────────────────────────────────────────────────────────

class _PrinterDetailDialog(QDialog):
    """Dialog de visualização detalhada de uma impressora."""

    def __init__(
        self,
        printer: Any,
        activity_service: Any,
        printer_location_service: Any,
        part_service: Any,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._printer = printer
        self._activity_service = activity_service
        self._printer_location_service = printer_location_service
        self._part_service = part_service

        self.setWindowTitle(f"Impressora \u2014 {printer.patrimonio}")
        self.setMinimumSize(820, 600)
        self.setStyleSheet(ESTILO_DIALOG)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Cabeçalho da impressora ──────────────────────────
        root.addWidget(self._build_header())

        # ── Abas de conteúdo ─────────────────────────────────
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                color: #717182; font-size: 12px; font-weight: 500;
                padding: 10px 20px; border: none;
                border-bottom: 2px solid transparent;
                background: transparent;
            }
            QTabBar::tab:hover { color: #e8e8f0; }
            QTabBar::tab:selected {
                color: #6366f1; font-weight: 700;
                border-bottom-color: #6366f1;
            }
            QTabBar { background: rgba(14,14,22,0.6); border-bottom: 1px solid rgba(42,42,62,0.5); }
        """)
        tabs.addTab(self._build_tab_geral(), "\U0001f4cb  Dados Gerais")
        tabs.addTab(self._build_tab_atividades(), "\U0001f527  Atividades")
        tabs.addTab(self._build_tab_locais(), "\U0001f4cd  Histórico de Locais")
        root.addWidget(tabs, stretch=1)

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setStyleSheet("QFrame { background: transparent; }")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(20)

        # Foto miniatura
        foto_lbl = QLabel()
        foto_lbl.setFixedSize(72, 72)
        foto_lbl.setAlignment(Qt.AlignCenter)
        foto_lbl.setStyleSheet(
            "background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.2);"
            " border-radius: 12px; color: #6366f1; font-size: 28px;"
        )
        p = self._printer
        if p.foto_path and Path(p.foto_path).exists():
            pm = QPixmap(p.foto_path)
            if not pm.isNull():
                foto_lbl.setPixmap(pm.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                foto_lbl.setStyleSheet("border-radius: 12px;")
        else:
            foto_lbl.setText("\U0001f5a8")
        layout.addWidget(foto_lbl)

        # Info principal
        info_col = QVBoxLayout()
        info_col.setSpacing(4)

        pat_lbl = QLabel(p.patrimonio)
        pat_lbl.setStyleSheet(
            "color: #e8e8f0; font-size: 20px; font-weight: 700;"
            " background: transparent; letter-spacing: -0.3px;"
        )
        info_col.addWidget(pat_lbl)

        modelo_row = QHBoxLayout()
        modelo_row.setSpacing(8)
        if p.marca:
            marca_lbl = QLabel(p.marca)
            marca_lbl.setStyleSheet(
                "color: #717182; font-size: 13px; background: transparent;"
            )
            modelo_row.addWidget(marca_lbl)
            dot = QLabel("\u00b7")
            dot.setStyleSheet("color: #3a3a50; background: transparent;")
            modelo_row.addWidget(dot)
        if p.modelo:
            modelo_lbl = QLabel(p.modelo)
            modelo_lbl.setStyleSheet(
                "color: #94949f; font-size: 13px; background: transparent;"
            )
            modelo_row.addWidget(modelo_lbl)
        modelo_row.addStretch()
        info_col.addLayout(modelo_row)
        layout.addLayout(info_col, stretch=1)

        # Status e local (à direita)
        meta_col = QVBoxLayout()
        meta_col.setSpacing(6)
        meta_col.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        status_lbl = _badge_status(p.status or "—")
        status_lbl.setAlignment(Qt.AlignRight)
        meta_col.addWidget(status_lbl)

        if p.local_atual:
            local_lbl = QLabel(f"\U0001f4cd {p.local_atual}")
            local_lbl.setStyleSheet(
                "color: #717182; font-size: 12px; background: transparent;"
            )
            local_lbl.setAlignment(Qt.AlignRight)
            meta_col.addWidget(local_lbl)

        layout.addLayout(meta_col)
        return header

    def _build_tab_geral(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        p = self._printer

        # ── Bloco 1: Identificação ───────────────────────────
        id_box, id_lay = _group_box("Identificação")
        id_grid = QGridLayout()
        id_grid.setSpacing(12)
        id_grid.setHorizontalSpacing(24)

        campos_id = [
            ("Patrimônio", p.patrimonio or "—"),
            ("Serial", p.serial or "—"),
            ("Modelo", p.modelo or "—"),
            ("Marca", p.marca or "—"),
            ("Tipo", p.tipo or "—"),
        ]
        for i, (lbl, val) in enumerate(campos_id):
            col = i % 2
            row = (i // 2) * 2
            id_grid.addWidget(_campo_rotulo(lbl), row, col)
            id_grid.addWidget(_campo_readonly(val), row + 1, col)

        id_grid.setColumnStretch(0, 1)
        id_grid.setColumnStretch(1, 1)
        id_lay.addLayout(id_grid)
        layout.addWidget(id_box)

        # ── Bloco 2: Localização e Rede ──────────────────────
        loc_box, loc_lay = _group_box("Localização e Rede")
        loc_grid = QGridLayout()
        loc_grid.setSpacing(12)
        loc_grid.setHorizontalSpacing(24)

        campos_loc = [
            ("Local Atual", p.local_atual or "—"),
            ("IP Rede", p.ip_rede or "—"),
            ("MAC Address", p.mac_address or "—"),
        ]
        for i, (lbl, val) in enumerate(campos_loc):
            col = i % 2
            row = (i // 2) * 2
            loc_grid.addWidget(_campo_rotulo(lbl), row, col)
            loc_grid.addWidget(_campo_readonly(val), row + 1, col)

        loc_grid.setColumnStretch(0, 1)
        loc_grid.setColumnStretch(1, 1)
        loc_lay.addLayout(loc_grid)
        layout.addWidget(loc_box)

        # ── Bloco 3: Manutenção ──────────────────────────────
        man_box, man_lay = _group_box("Manutenção")
        man_grid = QGridLayout()
        man_grid.setSpacing(12)
        man_grid.setHorizontalSpacing(24)

        rev_val = formatar_data(p.proxima_revisao) if p.proxima_revisao else "—"
        campos_man = [
            ("Técnico Responsável", p.tecnico or "—"),
            ("Última Revisão", rev_val),
        ]
        for i, (lbl, val) in enumerate(campos_man):
            man_grid.addWidget(_campo_rotulo(lbl), 0, i)
            man_grid.addWidget(_campo_readonly(val), 1, i)

        man_grid.setColumnStretch(0, 1)
        man_grid.setColumnStretch(1, 1)
        man_lay.addLayout(man_grid)
        layout.addWidget(man_box)

        # ── Bloco 4: Observações ─────────────────────────────
        if p.observacao:
            obs_box, obs_lay = _group_box("Observações")
            obs_lay.addWidget(_campo_readonly(p.observacao))
            layout.addWidget(obs_box)

        # ── Bloco 5: Peças Faltantes ────────────────────────
        if p.pecas_faltantes:
            pecas_box, pecas_lay = _group_box("Peças Faltantes")
            pecas_lay.addWidget(_campo_readonly(p.pecas_faltantes))
            layout.addWidget(pecas_box)

        layout.addStretch()
        scroll.setWidget(container)

        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        return tab

    def _build_tab_atividades(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        atividades = self._activity_service.listar_por_impressora(self._printer.id)

        if not atividades:
            empty = QLabel("Nenhuma atividade registrada para esta impressora.")
            empty.setStyleSheet("color: #717182; font-size: 13px; padding: 40px; background: transparent;")
            empty.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty)
            return tab

        t = TabelaPadrao(["Data/Hora", "Tipo", "Descrição", "Peças", "Status", "Técnico"])
        t.setRowCount(len(atividades))
        for i, a in enumerate(atividades):
            t.setItem(i, 0, QTableWidgetItem(formatar_data_hora(a.event_at) if a.event_at else "—"))

            cor_tipo = "#f59e0b" if a.kind == "MANUTENCAO" else "#6366f1"
            label_tipo = "Manutenção" if a.kind == "MANUTENCAO" else "Movimentação"
            t.definir_badge(i, 1, label_tipo, cor_tipo)

            t.setItem(i, 2, QTableWidgetItem(a.notes or "—"))
            t.setItem(i, 3, QTableWidgetItem(a.parts_used or "—"))
            t.setItem(i, 4, QTableWidgetItem(a.status_atividade or "—"))

            nome_tec = a.technician.nome_exibicao if a.technician else "—"
            t.setItem(i, 5, QTableWidgetItem(nome_tec))
        t.redimensionar()
        layout.addWidget(t)
        return tab

    def _build_tab_locais(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        registros = (
            self._printer_location_service.listar_por_impressora(self._printer.id)
            if self._printer_location_service else []
        )

        t = TabelaPadrao(["Data", "Local", "Observação", "Registrado em"])
        t.setRowCount(len(registros))
        for i, r in enumerate(registros):
            t.setItem(i, 0, QTableWidgetItem(formatar_data(r.data) if r.data else "—"))
            t.setItem(i, 1, QTableWidgetItem(r.local or "—"))
            t.setItem(i, 2, QTableWidgetItem(r.observacao or "—"))
            t.setItem(i, 3, QTableWidgetItem(formatar_data_hora(r.created_at) if r.created_at else "—"))
        t.redimensionar()
        layout.addWidget(t)

        if not registros:
            empty = QLabel("Nenhum registro de localização encontrado.")
            empty.setStyleSheet("color: #717182; font-size: 13px; padding: 20px; background: transparent;")
            empty.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty)

        return tab


# ── Página Principal ──────────────────────────────────────────────────────────

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
    _impressoras_visiveis: list[Any]

    def __init__(
        self,
        session: Any,
        printer_service: Any,
        company_service: Any,
        technician_service: Any,
        activity_service: Any,
        part_service: Any,
        printer_location_service: Any = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.session = session
        self.printer_service = printer_service
        self.company_service = company_service
        self.technician_service = technician_service
        self.activity_service = activity_service
        self.part_service = part_service
        self.printer_location_service = printer_location_service
        self._impressoras_visiveis = []
        self._filtro_atual = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Header ───────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(10)

        titulo_col = QVBoxLayout()
        titulo_col.setSpacing(2)
        titulo = QLabel("Impressoras")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        titulo_col.addWidget(titulo)
        sub = QLabel("Gerencie todas as impressoras cadastradas")
        sub.setStyleSheet(ESTILO_SUBTITULO)
        titulo_col.addWidget(sub)
        header.addLayout(titulo_col)
        header.addStretch()

        self.search = SearchBar(placeholder="Buscar por patrimônio, modelo, serial ou local...")
        self.search.textChanged().connect(lambda t: self.filtrar(t))
        header.addWidget(self.search)

        btn_nova = QPushButton("\u2795  Nova Impressora")
        btn_nova.setToolTip("Cadastrar uma nova impressora")
        btn_nova.setCursor(Qt.PointingHandCursor)
        btn_nova.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
        btn_nova.clicked.connect(self._nova)
        header.addWidget(btn_nova)

        btn_importar = QPushButton("\U0001f4e5  Importar")
        btn_importar.setToolTip("Importar impressoras de um arquivo CSV ou XLSX")
        btn_importar.setCursor(Qt.PointingHandCursor)
        btn_importar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_importar.clicked.connect(lambda: self._importar())
        header.addWidget(btn_importar)

        btn_atualizar = QPushButton("\U0001f504  Atualizar")
        btn_atualizar.setToolTip("Recarregar a lista de impressoras")
        btn_atualizar.setCursor(Qt.PointingHandCursor)
        btn_atualizar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_atualizar.clicked.connect(self.recarregar)
        header.addWidget(btn_atualizar)

        layout.addLayout(header)

        # ── Tabela ───────────────────────────────────────────
        colunas = ["Patrimônio", "Serial", "Modelo", "Marca", "Status", "Local Atual", "Atividades"]
        self.tabela = TabelaPadrao(colunas)
        self.tabela.cellDoubleClicked.connect(self._detalhes)
        layout.addWidget(self.tabela)

        self._paginacao = PaginacaoWidget()
        self._paginacao.pagina_alterada.connect(lambda p: self._carregar())
        layout.addWidget(self._paginacao)

        self._carregar()

    def recarregar(self) -> None:
        self._filtro_atual = None
        self._paginacao.configurar(self.printer_service.contar_todos(), pagina_atual=1)
        self._carregar()

    def _carregar(self) -> None:
        impressoras = self.printer_service.listar_todos(
            filtro=self._filtro_atual,
            limite=self._paginacao.limit,
            offset=self._paginacao.offset,
        )
        self._impressoras_visiveis = impressoras
        total = self.printer_service.contar_todos(filtro=self._filtro_atual)
        self._paginacao.configurar(
            total, pagina_atual=self._paginacao.pagina,
            itens_por_pagina=self._paginacao.limit,
        )

        ids = [p.id for p in impressoras]
        counts = self.printer_service.contar_atividades(ids) if ids else {}

        self.tabela.setRowCount(len(impressoras))
        for i, p in enumerate(impressoras):
            pat_item = QTableWidgetItem(p.patrimonio)
            pat_item.setForeground(QColor(COR["texto"]))
            self.tabela.setItem(i, 0, pat_item)
            self.tabela.setItem(i, 1, QTableWidgetItem(p.serial or "—"))
            self.tabela.setItem(i, 2, QTableWidgetItem(p.modelo))
            self.tabela.setItem(i, 3, QTableWidgetItem(p.marca or "—"))

            cor = STATUS_CORES.get(p.status, "#94949f")
            self.tabela.definir_badge(i, 4, p.status, cor)

            self.tabela.setItem(i, 5, QTableWidgetItem(p.local_atual or "—"))

            cnt = QTableWidgetItem(str(counts.get(p.id, 0)))
            cnt.setTextAlignment(Qt.AlignCenter)
            cnt.setForeground(QColor(COR["texto_sec"]))
            self.tabela.setItem(i, 6, cnt)

        self.tabela.redimensionar()

    def filtrar(self, texto: str) -> None:
        self._filtro_atual = texto if texto else None
        self._carregar()

    # ── Detalhes ─────────────────────────────────────────────

    def _detalhes(self, row: int) -> None:
        if row < 0 or row >= len(self._impressoras_visiveis):
            return
        printer = self._impressoras_visiveis[row]

        detail_dlg = _PrinterDetailDialog(
            printer=printer,
            activity_service=self.activity_service,
            printer_location_service=self.printer_location_service,
            part_service=self.part_service,
            parent=self,
        )

        # Botões de ação no footer do dialog de detalhes
        footer = QFrame()
        footer.setStyleSheet(
            "QFrame { background: rgba(14,14,22,0.6);"
            " border-top: 1px solid rgba(42,42,62,0.7); }"
        )
        footer.setFixedHeight(60)
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(20, 0, 20, 0)
        f_lay.setSpacing(10)

        btn_edit = QPushButton("\u270f\ufe0f  Editar")
        btn_edit.setToolTip("Abrir formulário de edição desta impressora")
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setStyleSheet(ESTILO_BOTAO_AVISO)
        btn_edit.clicked.connect(lambda: self._editar_impressora(printer, row, detail_dlg))

        btn_del = QPushButton("\U0001f5d1  Excluir")
        btn_del.setToolTip("Excluir esta impressora (pode ser desfeito pela Lixeira)")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_del.clicked.connect(lambda: self._excluir_impressora(detail_dlg, printer))

        btn_imp = QPushButton("\U0001f4c1  Importar Locais")
        btn_imp.setToolTip("Importar histórico de localizações desta impressora a partir de um arquivo CSV ou XLSX")
        btn_imp.setCursor(Qt.PointingHandCursor)
        btn_imp.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_imp.clicked.connect(lambda: self._importar_locais(detail_dlg, printer))

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setCursor(Qt.PointingHandCursor)
        btn_fechar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_fechar.clicked.connect(detail_dlg.accept)

        f_lay.addWidget(btn_edit)
        f_lay.addWidget(btn_del)
        f_lay.addWidget(btn_imp)
        f_lay.addStretch()
        f_lay.addWidget(btn_fechar)

        detail_dlg.layout().addWidget(footer)
        detail_dlg.exec()

    # ── Nova impressora ───────────────────────────────────────

    def _nova(self) -> None:
        dlg = _PrinterDialog(
            printer_service=self.printer_service,
            company_service=self.company_service,
            technician_service=self.technician_service,
            printer=None,
            parent=self,
        )
        if dlg.exec() == QDialog.Accepted:
            dados = dlg.dados()
            if dados:
                with tratar_erro("criar impressora"):
                    self.printer_service.criar(**dados)
                    ToastManager.sucesso(f"Impressora '{dados['patrimonio']}' criada com sucesso!")
                    self.recarregar()

    # ── Editar ────────────────────────────────────────────────

    def _editar_impressora(self, printer: Any, row: int, parent_dialog: QDialog | None = None) -> None:
        dlg = _PrinterDialog(
            printer_service=self.printer_service,
            company_service=self.company_service,
            technician_service=self.technician_service,
            printer=printer,
            parent=self,
        )
        if dlg.exec() == QDialog.Accepted:
            dados = dlg.dados()
            if dados:
                with tratar_erro("atualizar impressora"):
                    self.printer_service.atualizar(printer, **dados)
                    ToastManager.sucesso(f"Impressora '{printer.patrimonio}' atualizada!")
                    self.recarregar()
                if parent_dialog:
                    parent_dialog.accept()
                idx = next(
                    (i for i, p in enumerate(self._impressoras_visiveis) if p.id == printer.id),
                    -1,
                )
                if idx >= 0:
                    self._detalhes(idx)

    # ── Excluir ───────────────────────────────────────────────

    def _excluir_impressora(self, parent_dialog: QDialog, printer: Any) -> None:
        if ConfirmacaoDigitarDialog.confirmar(
            "Excluir Impressora",
            f"Tem certeza que deseja excluir a impressora {printer.patrimonio}?\n\n"
            "Esta ação pode ser desfeita pela Lixeira em Configurações.",
            parent_dialog,
        ):
            with tratar_erro("excluir impressora"):
                self.printer_service.excluir(printer)
                ToastManager.mostrar(
                    f"Impressora '{printer.patrimonio}' excluída.",
                    "aviso", duracao=8000,
                    acao=(
                        "Desfazer",
                        lambda o=printer, svc=self.printer_service, pag=self: (
                            svc.restaurar(o), pag.recarregar()
                        ),
                    ),
                )
                parent_dialog.accept()
                self.recarregar()

    # ── Importar locais ───────────────────────────────────────

    def _importar_locais(self, parent_dialog: QDialog, printer: Any) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            parent_dialog, "Importar Histórico de Locais", "",
            "CSV (*.csv);;XLSX (*.xlsx)"
        )
        if not path_str:
            return
        path = Path(path_str)
        registros: list[dict[str, Any]] = []
        try:
            if path.suffix.lower() == ".csv":
                import csv
                with open(str(path), encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        registros.append(row)
            elif path.suffix.lower() == ".xlsx":
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
            QMessageBox.information(parent_dialog, "Importar", "Nenhum registro encontrado.")
            return

        try:
            importados = self.printer_location_service.importar(printer.id, registros)
            QMessageBox.information(
                parent_dialog, "Importado",
                f"{importados} registro(s) importado(s) com sucesso."
            )
            parent_dialog.accept()
            idx = next(
                (i for i, p in enumerate(self._impressoras_visiveis) if p.id == printer.id), -1
            )
            if idx >= 0:
                self._detalhes(idx)
        except Exception as e:
            QMessageBox.warning(parent_dialog, "Erro", f"Erro ao importar:\n{e}")

    # ── Importar CSV/XLSX ─────────────────────────────────────

    def _importar(self) -> None:
        dlg = ImportDialog(self, "printers", "Impressoras", self.printer_service, self.session)
        if dlg.exec() == ImportDialog.Accepted:
            self.recarregar()

    # ── Atalho para editar atividade ──────────────────────────

    def _editar_atividade(self, row: int, atividades: list[Any], printer: Any, parent_dialog: QDialog) -> None:
        """Compatibilidade: abre o dialog de edição de atividade."""
        pass
