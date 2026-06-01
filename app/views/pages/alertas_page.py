from datetime import datetime as dt

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
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

from app.utils.helpers import formatar_data_hora
from app.views.styles.theme import (
    ESTILO_BOTAO_AVISO,
    ESTILO_BOTAO_ERRO,
    ESTILO_BOTAO_FECHAR,
    ESTILO_BOTAO_PRIMARIO,
    ESTILO_BOTAO_SECUNDARIO,
    configurar_combo,
    ESTILO_DIALOG,
    ESTILO_INPUT,
    ESTILO_INPUT_READONLY,
    ESTILO_SUBTITULO,
    ESTILO_TITULO_PAGINA,
)
from app.views.widgets.search_bar import SearchBar
from app.views.widgets.table_widget import TabelaPadrao
from app.views.widgets.toast import ToastManager


CORES_TIPO = {
    "revisao": "#60a5fa",
    "critico": "#f87171",
    "aviso": "#fbbf24",
    "info": "#a78bfa",
    "estoque": "#fb923c",
}

STATUS_ALERTA = {
    True: ("Resolvido", "#34d399"),
    False: ("Pendente", "#fbbf24"),
}

TIPO_LABELS = {
    "revisao": "Revisão",
    "critico": "Crítico",
    "aviso": "Aviso",
    "info": "Informação",
    "estoque": "Estoque",
}

TIPO_OPCOES = ["revisao", "critico", "aviso", "info", "estoque"]


