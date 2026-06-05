from __future__ import annotations

from datetime import datetime as dt
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
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

from app.utils.helpers import formatar_data_hora
from app.utils.ui_helpers import tratar_erro
from app.utils.validacao import ValidadorCampo, obrigatorio
from app.views.styles.theme import (
    ESTILO_BOTAO_AVISO,
    ESTILO_BOTAO_ERRO,
    ESTILO_BOTAO_FECHAR,
    ESTILO_BOTAO_PRIMARIO,
    ESTILO_BOTAO_SECUNDARIO,
    configurar_combo,
    ESTILO_DIALOG,
    ESTILO_INPUT,
    ESTILO_SUBTITULO,
    ESTILO_TITULO_PAGINA,
    group_box,
    input_label,
    campo_rotulo,
    campo_readonly,
)
from app.views.widgets.confirm_dialog import ConfirmacaoDigitarDialog
from app.views.widgets.pagination import PaginacaoWidget
from app.views.widgets.search_bar import SearchBar
from app.views.widgets.table_widget import TabelaPadrao
from app.views.widgets.toast import ToastManager


CORES_TIPO: dict[str, str] = {
    "revisao": "#60a5fa",
    "critico": "#f87171",
    "aviso": "#fbbf24",
    "info": "#a78bfa",
    "estoque": "#fb923c",
}

STATUS_ALERTA: dict[bool, tuple[str, str]] = {
    True: ("Resolvido", "#34d399"),
    False: ("Pendente", "#fbbf24"),
}

TIPO_LABELS: dict[str, str] = {
    "revisao": "Revisão",
    "critico": "Crítico",
    "aviso": "Aviso",
    "info": "Informação",
    "estoque": "Estoque",
}

TIPO_OPCOES: list[str] = ["revisao", "critico", "aviso", "info", "estoque"]


