from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime as dt, timedelta
from typing import Any

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
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

from app.views.styles.theme import (
    ESTILO_BOTAO_SECUNDARIO,
    ESTILO_BOTAO_SUCESSO,
    ESTILO_TABELA_SIMPLES,
    ESTILO_TITULO_PAGINA,
    configurar_combo,
)


class _StatsCard(QFrame):
    lbl_valor: QLabel

    def __init__(self, titulo: str, valor: str, cor: str) -> None:
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
        self.lbl_valor = QLabel(valor)
        self.lbl_valor.setStyleSheet(
            f"color: {cor}; font-size: 26px; font-weight: 700; background: transparent; letter-spacing: -0.5px;"
        )
        layout.addWidget(lbl_titulo)
        layout.addWidget(self.lbl_valor)

    def set_valor(self, valor: str) -> None:
        self.lbl_valor.setText(valor)


class TechnicianAgendaPage(QWidget):
    _session: Any
    _technician_service: Any
    _activity_service: Any
    _printer_service: Any
    _tecnico_combo: QComboBox
    _date_picker: QDateEdit
    _card_capacidade: _StatsCard
    _card_agendadas: _StatsCard
    _card_andamento: _StatsCard
    _tabs: QTabWidget
    _tab_agenda: QWidget
    _tab_produtividade: QWidget
    _tabela_agenda: QTableWidget
    _tabela_produtividade: QTableWidget
    _rota_label: QLabel

    def __init__(self, session: Any, technician_service: Any, activity_service: Any,
                 printer_service: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session = session
        self._technician_service = technician_service
        self._activity_service = activity_service
        self._printer_service = printer_service
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        titulo = QLabel("\U0001f4c5 Agenda do Técnico")
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

        lbl_data = QLabel("Data:")
        lbl_data.setStyleSheet("color: #94949f; font-size: 13px; font-weight: 500; background: transparent;")
        filtros.addWidget(lbl_data)

        self._date_picker = QDateEdit()
        self._date_picker.setCalendarPopup(True)
        self._date_picker.setDate(QDate.currentDate())
        self._date_picker.setDisplayFormat("dd/MM/yyyy")
        self._date_picker.dateChanged.connect(self._recarregar_agenda)
        filtros.addWidget(self._date_picker)

        btn_atualizar = QPushButton("\u21bb Atualizar")
        btn_atualizar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_atualizar.clicked.connect(self._recarregar_agenda)
        filtros.addStretch()
        filtros.addWidget(btn_atualizar)

        layout.addLayout(filtros)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self._card_capacidade = _StatsCard("Capacidade", "0 / 0", "#6366f1")
        self._card_agendadas = _StatsCard("OS no Dia", "0", "#3b82f6")
        self._card_andamento = _StatsCard("Em Andamento", "0", "#f59e0b")
        cards.addWidget(self._card_capacidade)
        cards.addWidget(self._card_agendadas)
        cards.addWidget(self._card_andamento)
        layout.addLayout(cards)

        self._rota_label = QLabel()
        self._rota_label.setStyleSheet(
            "color: #94949f; font-size: 12px; background: transparent; padding: 4px 0;"
        )
        self._rota_label.setWordWrap(True)
        layout.addWidget(self._rota_label)

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs, 1)

        self._tab_agenda = self._criar_tabela_agenda()
        self._tabs.addTab(self._tab_agenda, "\U0001f4cb Agenda do Dia")

        self._tab_produtividade = self._criar_tabela_produtividade()
        self._tabs.addTab(self._tab_produtividade, "\U0001f4ca Produtividade")

    def _criar_tabela_agenda(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self._tabela_agenda = QTableWidget()
        self._tabela_agenda.setColumnCount(8)
        self._tabela_agenda.setHorizontalHeaderLabels(
            ["Ordem", "Patrimônio", "Local", "Tipo", "Descrição", "Status", "Urgência", "Recibo"]
        )
        self._tabela_agenda.setStyleSheet(ESTILO_TABELA_SIMPLES)
        self._tabela_agenda.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabela_agenda.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabela_agenda.verticalHeader().setVisible(False)
        self._tabela_agenda.setAlternatingRowColors(True)
        self._tabela_agenda.verticalHeader().setDefaultSectionSize(40)
        h = self._tabela_agenda.horizontalHeader()
        for i in range(8):
            h.setSectionResizeMode(i, QHeaderView.Stretch)
        layout.addWidget(self._tabela_agenda)
        return tab

    def _criar_tabela_produtividade(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        filtros_periodo = QHBoxLayout()
        filtros_periodo.setSpacing(10)

        lbl_inicio = QLabel("Início:")
        lbl_inicio.setStyleSheet("color: #94949f; font-size: 13px; font-weight: 500; background: transparent;")
        filtros_periodo.addWidget(lbl_inicio)

        hoje = QDate.currentDate()
        self._periodo_inicio = QDateEdit()
        self._periodo_inicio.setCalendarPopup(True)
        self._periodo_inicio.setDate(hoje.addMonths(-1))
        self._periodo_inicio.setDisplayFormat("dd/MM/yyyy")
        filtros_periodo.addWidget(self._periodo_inicio)

        lbl_fim = QLabel("Fim:")
        lbl_fim.setStyleSheet("color: #94949f; font-size: 13px; font-weight: 500; background: transparent;")
        filtros_periodo.addWidget(lbl_fim)

        self._periodo_fim = QDateEdit()
        self._periodo_fim.setCalendarPopup(True)
        self._periodo_fim.setDate(hoje)
        self._periodo_fim.setDisplayFormat("dd/MM/yyyy")
        filtros_periodo.addWidget(self._periodo_fim)

        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_filtrar.clicked.connect(self._recarregar_produtividade)
        filtros_periodo.addWidget(btn_filtrar)

        filtros_periodo.addStretch()
        layout.addLayout(filtros_periodo)

        cards_prod = QHBoxLayout()
        cards_prod.setSpacing(12)
        self._card_concluidas = _StatsCard("OS Concluídas", "0", "#10b981")
        self._card_pecas = _StatsCard("Peças Usadas", "0", "#f59e0b")
        self._card_tempo_medio = _StatsCard("Tempo Médio", "0min", "#6366f1")
        cards_prod.addWidget(self._card_concluidas)
        cards_prod.addWidget(self._card_pecas)
        cards_prod.addWidget(self._card_tempo_medio)
        layout.addLayout(cards_prod)

        self._tabela_produtividade = QTableWidget()
        self._tabela_produtividade.setColumnCount(7)
        self._tabela_produtividade.setHorizontalHeaderLabels(
            ["Data/Hora", "Patrimônio", "Descrição", "Peças", "Início", "Fim", "Duração"]
        )
        self._tabela_produtividade.setStyleSheet(ESTILO_TABELA_SIMPLES)
        self._tabela_produtividade.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabela_produtividade.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabela_produtividade.verticalHeader().setVisible(False)
        self._tabela_produtividade.setAlternatingRowColors(True)
        self._tabela_produtividade.verticalHeader().setDefaultSectionSize(40)
        h = self._tabela_produtividade.horizontalHeader()
        for i in range(7):
            h.setSectionResizeMode(i, QHeaderView.Stretch)
        layout.addWidget(self._tabela_produtividade, 1)
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
            self._recarregar_agenda()

    def _ao_trocar_tecnico(self) -> None:
        self._recarregar_agenda()

    def _recarregar_agenda(self) -> None:
        tech_id = self._tecnico_combo.currentData()
        if tech_id is None:
            self._tabela_agenda.setRowCount(0)
            self._card_capacidade.set_valor("0 / 0")
            self._card_agendadas.set_valor("0")
            self._card_andamento.set_valor("0")
            self._rota_label.setText("")
            return

        qdate = self._date_picker.date()
        data = dt(qdate.year(), qdate.month(), qdate.day())

        tecnico = self._technician_service.buscar_por_id(tech_id)
        capacidade = tecnico.capacidade_diaria if tecnico else 5

        atividades = self._activity_service.listar_por_tecnico_e_data(tech_id, data)
        em_andamento = self._activity_service.contar_por_tecnico_por_status(tech_id, "Em Atendimento")
        total_no_dia = len(atividades)

        self._card_capacidade.set_valor(f"{total_no_dia} / {capacidade}")
        self._card_agendadas.set_valor(str(total_no_dia))
        self._card_andamento.set_valor(str(em_andamento))

        self._preencher_agenda(atividades)
        self._sugerir_rota(atividades)

    def _sugerir_rota(self, atividades: list) -> None:
        if not atividades:
            self._rota_label.setText("Nenhuma OS agendada para este dia.")
            return

        locais = []
        for a in atividades:
            local = a.from_location or "Sem local"
            locais.append(local)

        ordem = list(dict.fromkeys(locais))
        setores_contagem = Counter(locais)
        resumo = " \u2192 ".join(f"{l}" for l in ordem)
        detalhes = "; ".join(f"{l}: {setores_contagem[l]} OS" for l in ordem)
        self._rota_label.setText(
            f"\U0001f9ed Rota Sugerida: {resumo}   |   {detalhes}"
        )

    def _preencher_agenda(self, atividades: list) -> None:
        if not atividades:
            self._tabela_agenda.setRowCount(0)
            return

        locais = []
        for a in atividades:
            locais.append(a.from_location or "Sem local")
        ordem_locais = list(dict.fromkeys(locais))

        local_para_numero = {l: i + 1 for i, l in enumerate(ordem_locais)}

        linhas = []
        for a in atividades:
            local = a.from_location or "Sem local"
            ordem = local_para_numero[local]
            linhas.append((ordem, local, a))

        linhas.sort(key=lambda x: (x[0], x[2].event_at or dt.min))

        self._tabela_agenda.setRowCount(0)
        self._tabela_agenda.setRowCount(len(linhas))
        for i, (ordem, local, a) in enumerate(linhas):
            printer = self._printer_service.buscar_por_id(a.printer_id) if hasattr(self, '_printer_service') else None
            pat = printer.patrimonio if printer else a.printer_id

            ordem_item = QTableWidgetItem(str(ordem))
            ordem_item.setTextAlignment(Qt.AlignCenter)
            self._tabela_agenda.setItem(i, 0, ordem_item)
            self._tabela_agenda.setItem(i, 1, QTableWidgetItem(pat))
            self._tabela_agenda.setItem(i, 2, QTableWidgetItem(local))
            self._tabela_agenda.setItem(i, 3, QTableWidgetItem(a.kind or ""))
            self._tabela_agenda.setItem(i, 4, QTableWidgetItem((a.notes or "")[:80]))
            self._tabela_agenda.setItem(i, 5, QTableWidgetItem(a.status_atividade or ""))
            self._tabela_agenda.setItem(i, 6, QTableWidgetItem(a.urgencia or ""))
            self._tabela_agenda.setItem(i, 7, QTableWidgetItem(a.numero_recibo or ""))

    def _recarregar_produtividade(self) -> None:
        tech_id = self._tecnico_combo.currentData()
        if tech_id is None:
            self._tabela_produtividade.setRowCount(0)
            self._card_concluidas.set_valor("0")
            self._card_pecas.set_valor("0")
            self._card_tempo_medio.set_valor("0min")
            return

        q_inicio = self._periodo_inicio.date()
        q_fim = self._periodo_fim.date()
        inicio = dt(q_inicio.year(), q_inicio.month(), q_inicio.day(), 0, 0, 0)
        fim = dt(q_fim.year(), q_fim.month(), q_fim.day(), 23, 59, 59)

        concluidas = self._activity_service.listar_concluidas_por_tecnico_no_periodo(tech_id, inicio, fim)

        total_pecas = 0
        duracoes = []
        for a in concluidas:
            if a.parts_used:
                total_pecas += len([p for p in a.parts_used.split(",") if p.strip()])
            if a.inicio_atendimento and a.fim_atendimento:
                diff = (a.fim_atendimento - a.inicio_atendimento).total_seconds()
                if diff > 0:
                    duracoes.append(diff)

        tempo_medio = sum(duracoes) / len(duracoes) if duracoes else 0
        horas = int(tempo_medio // 3600)
        minutos = int((tempo_medio % 3600) // 60)
        if horas > 0:
            tempo_str = f"{horas}h {minutos}min"
        else:
            tempo_str = f"{minutos}min"

        self._card_concluidas.set_valor(str(len(concluidas)))
        self._card_pecas.set_valor(str(total_pecas))
        self._card_tempo_medio.set_valor(tempo_str)

        self._tabela_produtividade.setRowCount(0)
        self._tabela_produtividade.setRowCount(len(concluidas))
        for i, a in enumerate(concluidas):
            printer = self._printer_service.buscar_por_id(a.printer_id) if hasattr(self, '_printer_service') else None
            pat = printer.patrimonio if printer else a.printer_id

            def fmt(dt_val):
                return dt_val.strftime("%d/%m/%Y %H:%M") if dt_val else "-"

            duracao = "-"
            if a.inicio_atendimento and a.fim_atendimento:
                diff = (a.fim_atendimento - a.inicio_atendimento).total_seconds()
                h = int(diff // 3600)
                m = int((diff % 3600) // 60)
                duracao = f"{h}h {m}min" if h > 0 else f"{m}min"

            self._tabela_produtividade.setItem(i, 0, QTableWidgetItem(fmt(a.fim_atendimento or a.event_at)))
            self._tabela_produtividade.setItem(i, 1, QTableWidgetItem(pat))
            self._tabela_produtividade.setItem(i, 2, QTableWidgetItem((a.notes or "")[:80]))
            self._tabela_produtividade.setItem(i, 3, QTableWidgetItem(a.parts_used or ""))
            self._tabela_produtividade.setItem(i, 4, QTableWidgetItem(fmt(a.inicio_atendimento)))
            self._tabela_produtividade.setItem(i, 5, QTableWidgetItem(fmt(a.fim_atendimento)))
            self._tabela_produtividade.setItem(i, 6, QTableWidgetItem(duracao))