class AlertasPage(QWidget):
    def __init__(self, session, alert_service, printer_service):
        super().__init__()
        self.session = session
        self.alert_service = alert_service
        self.printer_service = printer_service
        self._apenas_pendentes = False
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
        btn_estoque.clicked.connect(self._gerar_alertas_estoque)
        header.addWidget(btn_estoque)

        btn_novo = QPushButton("➕  Novo Alerta")
        btn_novo.setCursor(Qt.PointingHandCursor)
        btn_novo.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
        btn_novo.clicked.connect(self._novo)
        header.addWidget(btn_novo)

        btn_atualizar = QPushButton("🔄  Atualizar")
        btn_atualizar.setCursor(Qt.PointingHandCursor)
        btn_atualizar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_atualizar.clicked.connect(self.recarregar)
        header.addWidget(btn_atualizar)

        layout.addLayout(header)

        filtros = QHBoxLayout()
        filtros.setSpacing(8)

        self.btn_todos = QPushButton("📋  Todos")
        self.btn_todos.setCursor(Qt.PointingHandCursor)
        self.btn_todos.setStyleSheet(self._estilo_filtro(True))
        self.btn_todos.clicked.connect(lambda: self._alternar_filtro(False))

        self.btn_pendentes = QPushButton("⏳  Pendentes")
        self.btn_pendentes.setCursor(Qt.PointingHandCursor)
        self.btn_pendentes.setStyleSheet(self._estilo_filtro(False))
        self.btn_pendentes.clicked.connect(lambda: self._alternar_filtro(True))

        filtros.addWidget(self.btn_todos)
        filtros.addWidget(self.btn_pendentes)
        filtros.addStretch()

        self.lbl_contador = QLabel("")
        self.lbl_contador.setStyleSheet("color: #475569; font-size: 12px; background: transparent;")
        filtros.addWidget(self.lbl_contador)

        layout.addLayout(filtros)

        self.search = SearchBar(placeholder="Buscar por título, impressora ou tipo...")
        self.search.textChanged().connect(lambda texto: self._buscar(texto))
        layout.addWidget(self.search)

        colunas = ["Impressora", "Tipo", "Título", "Descrição", "Data", "Status"]
        self.tabela = TabelaPadrao(colunas)
        self.tabela.cellDoubleClicked.connect(self._detalhes)
        layout.addWidget(self.tabela)

        self.recarregar()

    def _estilo_filtro(self, ativo):
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

    def _alternar_filtro(self, apenas_pendentes):
        self._apenas_pendentes = apenas_pendentes
        self.btn_todos.setStyleSheet(self._estilo_filtro(not apenas_pendentes))
        self.btn_pendentes.setStyleSheet(self._estilo_filtro(apenas_pendentes))
        self.recarregar()

    def _buscar(self, texto):
        self._filtro_busca = texto
        self.recarregar()

    def recarregar(self, filtro=None):
        alertas = self.alert_service.listar_todos(apenas_pendentes=self._apenas_pendentes)
        termo = (self._filtro_busca or "").lower()

        if termo:
            alertas = [
                a for a in alertas
                if termo in (a.titulo or "").lower()
                or termo in (a.tipo or "").lower()
                or termo in str(getattr(a, "_patrimonio_cache", "")).lower()
            ]

        total_pendentes = self.alert_service.contar_pendentes()
        self.lbl_contador.setText(f"{total_pendentes} pendente(s)")

        self.tabela.setRowCount(len(alertas))

        for i, a in enumerate(alertas):
            printer = a.printer or self.printer_service.buscar_por_id(a.printer_id)
            pat = printer.patrimonio if printer else a.printer_id

            self.tabela.setItem(i, 0, self.tabela.item_colorido(pat, "#e2e8f0"))
            cor_tipo = CORES_TIPO.get(a.tipo, "#94949f")
            label_tipo = TIPO_LABELS.get(a.tipo, a.tipo)
            self.tabela.definir_badge(i, 1, label_tipo, cor_tipo)
            self.tabela.setItem(i, 2, QTableWidgetItem(a.titulo or ""))
            self.tabela.setItem(i, 3, QTableWidgetItem((a.descricao or "")[:60] + ("..." if len(a.descricao or "") > 60 else "")))
            self.tabela.setItem(i, 4, QTableWidgetItem(formatar_data_hora(a.data_alerta or a.created_at)))

            label_status, cor_status = STATUS_ALERTA.get(a.resolvido, ("Desconhecido", "#4b5563"))
            self.tabela.definir_badge(i, 5, label_status, cor_status)

        self.tabela.redimensionar()

    def _gerar_alertas_estoque(self):
        from db import safe_commit
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

    def _novo(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Novo Alerta")
        dialog.setFixedSize(500, 380)
        dialog.setStyleSheet(ESTILO_DIALOG)
        layout = QFormLayout(dialog)
        layout.setSpacing(8)

        printer_combo = QComboBox()
        configurar_combo(printer_combo)
        impressoras = self.printer_service.listar_todos()
        printer_combo.addItem("Selecione uma impressora...", None)
        for p in impressoras:
            printer_combo.addItem(f"{p.patrimonio} - {p.modelo}", p.id)
        layout.addRow("Impressora *:", printer_combo)

        tipo_combo = QComboBox()
        configurar_combo(tipo_combo)
        for t in TIPO_OPCOES:
            tipo_combo.addItem(TIPO_LABELS.get(t, t), t)
        layout.addRow("Tipo *:", tipo_combo)

        titulo_input = QLineEdit()
        titulo_input.setPlaceholderText("Título do alerta")
        titulo_input.setStyleSheet(ESTILO_INPUT)
        layout.addRow("Título *:", titulo_input)

        desc_input = QTextEdit()
        desc_input.setPlaceholderText("Descrição detalhada...")
        desc_input.setMaximumHeight(80)
        desc_input.setStyleSheet(ESTILO_INPUT)
        layout.addRow("Descrição:", desc_input)

        layout.addRow("", None)
        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.setStyleSheet(
            "QPushButton { border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }"
            " QPushButton[text='OK'] { background-color: #a78bfa; color: white; }"
            " QPushButton[text='Cancel'] { background-color: #1f2937; color: #94a3b8; }"
        )
        botoes.accepted.connect(lambda: self._salvar_novo(dialog, printer_combo, tipo_combo, titulo_input, desc_input))
        botoes.rejected.connect(dialog.reject)
        layout.addRow(botoes)
        dialog.exec()

    def _salvar_novo(self, dialog, printer_combo, tipo_combo, titulo_input, desc_input):
        printer_id = printer_combo.currentData()
        if not printer_id:
            QMessageBox.warning(dialog, "Aviso", "Selecione uma impressora!")
            return
        titulo = titulo_input.text().strip()
        if not titulo:
            QMessageBox.warning(dialog, "Aviso", "Preencha o título!")
            return

        self.alert_service.criar(
            printer_id=printer_id,
            tipo=tipo_combo.currentData(),
            titulo=titulo,
            descricao=desc_input.toPlainText().strip(),
        )
        ToastManager.atualizar_status(self.alert_service.contar_pendentes())
        ToastManager.sucesso(f"Alerta criado: {titulo}")
        self.recarregar()
        dialog.accept()

    def _detalhes(self, row):
        alertas = self.alert_service.listar_todos(apenas_pendentes=self._apenas_pendentes)
        if row < 0 or row >= len(alertas):
            return
        alerta = alertas[row]
        printer = alerta.printer or self.printer_service.buscar_por_id(alerta.printer_id)
        pat = printer.patrimonio if printer else alerta.printer_id

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Alerta - {alerta.titulo}")
        dialog.setFixedSize(520, 380)
        dialog.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        layout.addWidget(QLabel(f"<b style='color:#a78bfa;font-size:16px'>{alerta.titulo}</b>"))

        info = QVBoxLayout()
        info.setSpacing(6)
        info.addWidget(QLabel(f"<b style='color:#60a5fa'>Impressora:</b>  <span style='color:#e2e8f0'>{pat}</span>"))
        info.addWidget(QLabel(f"<b style='color:#60a5fa'>Tipo:</b>  <span style='color:#e2e8f0'>{TIPO_LABELS.get(alerta.tipo, alerta.tipo)}</span>"))
        info.addWidget(QLabel(f"<b style='color:#60a5fa'>Data:</b>  <span style='color:#e2e8f0'>{formatar_data_hora(alerta.data_alerta or alerta.created_at)}</span>"))
        info.addWidget(QLabel(f"<b style='color:#60a5fa'>Criado em:</b>  <span style='color:#e2e8f0'>{formatar_data_hora(alerta.created_at)}</span>"))
        layout.addLayout(info)

        layout.addWidget(QLabel("<b style='color:#60a5fa'>Descrição:</b>"))
        desc = QTextEdit()
        desc.setPlainText(alerta.descricao or "")
        desc.setReadOnly(True)
        desc.setMaximumHeight(100)
        desc.setStyleSheet(ESTILO_INPUT_READONLY)
        layout.addWidget(desc)

        if alerta.resolvido:
            res = QLabel(f"<b style='color:#34d399'>Resolvido em:</b>  <span style='color:#e2e8f0'>{formatar_data_hora(alerta.resolvido_em)}</span>")
            layout.addWidget(res)

        layout.addStretch()

        botoes = QHBoxLayout()
        botoes.addStretch()

        btn_editar = QPushButton("✏️  Editar")
        btn_editar.setCursor(Qt.PointingHandCursor)
        btn_editar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_editar.clicked.connect(lambda: self._editar(alerta, dialog))
        botoes.addWidget(btn_editar)

        btn_excluir = QPushButton("\U0001f5d1 Excluir")
        btn_excluir.setCursor(Qt.PointingHandCursor)
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_excluir.clicked.connect(lambda: self._excluir(alerta, dialog))
        botoes.addWidget(btn_excluir)

        if not alerta.resolvido:
            btn_resolver = QPushButton("✅  Resolver Alerta")
            btn_resolver.setCursor(Qt.PointingHandCursor)
            btn_resolver.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
            btn_resolver.clicked.connect(lambda: self._resolver(alerta, dialog))
            botoes.addWidget(btn_resolver)

        btn_fechar = QPushButton("🔙  Fechar")
        btn_fechar.setCursor(Qt.PointingHandCursor)
        btn_fechar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_fechar.clicked.connect(dialog.accept)
        botoes.addWidget(btn_fechar)

        layout.addLayout(botoes)
        dialog.exec()

    def _editar(self, alerta, parent_dialog):
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle("Editar Alerta")
        dialog.setFixedSize(500, 420)
        dialog.setStyleSheet(ESTILO_DIALOG)
        layout = QFormLayout(dialog)
        layout.setSpacing(8)

        printer_combo = QComboBox()
        configurar_combo(printer_combo)
        impressoras = self.printer_service.listar_todos()
        printer_combo.addItem("Selecione uma impressora...", None)
        idx_selecionado = 0
        for i, p in enumerate(impressoras):
            printer_combo.addItem(f"{p.patrimonio} - {p.modelo}", p.id)
            if p.id == alerta.printer_id:
                idx_selecionado = i + 1
        printer_combo.setCurrentIndex(idx_selecionado)
        layout.addRow("Impressora *:", printer_combo)

        tipo_combo = QComboBox()
        configurar_combo(tipo_combo)
        for t in TIPO_OPCOES:
            tipo_combo.addItem(TIPO_LABELS.get(t, t), t)
        tipo_combo.setCurrentIndex(TIPO_OPCOES.index(alerta.tipo) if alerta.tipo in TIPO_OPCOES else 0)
        layout.addRow("Tipo *:", tipo_combo)

        titulo_input = QLineEdit()
        titulo_input.setText(alerta.titulo or "")
        titulo_input.setStyleSheet(ESTILO_INPUT)
        layout.addRow("Título *:", titulo_input)

        desc_input = QTextEdit()
        desc_input.setPlainText(alerta.descricao or "")
        desc_input.setMaximumHeight(80)
        desc_input.setStyleSheet(ESTILO_INPUT)
        layout.addRow("Descrição:", desc_input)

        from PySide6.QtWidgets import QCheckBox
        chk_resolvido = QCheckBox("Alerta resolvido")
        chk_resolvido.setChecked(alerta.resolvido)
        chk_resolvido.setStyleSheet(
            "QCheckBox { color: #e2e8f0; font-size: 12px; spacing: 8px; }"
            " QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px;"
            " border: 2px solid #475569; background: transparent; }"
            " QCheckBox::indicator:checked { background-color: #a78bfa; border-color: #a78bfa; }"
        )
        layout.addRow("Status:", chk_resolvido)

        layout.addRow("", None)
        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.setStyleSheet(
            "QPushButton { border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }"
            " QPushButton[text='OK'] { background-color: #a78bfa; color: white; }"
            " QPushButton[text='Cancel'] { background-color: #1f2937; color: #94a3b8; }"
        )
        botoes.accepted.connect(lambda: self._salvar_edicao(dialog, alerta, printer_combo, tipo_combo, titulo_input, desc_input, chk_resolvido, parent_dialog))
        botoes.rejected.connect(dialog.reject)
        layout.addRow(botoes)
        dialog.exec()

    def _salvar_edicao(self, dialog, alerta, printer_combo, tipo_combo, titulo_input, desc_input, chk_resolvido, parent_dialog):
        printer_id = printer_combo.currentData()
        if not printer_id:
            QMessageBox.warning(dialog, "Aviso", "Selecione uma impressora!")
            return
        titulo = titulo_input.text().strip()
        if not titulo:
            QMessageBox.warning(dialog, "Aviso", "Preencha o título!")
            return

        alerta.printer_id = printer_id
        alerta.tipo = tipo_combo.currentData()
        alerta.titulo = titulo
        alerta.descricao = desc_input.toPlainText().strip()
        if chk_resolvido.isChecked() and not alerta.resolvido:
            alerta.resolvido = True
            alerta.resolvido_em = dt.now()
        elif not chk_resolvido.isChecked() and alerta.resolvido:
            alerta.resolvido = False
            alerta.resolvido_em = None
        from db import safe_commit
        safe_commit(self.session)
        ToastManager.atualizar_status(self.alert_service.contar_pendentes())
        ToastManager.info(f"Alerta atualizado: {titulo}")
        self.recarregar()
        dialog.accept()
        parent_dialog.accept()

    def _excluir(self, alerta, dialog):
        resp = QMessageBox.question(
            dialog, "Excluir Alerta",
            f"Deseja realmente excluir o alerta \"{alerta.titulo}\"?\nEsta ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            try:
                self.alert_service.excluir(alerta)
                ToastManager.atualizar_status(self.alert_service.contar_pendentes())
                ToastManager.info(f"Alerta excluído: {alerta.titulo}")
                self.recarregar()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Erro", f"Erro ao excluir alerta:\n{e}")

    def _resolver(self, alerta, dialog):
        resp = QMessageBox.question(
            dialog, "Resolver Alerta",
            "Marcar este alerta como resolvido?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            self.alert_service.resolver(alerta)
            ToastManager.atualizar_status(self.alert_service.contar_pendentes())
            ToastManager.info(f"Alerta resolvido: {alerta.titulo}")
            self.recarregar()
            dialog.accept()