class AlertasPage(QWidget):
    session: Any
    alert_service: Any
    printer_service: Any
    part_service: Any | None
    _filtro_status: str | None
    _filtro_busca: str
    btn_todos: QPushButton
    btn_pendentes: QPushButton
    btn_resolvidos: QPushButton
    lbl_contador: QLabel
    search: SearchBar
    tabela: TabelaPadrao
    _alertas_visiveis: list[Any]
    _paginacao: PaginacaoWidget

    def __init__(self, session: Any, alert_service: Any, printer_service: Any, part_service: Any | None = None) -> None:
        super().__init__()
        self.session = session
        self.alert_service = alert_service
        self.printer_service = printer_service
        self.part_service = part_service
        self._filtro_status = None
        self._filtro_busca = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(10)

        titulo = QLabel("Alertas")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        sub = QLabel("Monitore revisões, avisos e problemas das impressoras")
        sub.setStyleSheet(ESTILO_SUBTITULO)

        titulo_col = QVBoxLayout()
        titulo_col.setSpacing(2)
        titulo_col.addWidget(titulo)
        titulo_col.addWidget(sub)
        header.addLayout(titulo_col)
        header.addStretch()

        btn_estoque = QPushButton("📦  Verif. Estoque")
        btn_estoque.setCursor(Qt.PointingHandCursor)
        btn_estoque.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_estoque.setToolTip("Verificar alertas de estoque baixo")
        btn_estoque.clicked.connect(self._gerar_alertas_estoque)
        header.addWidget(btn_estoque)

        btn_novo = QPushButton("➕  Novo Alerta")
        btn_novo.setCursor(Qt.PointingHandCursor)
        btn_novo.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
        btn_novo.setToolTip("Criar novo alerta")
        btn_novo.clicked.connect(self._novo)
        header.addWidget(btn_novo)

        btn_atualizar = QPushButton("🔄  Atualizar")
        btn_atualizar.setCursor(Qt.PointingHandCursor)
        btn_atualizar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_atualizar.setToolTip("Recarregar lista de alertas")
        btn_atualizar.clicked.connect(self.recarregar)
        header.addWidget(btn_atualizar)

        layout.addLayout(header)

        filtros = QHBoxLayout()
        filtros.setSpacing(8)

        self.btn_todos = QPushButton("📋  Todos")
        self.btn_todos.setCursor(Qt.PointingHandCursor)
        self.btn_todos.setStyleSheet(self._estilo_filtro(True))
        self.btn_todos.setToolTip("Mostrar todos os alertas")
        self.btn_todos.clicked.connect(lambda: self._alternar_filtro(None))

        self.btn_pendentes = QPushButton("⏳  Pendentes")
        self.btn_pendentes.setCursor(Qt.PointingHandCursor)
        self.btn_pendentes.setStyleSheet(self._estilo_filtro(False))
        self.btn_pendentes.setToolTip("Filtrar alertas pendentes")
        self.btn_pendentes.clicked.connect(lambda: self._alternar_filtro("pendentes"))

        self.btn_resolvidos = QPushButton("✅  Resolvidos")
        self.btn_resolvidos.setCursor(Qt.PointingHandCursor)
        self.btn_resolvidos.setStyleSheet(self._estilo_filtro(False))
        self.btn_resolvidos.setToolTip("Filtrar alertas resolvidos")
        self.btn_resolvidos.clicked.connect(lambda: self._alternar_filtro("resolvidos"))

        filtros.addWidget(self.btn_todos)
        filtros.addWidget(self.btn_pendentes)
        filtros.addWidget(self.btn_resolvidos)
        filtros.addStretch()

        self.lbl_contador = QLabel("")
        self.lbl_contador.setStyleSheet("color: #475569; font-size: 12px; background: transparent;")

        layout.addLayout(filtros)

        self.search = SearchBar(placeholder="Buscar por título, impressora ou tipo...")
        self.search.textChanged().connect(lambda texto: self._buscar(texto))
        layout.addWidget(self.search)

        colunas = ["Referência", "Tipo", "Título", "Descrição", "Data", "Status"]
        self.tabela = TabelaPadrao(colunas)
        self.tabela.cellDoubleClicked.connect(self._detalhes)
        layout.addWidget(self.tabela)

        self._alertas_visiveis = []
        self._paginacao = PaginacaoWidget()
        self._paginacao.pagina_alterada.connect(lambda p: self._carregar())
        layout.addWidget(self._paginacao)

        self._carregar()

    def _estilo_filtro(self, ativo: bool) -> str:
        if ativo:
            return (
                "QPushButton { background-color: #a78bfa; color: #ffffff; border: none;"
                " border-radius: 6px; padding: 7px 16px; font-size: 12px; font-weight: 600; }"
            )
        return (
            "QPushButton { background-color: transparent; color: #475569;"
            " border: 1px solid #2e2e4a; border-radius: 6px; padding: 7px 16px;"
            " font-size: 12px; font-weight: 500; }"
            " QPushButton:hover { border-color: #4a4a6a; color: #94a3b8; }"
        )

    def _atualizar_botoes_filtro(self) -> None:
        self.btn_todos.setStyleSheet(self._estilo_filtro(self._filtro_status is None))
        self.btn_pendentes.setStyleSheet(self._estilo_filtro(self._filtro_status == "pendentes"))
        self.btn_resolvidos.setStyleSheet(self._estilo_filtro(self._filtro_status == "resolvidos"))

    def _alternar_filtro(self, status: str | None) -> None:
        self._filtro_status = status
        self._atualizar_botoes_filtro()
        self._carregar()

    def _buscar(self, texto: str) -> None:
        self._filtro_busca = texto
        self._carregar()

    def recarregar(self) -> None:
        self._filtro_busca = ""
        self._carregar()

    def _carregar(self):
        filtro = self._filtro_busca or None
        apenas_pendentes = self._filtro_status == "pendentes"
        apenas_resolvidos = self._filtro_status == "resolvidos"
        alertas = self.alert_service.listar_todos(
            apenas_pendentes=apenas_pendentes,
            apenas_resolvidos=apenas_resolvidos,
            filtro_busca=filtro,
            limite=self._paginacao.limit, offset=self._paginacao.offset,
        )
        total = self.alert_service.contar_todos(
            apenas_pendentes=apenas_pendentes,
            apenas_resolvidos=apenas_resolvidos,
            filtro_busca=filtro,
        )
        self._paginacao.configurar(total, pagina_atual=self._paginacao.pagina,
                                   itens_por_pagina=self._paginacao.limit)
        self._alertas_visiveis = alertas

        total_pendentes = self.alert_service.contar_pendentes()
        self.lbl_contador.setText(f"{total_pendentes} pendente(s)")

        self.tabela.setRowCount(len(alertas))

        for i, a in enumerate(alertas):
            if a.printer_id:
                printer = a.printer or self.printer_service.buscar_por_id(a.printer_id)
                ref = printer.patrimonio if printer else a.printer_id
            elif a.part_id:
                ref = a.part.nome if a.part else f"Peça #{a.part_id}"
            else:
                ref = "-"

            self.tabela.setItem(i, 0, self.tabela.item_colorido(ref, "#e2e8f0"))
            cor_tipo = CORES_TIPO.get(a.tipo, "#94949f")
            label_tipo = TIPO_LABELS.get(a.tipo, a.tipo)
            self.tabela.definir_badge(i, 1, label_tipo, cor_tipo)
            self.tabela.setItem(i, 2, QTableWidgetItem(a.titulo or ""))
            self.tabela.setItem(i, 3, QTableWidgetItem((a.descricao or "")[:60] + ("..." if len(a.descricao or "") > 60 else "")))
            self.tabela.setItem(i, 4, QTableWidgetItem(formatar_data_hora(a.data_alerta or a.created_at)))

            label_status, cor_status = STATUS_ALERTA.get(a.resolvido, ("Desconhecido", "#4b5563"))
            self.tabela.definir_badge(i, 5, label_status, cor_status)

        self.tabela.redimensionar()

    def _gerar_alertas_estoque(self) -> None:
        try:
            criados = self.alert_service.verificar_estoque_baixo()
            ToastManager.atualizar_status(self.alert_service.contar_pendentes())
            if criados:
                ToastManager.info(f"{criados} alerta(s) de estoque baixo gerado(s)")
            else:
                ToastManager.sucesso("Nenhuma peça com estoque crítico")
        except Exception as e:
            ToastManager.erro(f"Erro ao verificar estoque: {str(e)}")
        self.recarregar()

    def _novo(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Novo Alerta")
        dialog.setMinimumSize(520, 500)
        dialog.setStyleSheet(ESTILO_DIALOG)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        alerta_box, alerta_layout = group_box("Alerta")
        form_alerta = QFormLayout()
        form_alerta.setSpacing(8)

        printer_combo = QComboBox()
        configurar_combo(printer_combo)
        cmp = printer_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        impressoras = self.printer_service.listar_todos()
        printer_combo.addItem("(nenhuma impressora)", None)
        for p in impressoras:
            printer_combo.addItem(f"{p.patrimonio} - {p.modelo}", p.id)
        form_alerta.addRow("Impressora:", printer_combo)

        part_combo = QComboBox()
        configurar_combo(part_combo)
        cmp = part_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        part_combo.addItem("(nenhuma peça)", None)
        if self.part_service:
            partes = self.part_service.listar_todas()
            for p in partes:
                part_combo.addItem(f"{p.nome} ({p.codigo})", p.id)
        form_alerta.addRow("Peça:", part_combo)

        tipo_combo = QComboBox()
        configurar_combo(tipo_combo)
        cmp = tipo_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        for t in TIPO_OPCOES:
            tipo_combo.addItem(TIPO_LABELS.get(t, t), t)
        form_alerta.addRow("Tipo *:", tipo_combo)

        titulo_input = QLineEdit()
        titulo_input.setPlaceholderText("Título do alerta")
        titulo_input.setStyleSheet(ESTILO_INPUT)
        form_alerta.addRow("Título *:", titulo_input)

        erro_titulo = QLabel()
        erro_titulo.setStyleSheet("color: #ef4444; font-size: 10px; background: transparent;")
        erro_titulo.hide()
        form_alerta.addRow("", erro_titulo)
        ValidadorCampo(titulo_input, obrigatorio, erro_titulo)

        alerta_layout.addLayout(form_alerta)
        layout.addWidget(alerta_box)

        detalhes_box, detalhes_layout = group_box("Detalhes")
        form_detalhes = QFormLayout()
        form_detalhes.setSpacing(8)

        desc_input = QTextEdit()
        desc_input.setPlaceholderText("Descrição detalhada...")
        desc_input.setMaximumHeight(80)
        desc_input.setStyleSheet(ESTILO_INPUT)
        form_detalhes.addRow("Descrição:", desc_input)

        from PySide6.QtWidgets import QDateEdit
        data_agendada = QDateEdit()
        data_agendada.setCalendarPopup(True)
        data_agendada.setDate(data_agendada.date().addDays(1))
        data_agendada.setStyleSheet(ESTILO_INPUT)
        data_agendada.setSpecialValueText("Sem data")
        form_detalhes.addRow("Agendar para:", data_agendada)

        detalhes_layout.addLayout(form_detalhes)
        layout.addWidget(detalhes_box)

        layout.addStretch()
        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.setStyleSheet(
            "QPushButton { border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }"
            " QPushButton[text='OK'] { background-color: #a78bfa; color: white; }"
            " QPushButton[text='Cancel'] { background-color: #1f2937; color: #94a3b8; }"
        )
        btn_ok = botoes.button(QDialogButtonBox.Ok)
        if btn_ok:
            btn_ok.setToolTip("Salvar novo alerta")
        btn_cancel = botoes.button(QDialogButtonBox.Cancel)
        if btn_cancel:
            btn_cancel.setToolTip("Cancelar")
        botoes.accepted.connect(lambda: self._salvar_novo(dialog, printer_combo, part_combo, tipo_combo, titulo_input, desc_input, data_agendada))
        botoes.rejected.connect(dialog.reject)
        layout.addWidget(botoes)
        dialog.exec()

    def _salvar_novo(self, dialog: QDialog, printer_combo: QComboBox, part_combo: QComboBox, tipo_combo: QComboBox, titulo_input: QLineEdit, desc_input: QTextEdit, data_agendada: Any) -> None:
        titulo = titulo_input.text().strip()
        if not titulo:
            QMessageBox.warning(dialog, "Aviso", "Preencha o título!")
            return

        printer_id = printer_combo.currentData()
        part_id = part_combo.currentData()
        data_ag = data_agendada.date().toPython() if data_agendada.date() != data_agendada.minimumDate() else None
        from datetime import datetime, time
        data_agendada_dt = datetime.combine(data_ag, time(0, 0)) if data_ag else None

        with tratar_erro("criar alerta"):
            self.alert_service.criar(
                printer_id=printer_id,
                part_id=part_id,
                tipo=tipo_combo.currentData(),
                titulo=titulo,
                descricao=desc_input.toPlainText().strip(),
                data_agendada=data_agendada_dt,
            )
            ToastManager.atualizar_status(self.alert_service.contar_pendentes())
            ToastManager.sucesso(f"Alerta criado: {titulo}")
            agendados = self.alert_service.verificar_agendados()
            for a in agendados:
                ref = a.printer.patrimonio if a.printer else (a.part.nome if a.part else "")
                ToastManager.aviso(f"⏰ {a.titulo}{' — '+ref if ref else ''}")
            self.recarregar()
            dialog.accept()

    def _detalhes(self, row: int) -> None:
        if row < 0 or row >= len(self._alertas_visiveis):
            return
        alerta = self._alertas_visiveis[row]
        printer = alerta.printer if alerta.printer_id else None
        pat = printer.patrimonio if printer else (alerta.printer_id or "-")

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Alerta - {alerta.titulo}")
        dialog.setMinimumSize(600, 500)
        dialog.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        header_row.addWidget(QLabel(f"<b style='color:#a78bfa;font-size:18px'>{alerta.titulo}</b>"), stretch=1)

        cor_tipo = CORES_TIPO.get(alerta.tipo, "#94949f")
        label_tipo = TIPO_LABELS.get(alerta.tipo, alerta.tipo)
        badge_tipo = QLabel(label_tipo)
        badge_tipo.setStyleSheet(
            f"background-color: {cor_tipo}22; color: {cor_tipo};"
            " padding: 4px 12px; border-radius: 10px; font-size: 11px; font-weight: 700;"
        )
        header_row.addWidget(badge_tipo)

        label_status, cor_status = STATUS_ALERTA.get(alerta.resolvido, ("-", "#4b5563"))
        badge_status = QLabel(label_status)
        badge_status.setStyleSheet(
            f"background-color: {cor_status}22; color: {cor_status};"
            " padding: 4px 12px; border-radius: 10px; font-size: 11px; font-weight: 700;"
        )
        header_row.addWidget(badge_status)

        layout.addLayout(header_row)

        linha = QFrame()
        linha.setFrameShape(QFrame.HLine)
        linha.setStyleSheet("border: none; border-top: 1px solid #2a2a3e;")
        layout.addWidget(linha)

        info_box, info_layout = group_box("Informações")
        info_grid = QGridLayout()
        info_grid.setSpacing(6)
        info_grid.setHorizontalSpacing(12)

        campos_info = [
            ("🖨️ Impressora", str(pat)),
        ]
        if alerta.part_id:
            nome_peca = alerta.part.nome if alerta.part else f"ID {alerta.part_id}"
            campos_info.append(("🔧 Peça", nome_peca))
        campos_info.append(("📋 Tipo", label_tipo))
        campos_info.append(("📅 Data", formatar_data_hora(alerta.data_alerta or alerta.created_at)))
        if alerta.data_agendada:
            campos_info.append(("⏰ Agendado", formatar_data_hora(alerta.data_agendada)))
        if alerta.resolvido:
            campos_info.append(("✅ Resolvido em", formatar_data_hora(alerta.resolvido_em)))

        for i, (rotulo, valor) in enumerate(campos_info):
            col = i % 2
            row_g = (i // 2) * 2
            info_grid.addWidget(campo_rotulo(rotulo), row_g, col)
            val_lbl = QLabel(str(valor))
            val_lbl.setWordWrap(True)
            val_lbl.setStyleSheet("color: #c8c8e0; font-size: 11px; font-weight: 500; background: transparent; padding: 0; margin: 0;")
            info_grid.addWidget(val_lbl, row_g + 1, col)

        info_grid.setColumnStretch(0, 1)
        info_grid.setColumnStretch(1, 1)
        info_layout.addLayout(info_grid)
        layout.addWidget(info_box)

        desc_box, desc_layout = group_box("Descrição")
        desc_label = campo_readonly(alerta.descricao or "—")
        desc_layout.addWidget(desc_label)
        layout.addWidget(desc_box)

        botoes = QHBoxLayout()
        botoes.setSpacing(10)

        if not alerta.resolvido:
            btn_resolver = QPushButton("✅  Resolver Alerta")
            btn_resolver.setCursor(Qt.PointingHandCursor)
            btn_resolver.setMinimumHeight(38)
            btn_resolver.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
            btn_resolver.setToolTip("Marcar este alerta como resolvido")
            btn_resolver.clicked.connect(lambda: self._resolver(alerta, dialog))
            botoes.addWidget(btn_resolver)

        btn_editar = QPushButton("✏️  Editar")
        btn_editar.setCursor(Qt.PointingHandCursor)
        btn_editar.setMinimumHeight(38)
        btn_editar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_editar.setToolTip("Editar este alerta")
        btn_editar.clicked.connect(lambda: self._editar(alerta, dialog))
        botoes.addWidget(btn_editar)

        btn_excluir = QPushButton("\U0001f5d1 Excluir")
        btn_excluir.setCursor(Qt.PointingHandCursor)
        btn_excluir.setMinimumHeight(38)
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_excluir.setToolTip("Excluir este alerta (pode ser desfeito pela Lixeira)")
        btn_excluir.clicked.connect(lambda: self._excluir(alerta, dialog))
        botoes.addWidget(btn_excluir)

        botoes.addStretch()

        btn_fechar = QPushButton("❌​  Fechar")
        btn_fechar.setCursor(Qt.PointingHandCursor)
        btn_fechar.setMinimumHeight(38)
        btn_fechar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_fechar.setToolTip("Fechar janela")
        btn_fechar.clicked.connect(dialog.accept)
        botoes.addWidget(btn_fechar)

        layout.addLayout(botoes)
        dialog.exec()

    def _editar(self, alerta: Any, parent_dialog: QDialog) -> None:
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle("Editar Alerta")
        dialog.setMinimumSize(520, 540)
        dialog.setStyleSheet(ESTILO_DIALOG)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        alerta_box, alerta_layout = group_box("Alerta")
        form_alerta = QFormLayout()
        form_alerta.setSpacing(8)

        printer_combo = QComboBox()
        configurar_combo(printer_combo)
        cmp = printer_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        impressoras = self.printer_service.listar_todos()
        printer_combo.addItem("(nenhuma impressora)", None)
        idx_selecionado = 0
        for i, p in enumerate(impressoras):
            printer_combo.addItem(f"{p.patrimonio} - {p.modelo}", p.id)
            if p.id == alerta.printer_id:
                idx_selecionado = i + 1
        printer_combo.setCurrentIndex(idx_selecionado)
        form_alerta.addRow("Impressora:", printer_combo)

        part_combo = QComboBox()
        configurar_combo(part_combo)
        cmp = part_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        part_combo.addItem("(nenhuma peça)", None)
        idx_part = 0
        if self.part_service:
            partes = self.part_service.listar_todas()
            for i, p in enumerate(partes):
                part_combo.addItem(f"{p.nome} ({p.codigo})", p.id)
                if p.id == alerta.part_id:
                    idx_part = i + 1
        part_combo.setCurrentIndex(idx_part)
        form_alerta.addRow("Peça:", part_combo)

        tipo_combo = QComboBox()
        configurar_combo(tipo_combo)
        cmp = tipo_combo.completer()
        if cmp:
            cmp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        for t in TIPO_OPCOES:
            tipo_combo.addItem(TIPO_LABELS.get(t, t), t)
        tipo_combo.setCurrentIndex(TIPO_OPCOES.index(alerta.tipo) if alerta.tipo in TIPO_OPCOES else 0)
        form_alerta.addRow("Tipo *:", tipo_combo)

        titulo_input = QLineEdit()
        titulo_input.setText(alerta.titulo or "")
        titulo_input.setStyleSheet(ESTILO_INPUT)
        form_alerta.addRow("Título *:", titulo_input)

        erro_titulo = QLabel()
        erro_titulo.setStyleSheet("color: #ef4444; font-size: 10px; background: transparent;")
        erro_titulo.hide()
        form_alerta.addRow("", erro_titulo)
        ValidadorCampo(titulo_input, obrigatorio, erro_titulo)

        alerta_layout.addLayout(form_alerta)
        layout.addWidget(alerta_box)

        detalhes_box, detalhes_layout = group_box("Detalhes")
        form_detalhes = QFormLayout()
        form_detalhes.setSpacing(8)

        desc_input = QTextEdit()
        desc_input.setPlainText(alerta.descricao or "")
        desc_input.setMaximumHeight(80)
        desc_input.setStyleSheet(ESTILO_INPUT)
        form_detalhes.addRow("Descrição:", desc_input)

        from PySide6.QtWidgets import QCheckBox, QDateEdit
        chk_resolvido = QCheckBox("Alerta resolvido")
        chk_resolvido.setChecked(alerta.resolvido)
        chk_resolvido.setStyleSheet(
            "QCheckBox { color: #e2e8f0; font-size: 12px; spacing: 8px; }"
            " QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px;"
            " border: 2px solid #475569; background: transparent; }"
            " QCheckBox::indicator:checked { background-color: #a78bfa; border-color: #a78bfa; }"
        )
        form_detalhes.addRow("Status:", chk_resolvido)

        data_agendada = QDateEdit()
        data_agendada.setCalendarPopup(True)
        data_agendada.setStyleSheet(ESTILO_INPUT)
        data_agendada.setSpecialValueText("Sem data")
        if alerta.data_agendada:
            from datetime import datetime
            data_agendada.setDate(data_agendada.date().fromPython(alerta.data_agendada.date()))
        else:
            data_agendada.setDate(data_agendada.minimumDate())
        form_detalhes.addRow("Agendar para:", data_agendada)

        detalhes_layout.addLayout(form_detalhes)
        layout.addWidget(detalhes_box)

        layout.addStretch()
        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.setStyleSheet(
            "QPushButton { border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }"
            " QPushButton[text='OK'] { background-color: #a78bfa; color: white; }"
            " QPushButton[text='Cancel'] { background-color: #1f2937; color: #94a3b8; }"
        )
        btn_ok = botoes.button(QDialogButtonBox.Ok)
        if btn_ok:
            btn_ok.setToolTip("Salvar alterações do alerta")
        btn_cancel = botoes.button(QDialogButtonBox.Cancel)
        if btn_cancel:
            btn_cancel.setToolTip("Cancelar")
        botoes.accepted.connect(lambda: self._salvar_edicao(dialog, alerta, printer_combo, part_combo, tipo_combo, titulo_input, desc_input, chk_resolvido, data_agendada, parent_dialog))
        botoes.rejected.connect(dialog.reject)
        layout.addWidget(botoes)
        dialog.exec()

    def _salvar_edicao(self, dialog: QDialog, alerta: Any, printer_combo: QComboBox, part_combo: QComboBox, tipo_combo: QComboBox, titulo_input: QLineEdit, desc_input: QTextEdit, chk_resolvido: Any, data_agendada: Any, parent_dialog: QDialog) -> None:
        titulo = titulo_input.text().strip()
        if not titulo:
            QMessageBox.warning(dialog, "Aviso", "Preencha o título!")
            return

        alerta.printer_id = printer_combo.currentData()
        alerta.part_id = part_combo.currentData()
        alerta.tipo = tipo_combo.currentData()
        alerta.titulo = titulo
        alerta.descricao = desc_input.toPlainText().strip()

        data_ag = data_agendada.date().toPython() if data_agendada.date() != data_agendada.minimumDate() else None
        from datetime import datetime, time
        alerta.data_agendada = datetime.combine(data_ag, time(0, 0)) if data_ag else None

        if chk_resolvido.isChecked() and not alerta.resolvido:
            alerta.resolvido = True
            alerta.resolvido_em = dt.now()
        elif not chk_resolvido.isChecked() and alerta.resolvido:
            alerta.resolvido = False
            alerta.resolvido_em = None
        from db import safe_commit
        safe_commit(self.session)
        agendados = self.alert_service.verificar_agendados()
        for a in agendados:
            ref = a.printer.patrimonio if a.printer else (a.part.nome if a.part else "")
            ToastManager.aviso(f"⏰ {a.titulo}{' — '+ref if ref else ''}", persistente=True)
        ToastManager.atualizar_status(self.alert_service.contar_pendentes())
        ToastManager.info(f"Alerta atualizado: {titulo}")
        self.recarregar()
        dialog.accept()
        parent_dialog.accept()

    def _excluir(self, alerta: Any, dialog: QDialog) -> None:
        if ConfirmacaoDigitarDialog.confirmar(
            "Excluir Alerta",
            f"Deseja realmente excluir o alerta \"{alerta.titulo}\"?",
            dialog,
        ):
            try:
                self.alert_service.excluir(alerta)
                ToastManager.atualizar_status(self.alert_service.contar_pendentes())
                ToastManager.mostrar(
                    f"Alerta '{alerta.titulo}' excluído.",
                    "aviso", duracao=8000,
                    acao=("Desfazer", lambda o=alerta, svc=self.alert_service, pag=self: (svc.restaurar(o), ToastManager.atualizar_status(svc.contar_pendentes()), pag.recarregar())),
                )
                self.recarregar()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Erro", f"Erro ao excluir alerta:\n{e}")

    def _resolver(self, alerta: Any, dialog: QDialog) -> None:
        resp = QMessageBox.question(
            dialog, "Resolver Alerta",
            "Marcar este alerta como resolvido?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            with tratar_erro("resolver alerta"):
                self.alert_service.resolver(alerta)
                ToastManager.atualizar_status(self.alert_service.contar_pendentes())
                ToastManager.info(f"Alerta resolvido: {alerta.titulo}")
                self.recarregar()
                dialog.accept()
