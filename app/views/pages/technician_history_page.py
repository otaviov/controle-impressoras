from __future__ import annotations

from app.models.base import utcnow
from datetime import datetime as dt
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.models import Activity, Printer, User
from app.views.styles.theme import (
    ATIVIDADE_CORES,
    ESTILO_BOTAO_SECUNDARIO,
    ESTILO_BOTAO_SUCESSO,
    ESTILO_INPUT,
    ESTILO_LABEL_VALOR,
    ESTILO_TABELA_SIMPLES,
    ESTILO_TITULO_PAGINA,
    STATUS_ATIVIDADE_OPCOES,
    TIPO_ATIVIDADE_CORES,
    configurar_combo,
    configurar_combo_colorido,
)
from app.utils.helpers import formatar_data_hora
from app.views.widgets.table_widget import tornar_interativa


class _StatsCard(QFrame):
    lbl_valor: QLabel

    def __init__(self, titulo: str, valor: int, cor: str) -> None:
        super().__init__()
        self.setStyleSheet(
            f"QFrame {{ background-color: #14141f; border: 1px solid #2a2a3e;"
            f" border-radius: 12px; padding: 16px; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("color: #717182; font-size: 11px; font-weight: 600; background: transparent;")
        self.lbl_valor = QLabel(str(valor))
        self.lbl_valor.setStyleSheet(
            f"color: {cor}; font-size: 26px; font-weight: 700; background: transparent; letter-spacing: -0.5px;"
        )
        layout.addWidget(lbl_titulo)
        layout.addWidget(self.lbl_valor)

    def set_valor(self, valor: int) -> None:
        self.lbl_valor.setText(str(valor))


class TechnicianHistoryPage(QWidget):
    abrir_os = Signal(int)
    _session: Any
    _technician_service: Any
    _activity_service: Any
    _user_service: Any
    _login_history_service: Any
    _printer_service: Any
    _current_tech_id: Any | None
    _tecnico_combo: QComboBox
    _status_combo: QComboBox
    _tipo_combo: QComboBox
    _card_total: _StatsCard
    _card_andamento: _StatsCard
    _card_concluidas: _StatsCard
    _card_mov: _StatsCard
    _tabs: QTabWidget
    _tab_atividades: QWidget
    _tab_andamento: QWidget
    _tab_mov: QWidget
    _tab_login: QWidget
    _tabela_atividades: QTableWidget
    _tabela_andamento: QTableWidget
    _tabela_mov: QTableWidget
    _tabela_login: QTableWidget
    _assoc_label: QLabel
    _assoc_combo: QComboBox
    _assoc_btn: QPushButton
    _tab_os_abertas: QWidget
    _tab_pecas: QWidget
    _tabela_os_abertas: QTableWidget
    _tabela_pecas: QTableWidget
    _peca_search_input: QLineEdit
    _tabela_quem_usou: QTableWidget

    def __init__(self, session: Any, technician_service: Any, activity_service: Any, user_service: Any, login_history_service: Any,
                 printer_service: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session = session
        self._technician_service = technician_service
        self._activity_service = activity_service
        self._user_service = user_service
        self._login_history_service = login_history_service
        self._printer_service = printer_service
        self._current_tech_id = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        titulo = QLabel("\U0001f4dc Histórico de Técnicos")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        header.addWidget(titulo)
        header.addStretch()
        layout.addLayout(header)

        filtros = QHBoxLayout()
        filtros.setSpacing(10)

        lbl_tec = QLabel("Técnico:")
        lbl_tec.setStyleSheet("color: #94949f; font-size: 13px; font-weight: 500; background: transparent;")
        filtros.addWidget(lbl_tec)

        self._tecnico_combo = QComboBox()
        configurar_combo(self._tecnico_combo)
        self._tecnico_combo.setMinimumWidth(260)
        self._tecnico_combo.currentIndexChanged.connect(self._ao_trocar_tecnico)
        filtros.addWidget(self._tecnico_combo)

        lbl_status = QLabel("Status:")
        lbl_status.setStyleSheet("color: #94949f; font-size: 13px; font-weight: 500; background: transparent;")
        filtros.addWidget(lbl_status)

        self._status_combo = QComboBox()
        configurar_combo(self._status_combo)
        self._status_combo.addItems(["Todos"] + STATUS_ATIVIDADE_OPCOES)
        configurar_combo_colorido(self._status_combo, ATIVIDADE_CORES)
        self._status_combo.currentIndexChanged.connect(self._aplicar_filtros)
        filtros.addWidget(self._status_combo)

        lbl_tipo = QLabel("Tipo:")
        lbl_tipo.setStyleSheet("color: #94949f; font-size: 13px; font-weight: 500; background: transparent;")
        filtros.addWidget(lbl_tipo)

        self._tipo_combo = QComboBox()
        configurar_combo(self._tipo_combo)
        self._tipo_combo.addItems(["Todos", "MANUTENCAO", "MOVIMENTACAO"])
        configurar_combo_colorido(self._tipo_combo, TIPO_ATIVIDADE_CORES)
        self._tipo_combo.currentIndexChanged.connect(self._aplicar_filtros)
        filtros.addWidget(self._tipo_combo)

        btn_atualizar = QPushButton("\u21bb Atualizar")
        btn_atualizar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_atualizar.clicked.connect(self.recarregar)
        filtros.addStretch()
        filtros.addWidget(btn_atualizar)

        layout.addLayout(filtros)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self._card_total = _StatsCard("Total de OS", 0, "#6366f1")
        self._card_andamento = _StatsCard("Em Atendimento", 0, "#6366f1")
        self._card_concluidas = _StatsCard("Concluídas", 0, "#10b981")
        self._card_mov = _StatsCard("Movimentações", 0, "#3b82f6")
        cards.addWidget(self._card_total)
        cards.addWidget(self._card_andamento)
        cards.addWidget(self._card_concluidas)
        cards.addWidget(self._card_mov)
        layout.addLayout(cards)

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs, 1)

        self._tab_atividades = self._criar_tabela_atividades()
        self._tabs.addTab(self._tab_atividades, "\u2699\ufe0f Atividades")

        self._tab_andamento = self._criar_tabela_andamento()
        self._tabs.addTab(self._tab_andamento, "\u23f3 Em Andamento")

        self._tab_mov = self._criar_tabela_movimentacoes()
        self._tabs.addTab(self._tab_mov, "\U0001f69a Movimentações")

        self._tab_login = self._criar_tabela_login()
        self._tabs.addTab(self._tab_login, "\U0001f511 Sessões")

        self._tab_os_abertas = self._criar_tabela_os_abertas()
        self._tabs.addTab(self._tab_os_abertas, "\U0001f4cc OS Abertas")

        self._tab_pecas = self._criar_tabela_pecas()
        self._tabs.addTab(self._tab_pecas, "\U0001f527 Peças")

        self._tabela_atividades.cellDoubleClicked.connect(lambda r, c: self._ao_duplo_clicar_os(r, self._tabela_atividades))
        self._tabela_andamento.cellDoubleClicked.connect(lambda r, c: self._ao_duplo_clicar_os(r, self._tabela_andamento))
        self._tabela_os_abertas.cellDoubleClicked.connect(lambda r, c: self._ao_duplo_clicar_os(r, self._tabela_os_abertas))

    def _criar_tabela_atividades(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self._tabela_atividades = QTableWidget()
        self._tabela_atividades.setColumnCount(8)
        self._tabela_atividades.setHorizontalHeaderLabels(
            ["Data/Hora", "Patrimônio", "Tipo", "Descrição", "Peças", "Origem/Destino", "Status", "Recibo"]
        )
        self._tabela_atividades.setStyleSheet(ESTILO_TABELA_SIMPLES)
        self._tabela_atividades.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabela_atividades.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabela_atividades.verticalHeader().setVisible(False)
        self._tabela_atividades.setAlternatingRowColors(True)
        self._tabela_atividades.verticalHeader().setDefaultSectionSize(40)
        tornar_interativa(self._tabela_atividades)
        layout.addWidget(self._tabela_atividades)
        return tab

    def _criar_tabela_andamento(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        lbl = QLabel("Máquinas sendo consertadas agora pelo técnico selecionado:")
        lbl.setStyleSheet("color: #94949f; font-size: 12px; background: transparent;")
        layout.addWidget(lbl)
        self._tabela_andamento = QTableWidget()
        self._tabela_andamento.setColumnCount(7)
        self._tabela_andamento.setHorizontalHeaderLabels(
            ["Data/Hora", "Patrimônio", "Modelo", "Descrição", "Peças", "Local", "Recibo"]
        )
        self._tabela_andamento.setStyleSheet(ESTILO_TABELA_SIMPLES)
        self._tabela_andamento.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabela_andamento.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabela_andamento.verticalHeader().setVisible(False)
        self._tabela_andamento.setAlternatingRowColors(True)
        self._tabela_andamento.verticalHeader().setDefaultSectionSize(40)
        tornar_interativa(self._tabela_andamento)
        layout.addWidget(self._tabela_andamento)
        return tab

    def _criar_tabela_movimentacoes(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self._tabela_mov = QTableWidget()
        self._tabela_mov.setColumnCount(7)
        self._tabela_mov.setHorizontalHeaderLabels(
            ["Data/Hora", "Patrimônio", "Peças", "Origem", "Destino", "Status", "Recibo"]
        )
        self._tabela_mov.setStyleSheet(ESTILO_TABELA_SIMPLES)
        self._tabela_mov.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabela_mov.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabela_mov.verticalHeader().setVisible(False)
        self._tabela_mov.setAlternatingRowColors(True)
        self._tabela_mov.verticalHeader().setDefaultSectionSize(40)
        tornar_interativa(self._tabela_mov)
        layout.addWidget(self._tabela_mov)
        return tab

    def _criar_tabela_login(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        assoc_frame = QFrame()
        assoc_frame.setStyleSheet(
            "QFrame { background-color: #14141f; border: 1px solid #2a2a3e;"
            " border-radius: 8px; padding: 8px; }"
        )
        assoc_layout = QHBoxLayout(assoc_frame)
        assoc_layout.setContentsMargins(12, 8, 12, 8)
        assoc_layout.setSpacing(8)

        assoc_label = QLabel("Usuário associado:")
        assoc_label.setStyleSheet("color: #94949f; font-size: 12px; font-weight: 600; background: transparent;")
        assoc_layout.addWidget(assoc_label)

        self._assoc_label = QLabel("—")
        self._assoc_label.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 600; background: transparent;")
        assoc_layout.addWidget(self._assoc_label)

        assoc_layout.addSpacing(12)

        self._assoc_combo = QComboBox()
        configurar_combo(self._assoc_combo)
        self._assoc_combo.setMinimumWidth(200)
        assoc_layout.addWidget(self._assoc_combo)

        self._assoc_btn = QPushButton("Salvar Associação")
        self._assoc_btn.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        self._assoc_btn.clicked.connect(self._salvar_associacao)
        assoc_layout.addWidget(self._assoc_btn)

        assoc_layout.addStretch()
        layout.addWidget(assoc_frame)

        self._tabela_login = QTableWidget()
        self._tabela_login.setColumnCount(5)
        self._tabela_login.setHorizontalHeaderLabels(
            ["Usuário", "Perfil", "Login", "Logout", "Duração"]
        )
        self._tabela_login.setStyleSheet(ESTILO_TABELA_SIMPLES)
        self._tabela_login.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabela_login.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabela_login.verticalHeader().setVisible(False)
        self._tabela_login.setAlternatingRowColors(True)
        self._tabela_login.verticalHeader().setDefaultSectionSize(40)
        tornar_interativa(self._tabela_login)
        layout.addWidget(self._tabela_login)
        return tab

    def _criar_tabela_os_abertas(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        lbl = QLabel("Ordens de serviço em aberto (não concluídas) para este técnico:")
        lbl.setStyleSheet("color: #94949f; font-size: 12px; background: transparent;")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        self._tabela_os_abertas = QTableWidget()
        self._tabela_os_abertas.setColumnCount(7)
        self._tabela_os_abertas.setHorizontalHeaderLabels(
            ["Data/Hora", "Patrimônio", "Local", "Status", "Descrição", "Urgência", "Recibo"]
        )
        self._tabela_os_abertas.setStyleSheet(ESTILO_TABELA_SIMPLES)
        self._tabela_os_abertas.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabela_os_abertas.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabela_os_abertas.verticalHeader().setVisible(False)
        self._tabela_os_abertas.setAlternatingRowColors(True)
        self._tabela_os_abertas.verticalHeader().setDefaultSectionSize(40)
        tornar_interativa(self._tabela_os_abertas)
        layout.addWidget(self._tabela_os_abertas)
        return tab

    def _criar_tabela_pecas(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        lbl = QLabel("Peças mais usadas por este técnico:")
        lbl.setStyleSheet("color: #94949f; font-size: 12px; background: transparent;")
        layout.addWidget(lbl)

        self._tabela_pecas = QTableWidget()
        self._tabela_pecas.setColumnCount(2)
        self._tabela_pecas.setHorizontalHeaderLabels(["Peça", "Vezes Usada"])
        self._tabela_pecas.setStyleSheet(ESTILO_TABELA_SIMPLES)
        self._tabela_pecas.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabela_pecas.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabela_pecas.verticalHeader().setVisible(False)
        self._tabela_pecas.setAlternatingRowColors(True)
        self._tabela_pecas.verticalHeader().setDefaultSectionSize(36)
        tornar_interativa(self._tabela_pecas)
        self._tabela_pecas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        layout.addWidget(self._tabela_pecas)

        layout.addSpacing(12)

        search_frame = QFrame()
        search_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)

        search_lbl = QLabel("Quem usou esta peça:")
        search_lbl.setStyleSheet("color: #94949f; font-size: 12px; font-weight: 600; background: transparent;")
        search_layout.addWidget(search_lbl)

        self._peca_search_input = QLineEdit()
        self._peca_search_input.setStyleSheet(ESTILO_INPUT)
        self._peca_search_input.setPlaceholderText("Digite o nome da peça...")
        search_layout.addWidget(self._peca_search_input)

        btn_search = QPushButton("Buscar")
        btn_search.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_search.clicked.connect(self._buscar_quem_usou_peca)
        search_layout.addWidget(btn_search)
        search_layout.addStretch()
        layout.addWidget(search_frame)

        self._tabela_quem_usou = QTableWidget()
        self._tabela_quem_usou.setColumnCount(5)
        self._tabela_quem_usou.setHorizontalHeaderLabels(
            ["Técnico", "Data/Hora", "Patrimônio", "Peças", "Descrição"]
        )
        self._tabela_quem_usou.setStyleSheet(ESTILO_TABELA_SIMPLES)
        self._tabela_quem_usou.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabela_quem_usou.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabela_quem_usou.verticalHeader().setVisible(False)
        self._tabela_quem_usou.setAlternatingRowColors(True)
        self._tabela_quem_usou.verticalHeader().setDefaultSectionSize(40)
        tornar_interativa(self._tabela_quem_usou)
        layout.addWidget(self._tabela_quem_usou)
        return tab

    def recarregar(self) -> None:
        tecnicos = self._technician_service.listar_todos()
        current_text = self._tecnico_combo.currentText()

        self._tecnico_combo.blockSignals(True)
        self._tecnico_combo.clear()
        self._tecnico_combo.addItem("-- Selecione um técnico --", None)
        for t in tecnicos:
            display = t.nome_exibicao or t.nome_completo
            self._tecnico_combo.addItem(display, t.id)

        if current_text:
            idx = self._tecnico_combo.findText(current_text)
            if idx >= 0:
                self._tecnico_combo.setCurrentIndex(idx)
        self._tecnico_combo.blockSignals(False)

        if self._tecnico_combo.currentData() is not None:
            self._ao_trocar_tecnico()

    def _ao_trocar_tecnico(self) -> None:
        self._current_tech_id = self._tecnico_combo.currentData()
        if self._current_tech_id is None:
            self._limpar_tabelas()
            return
        self._atualizar_stats()
        self._aplicar_filtros()

    def _aplicar_filtros(self) -> None:
        tech_id = self._current_tech_id
        if tech_id is None:
            return

        status = self._status_combo.currentText()
        tipo = self._tipo_combo.currentText()

        if status == "Todos":
            atividades = self._activity_service.listar_por_tecnico(tech_id)
        else:
            atividades = self._activity_service.listar_por_tecnico_e_status(tech_id, status)

        if tipo != "Todos":
            atividades = [a for a in atividades if a.kind == tipo]

        self._preencher_atividades(atividades)
        self._preencher_andamento(tech_id)
        self._preencher_movimentacoes(tech_id)
        self._preencher_login(tech_id)
        self._preencher_os_abertas(tech_id)
        self._preencher_pecas(tech_id)

    def _atualizar_stats(self) -> None:
        tech_id = self._current_tech_id
        if tech_id is None:
            for card in [self._card_total, self._card_andamento, self._card_concluidas, self._card_mov]:
                card.set_valor(0)
            return

        total = self._activity_service.contar_por_tecnico(tech_id)
        andamento = self._activity_service.contar_por_tecnico_por_status(tech_id, "Em Atendimento")
        concluidas = self._activity_service.contar_por_tecnico_por_status(tech_id, "Concluido")
        mov = len(self._activity_service.listar_por_tecnico_e_tipo(tech_id, "MOVIMENTACAO"))

        self._card_total.set_valor(total)
        self._card_andamento.set_valor(andamento)
        self._card_concluidas.set_valor(concluidas)
        self._card_mov.set_valor(mov)

    def _preencher_atividades(self, atividades: list[Any]) -> None:
        self._tabela_atividades.setRowCount(0)
        self._tabela_atividades.setRowCount(len(atividades))
        for i, a in enumerate(atividades):
            printer = self._printer_service.buscar_por_id(a.printer_id)
            pat = printer.patrimonio if printer else a.printer_id
            item0 = QTableWidgetItem(formatar_data_hora(a.event_at))
            item0.setData(Qt.UserRole, a.id)
            self._tabela_atividades.setItem(i, 0, item0)
            self._tabela_atividades.setItem(i, 1, QTableWidgetItem(pat))
            self._tabela_atividades.setItem(i, 2, QTableWidgetItem(a.kind))
            self._tabela_atividades.setItem(i, 3, QTableWidgetItem((a.notes or "")[:60]))
            self._tabela_atividades.setItem(i, 4, QTableWidgetItem(a.parts_used or ""))
            od = f"{a.from_location} \u2192 {a.to_location}" if a.from_location or a.to_location else "-"
            self._tabela_atividades.setItem(i, 5, QTableWidgetItem(od))
            self._tabela_atividades.setItem(i, 6, QTableWidgetItem(a.status_atividade or ""))
            self._tabela_atividades.setItem(i, 7, QTableWidgetItem(a.numero_recibo or ""))

    def _preencher_andamento(self, tech_id: int) -> None:
        atividades = self._activity_service.listar_por_tecnico_e_status(tech_id, "Em Atendimento")
        self._tabela_andamento.setRowCount(0)
        self._tabela_andamento.setRowCount(len(atividades))
        for i, a in enumerate(atividades):
            printer = self._printer_service.buscar_por_id(a.printer_id)
            pat = printer.patrimonio if printer else a.printer_id
            modelo = printer.modelo if printer else ""
            item0 = QTableWidgetItem(formatar_data_hora(a.event_at))
            item0.setData(Qt.UserRole, a.id)
            self._tabela_andamento.setItem(i, 0, item0)
            self._tabela_andamento.setItem(i, 1, QTableWidgetItem(pat))
            self._tabela_andamento.setItem(i, 2, QTableWidgetItem(modelo))
            self._tabela_andamento.setItem(i, 3, QTableWidgetItem((a.notes or "")[:60]))
            self._tabela_andamento.setItem(i, 4, QTableWidgetItem(a.parts_used or ""))
            local = a.from_location or printer.local_atual or "-"
            self._tabela_andamento.setItem(i, 5, QTableWidgetItem(local))
            self._tabela_andamento.setItem(i, 6, QTableWidgetItem(a.numero_recibo or ""))

    def _preencher_movimentacoes(self, tech_id: int) -> None:
        atividades = self._activity_service.listar_por_tecnico_e_tipo(tech_id, "MOVIMENTACAO")
        self._tabela_mov.setRowCount(0)
        self._tabela_mov.setRowCount(len(atividades))
        for i, a in enumerate(atividades):
            printer = self._printer_service.buscar_por_id(a.printer_id)
            pat = printer.patrimonio if printer else a.printer_id
            self._tabela_mov.setItem(i, 0, QTableWidgetItem(formatar_data_hora(a.event_at)))
            self._tabela_mov.setItem(i, 1, QTableWidgetItem(pat))
            self._tabela_mov.setItem(i, 2, QTableWidgetItem(a.parts_used or ""))
            self._tabela_mov.setItem(i, 3, QTableWidgetItem(a.from_location or "-"))
            self._tabela_mov.setItem(i, 4, QTableWidgetItem(a.to_location or "-"))
            self._tabela_mov.setItem(i, 5, QTableWidgetItem(a.status_atividade or ""))
            self._tabela_mov.setItem(i, 6, QTableWidgetItem(a.numero_recibo or ""))

    def _preencher_login(self, tech_id: int) -> None:
        tecnico = self._technician_service.buscar_por_id(tech_id)
        if not tecnico:
            self._tabela_login.setRowCount(0)
            self._assoc_label.setText("—")
            self._assoc_combo.clear()
            return

        usuarios = self._user_service.listar_todos()
        self._assoc_combo.blockSignals(True)
        self._assoc_combo.clear()
        self._assoc_combo.addItem("-- Nenhum --", None)
        for u in usuarios:
            self._assoc_combo.addItem(f"{u.nome} ({u.perfil})", u.id)
        self._assoc_combo.blockSignals(False)

        user_match = None
        if tecnico.user_id is not None:
            for u in usuarios:
                if u.id == tecnico.user_id:
                    user_match = u
                    break
            if user_match is None:
                tecnico.user_id = None

        if user_match is None:
            for u in usuarios:
                if tecnico.nome_completo.lower() in u.nome.lower() or \
                   (tecnico.nome_exibicao and tecnico.nome_exibicao.lower() in u.nome.lower()):
                    user_match = u
                    self._technician_service.associar_usuario(tech_id, u.id)
                    break

        if user_match is None:
            self._tabela_login.setRowCount(0)
            self._tabela_login.setRowCount(1)
            self._tabela_login.setSpan(0, 0, 1, 5)
            lbl_empty = QLabel(
                "Nenhuma sessão — associe um usuário do sistema acima."
            )
            lbl_empty.setStyleSheet("color: #717182; font-size: 12px; background: transparent;")
            lbl_empty.setAlignment(Qt.AlignCenter)
            self._tabela_login.setCellWidget(0, 0, lbl_empty)
            self._assoc_label.setStyleSheet("color: #ef4444; font-size: 12px; font-weight: 600; background: transparent;")
            self._assoc_label.setText("Nenhum")
            self._assoc_combo.setCurrentIndex(0)
            return

        for i in range(self._assoc_combo.count()):
            if self._assoc_combo.itemData(i) == user_match.id:
                self._assoc_combo.setCurrentIndex(i)
                break

        self._assoc_label.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 600; background: transparent;")
        self._assoc_label.setText(user_match.nome)

        sessoes = self._login_history_service.listar_por_usuario(user_match.id)
        self._tabela_login.setRowCount(0)
        self._tabela_login.setRowCount(len(sessoes))
        for i, s in enumerate(sessoes):
            self._tabela_login.setItem(i, 0, QTableWidgetItem(user_match.nome))
            self._tabela_login.setItem(i, 1, QTableWidgetItem(user_match.perfil.capitalize()))
            self._tabela_login.setItem(i, 2, QTableWidgetItem(formatar_data_hora(s.login_at)))
            logout = formatar_data_hora(s.logout_at) if s.logout_at else "Em sessão"
            self._tabela_login.setItem(i, 3, QTableWidgetItem(logout))
            if s.logout_at:
                diff = s.logout_at - s.login_at
                horas = int(diff.total_seconds() // 3600)
                minutos = int((diff.total_seconds() % 3600) // 60)
                duracao = f"{horas}h {minutos}min"
            else:
                diff = utcnow() - s.login_at
                horas = int(diff.total_seconds() // 3600)
                minutos = int((diff.total_seconds() % 3600) // 60)
                duracao = f"{horas}h {minutos}min (em andamento)"
            self._tabela_login.setItem(i, 4, QTableWidgetItem(duracao))

    def _preencher_os_abertas(self, tech_id: int) -> None:
        atividades = self._activity_service.listar_os_abertas_por_tecnico(tech_id)
        self._tabela_os_abertas.setRowCount(0)
        self._tabela_os_abertas.setRowCount(len(atividades))
        for i, a in enumerate(atividades):
            printer = self._printer_service.buscar_por_id(a.printer_id)
            pat = printer.patrimonio if printer else a.printer_id
            item0 = QTableWidgetItem(formatar_data_hora(a.event_at))
            item0.setData(Qt.UserRole, a.id)
            self._tabela_os_abertas.setItem(i, 0, item0)
            self._tabela_os_abertas.setItem(i, 1, QTableWidgetItem(pat))
            self._tabela_os_abertas.setItem(i, 2, QTableWidgetItem(a.from_location or ""))
            self._tabela_os_abertas.setItem(i, 3, QTableWidgetItem(a.status_atividade or ""))
            self._tabela_os_abertas.setItem(i, 4, QTableWidgetItem((a.notes or "")[:60]))
            self._tabela_os_abertas.setItem(i, 5, QTableWidgetItem(a.urgencia or ""))
            self._tabela_os_abertas.setItem(i, 6, QTableWidgetItem(a.numero_recibo or ""))

    def _preencher_pecas(self, tech_id: int) -> None:
        pecas = self._activity_service.listar_pecas_por_tecnico(tech_id)
        self._tabela_pecas.setRowCount(0)
        self._tabela_pecas.setRowCount(len(pecas))
        for i, (nome, qtd) in enumerate(pecas):
            self._tabela_pecas.setItem(i, 0, QTableWidgetItem(nome))
            item = QTableWidgetItem(str(qtd))
            item.setTextAlignment(Qt.AlignCenter)
            self._tabela_pecas.setItem(i, 1, item)

    def _buscar_quem_usou_peca(self) -> None:
        nome = self._peca_search_input.text().strip()
        if not nome:
            return
        resultados = self._activity_service.listar_tecnicos_por_peca(nome)
        self._tabela_quem_usou.setRowCount(0)
        self._tabela_quem_usou.setRowCount(len(resultados))
        for i, a in enumerate(resultados):
            printer = self._printer_service.buscar_por_id(a.printer_id)
            pat = printer.patrimonio if printer else a.printer_id
            tech_nome = a.technician.nome_exibicao or a.technician.nome_completo if a.technician else "—"
            self._tabela_quem_usou.setItem(i, 0, QTableWidgetItem(tech_nome))
            self._tabela_quem_usou.setItem(i, 1, QTableWidgetItem(formatar_data_hora(a.event_at)))
            self._tabela_quem_usou.setItem(i, 2, QTableWidgetItem(pat))
            self._tabela_quem_usou.setItem(i, 3, QTableWidgetItem(a.parts_used or ""))
            self._tabela_quem_usou.setItem(i, 4, QTableWidgetItem((a.notes or "")[:80]))

    def _salvar_associacao(self) -> None:
        tech_id = self._current_tech_id
        if tech_id is None:
            return
        user_id = self._assoc_combo.currentData()
        self._technician_service.associar_usuario(tech_id, user_id)
        self._preencher_login(tech_id)

    def _ao_duplo_clicar_os(self, row: int, tabela: QTableWidget) -> None:
        item = tabela.item(row, 0)
        if item is None:
            return
        activity_id = item.data(Qt.UserRole)
        if activity_id is not None:
            self.abrir_os.emit(activity_id)

    def _limpar_tabelas(self) -> None:
        self._tabela_atividades.setRowCount(0)
        self._tabela_andamento.setRowCount(0)
        self._tabela_mov.setRowCount(0)
        self._tabela_login.setRowCount(0)
        self._tabela_os_abertas.setRowCount(0)
        self._tabela_pecas.setRowCount(0)
        self._tabela_quem_usou.setRowCount(0)
        for card in [self._card_total, self._card_andamento, self._card_concluidas, self._card_mov]:
            card.set_valor(0)
