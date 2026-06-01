from datetime import datetime as dt

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.models import Activity, Printer, User
from app.views.styles.theme import (
    ESTILO_BOTAO_SECUNDARIO,
    ESTILO_BOTAO_SUCESSO,
    ESTILO_LABEL_VALOR,
    ESTILO_TABELA_SIMPLES,
    ESTILO_TITULO_PAGINA,
    STATUS_ATIVIDADE_OPCOES,
    configurar_combo,
    estilos_dialogo_tabs,
)
from app.utils.helpers import formatar_data_hora


class _StatsCard(QFrame):
    def __init__(self, titulo, valor, cor):
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

    def set_valor(self, valor):
        self.lbl_valor.setText(str(valor))


class TechnicianHistoryPage(QWidget):
    def __init__(self, session, technician_service, activity_service, user_service, login_history_service,
                 printer_service, parent=None):
        super().__init__(parent)
        self._session = session
        self._technician_service = technician_service
        self._activity_service = activity_service
        self._user_service = user_service
        self._login_history_service = login_history_service
        self._printer_service = printer_service
        self._current_tech_id = None
        self._init_ui()

    def _init_ui(self):
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
        self._status_combo.currentIndexChanged.connect(self._aplicar_filtros)
        filtros.addWidget(self._status_combo)

        lbl_tipo = QLabel("Tipo:")
        lbl_tipo.setStyleSheet("color: #94949f; font-size: 13px; font-weight: 500; background: transparent;")
        filtros.addWidget(lbl_tipo)

        self._tipo_combo = QComboBox()
        configurar_combo(self._tipo_combo)
        self._tipo_combo.addItems(["Todos", "MANUTENCAO", "MOVIMENTACAO"])
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
        self._card_andamento = _StatsCard("Em Andamento", 0, "#f97316")
        self._card_concluidas = _StatsCard("Concluídas", 0, "#10b981")
        self._card_mov = _StatsCard("Movimentações", 0, "#3b82f6")
        cards.addWidget(self._card_total)
        cards.addWidget(self._card_andamento)
        cards.addWidget(self._card_concluidas)
        cards.addWidget(self._card_mov)
        layout.addLayout(cards)

        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(estilos_dialogo_tabs())
        layout.addWidget(self._tabs, 1)

        self._tab_atividades = self._criar_tabela_atividades()
        self._tabs.addTab(self._tab_atividades, "\u2699\ufe0f Atividades")

        self._tab_andamento = self._criar_tabela_andamento()
        self._tabs.addTab(self._tab_andamento, "\u23f3 Em Andamento")

        self._tab_mov = self._criar_tabela_movimentacoes()
        self._tabs.addTab(self._tab_mov, "\U0001f69a Movimentações")

        self._tab_login = self._criar_tabela_login()
        self._tabs.addTab(self._tab_login, "\U0001f511 Sessões")

    def _criar_tabela_atividades(self):
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
        h = self._tabela_atividades.horizontalHeader()
        for i in range(8):
            h.setSectionResizeMode(i, QHeaderView.Stretch)
        layout.addWidget(self._tabela_atividades)
        return tab

    def _criar_tabela_andamento(self):
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
        h = self._tabela_andamento.horizontalHeader()
        for i in range(7):
            h.setSectionResizeMode(i, QHeaderView.Stretch)
        layout.addWidget(self._tabela_andamento)
        return tab

    def _criar_tabela_movimentacoes(self):
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
        h = self._tabela_mov.horizontalHeader()
        for i in range(7):
            h.setSectionResizeMode(i, QHeaderView.Stretch)
        layout.addWidget(self._tabela_mov)
        return tab

    def _criar_tabela_login(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        lbl = QLabel(
            "Sessões de login dos usuários do sistema. "
            "Relaciona técnicos a usuários pelo nome."
        )
        lbl.setStyleSheet("color: #94949f; font-size: 12px; background: transparent;")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
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
        h = self._tabela_login.horizontalHeader()
        for i in range(5):
            h.setSectionResizeMode(i, QHeaderView.Stretch)
        layout.addWidget(self._tabela_login)
        return tab

    def recarregar(self):
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

    def _ao_trocar_tecnico(self):
        self._current_tech_id = self._tecnico_combo.currentData()
        if self._current_tech_id is None:
            self._limpar_tabelas()
            return
        self._atualizar_stats()
        self._aplicar_filtros()

    def _aplicar_filtros(self):
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

    def _atualizar_stats(self):
        tech_id = self._current_tech_id
        if tech_id is None:
            for card in [self._card_total, self._card_andamento, self._card_concluidas, self._card_mov]:
                card.set_valor(0)
            return

        total = self._activity_service.contar_por_tecnico(tech_id)
        andamento = self._activity_service.contar_por_tecnico_por_status(tech_id, "Em Andamento")
        concluidas = self._activity_service.contar_por_tecnico_por_status(tech_id, "Concluida")
        mov = len(self._activity_service.listar_por_tecnico_e_tipo(tech_id, "MOVIMENTACAO"))

        self._card_total.set_valor(total)
        self._card_andamento.set_valor(andamento)
        self._card_concluidas.set_valor(concluidas)
        self._card_mov.set_valor(mov)

    def _preencher_atividades(self, atividades):
        self._tabela_atividades.setRowCount(0)
        self._tabela_atividades.setRowCount(len(atividades))
        for i, a in enumerate(atividades):
            printer = self._printer_service.buscar_por_id(a.printer_id)
            pat = printer.patrimonio if printer else a.printer_id
            self._tabela_atividades.setItem(i, 0, QTableWidgetItem(formatar_data_hora(a.event_at)))
            self._tabela_atividades.setItem(i, 1, QTableWidgetItem(pat))
            self._tabela_atividades.setItem(i, 2, QTableWidgetItem(a.kind))
            self._tabela_atividades.setItem(i, 3, QTableWidgetItem((a.notes or "")[:60]))
            self._tabela_atividades.setItem(i, 4, QTableWidgetItem(a.parts_used or ""))
            od = f"{a.from_location} \u2192 {a.to_location}" if a.from_location or a.to_location else "-"
            self._tabela_atividades.setItem(i, 5, QTableWidgetItem(od))
            self._tabela_atividades.setItem(i, 6, QTableWidgetItem(a.status_atividade or ""))
            self._tabela_atividades.setItem(i, 7, QTableWidgetItem(a.numero_recibo or ""))

    def _preencher_andamento(self, tech_id):
        atividades = self._activity_service.listar_por_tecnico_e_status(tech_id, "Em Andamento")
        self._tabela_andamento.setRowCount(0)
        self._tabela_andamento.setRowCount(len(atividades))
        for i, a in enumerate(atividades):
            printer = self._printer_service.buscar_por_id(a.printer_id)
            pat = printer.patrimonio if printer else a.printer_id
            modelo = printer.modelo if printer else ""
            self._tabela_andamento.setItem(i, 0, QTableWidgetItem(formatar_data_hora(a.event_at)))
            self._tabela_andamento.setItem(i, 1, QTableWidgetItem(pat))
            self._tabela_andamento.setItem(i, 2, QTableWidgetItem(modelo))
            self._tabela_andamento.setItem(i, 3, QTableWidgetItem((a.notes or "")[:60]))
            self._tabela_andamento.setItem(i, 4, QTableWidgetItem(a.parts_used or ""))
            local = a.from_location or printer.local_atual or "-"
            self._tabela_andamento.setItem(i, 5, QTableWidgetItem(local))
            self._tabela_andamento.setItem(i, 6, QTableWidgetItem(a.numero_recibo or ""))

    def _preencher_movimentacoes(self, tech_id):
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

    def _preencher_login(self, tech_id):
        tecnico = self._technician_service.buscar_por_id(tech_id)
        if not tecnico:
            self._tabela_login.setRowCount(0)
            return

        usuarios = self._user_service.listar_todos()
        user_match = None
        for u in usuarios:
            if tecnico.nome_completo.lower() in u.nome.lower() or \
               (tecnico.nome_exibicao and tecnico.nome_exibicao.lower() in u.nome.lower()):
                user_match = u
                break

        if not user_match:
            self._tabela_login.setRowCount(0)
            lbl_empty = QLabel(
                "Nenhum usuário do sistema corresponde a este técnico. "
                "Associe pelo nome completo ou nome de exibição."
            )
            lbl_empty.setStyleSheet("color: #717182; font-size: 12px; background: transparent;")
            self._tabela_login.setRowCount(1)
            self._tabela_login.setSpan(0, 0, 1, 5)
            self._tabela_login.setCellWidget(0, 0, lbl_empty)
            return

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
                diff = dt.utcnow() - s.login_at
                horas = int(diff.total_seconds() // 3600)
                minutos = int((diff.total_seconds() % 3600) // 60)
                duracao = f"{horas}h {minutos}min (em andamento)"
            self._tabela_login.setItem(i, 4, QTableWidgetItem(duracao))

    def _limpar_tabelas(self):
        self._tabela_atividades.setRowCount(0)
        self._tabela_andamento.setRowCount(0)
        self._tabela_mov.setRowCount(0)
        self._tabela_login.setRowCount(0)
        for card in [self._card_total, self._card_andamento, self._card_concluidas, self._card_mov]:
            card.set_valor(0)
