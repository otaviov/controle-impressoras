from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)
from datetime import datetime as dt

from app.services.notification_service import NotificadorService
from app.utils.ui_helpers import exportar_em_thread
from app.services import (
    ActivityService,
    AlertService,
    AuditService,
    CompanyService,
    DashboardService,
    LoginHistoryService,
    MaintenanceScheduler,
    PartService,
    PrinterLocationService,
    PrinterService,
    SnmpMonitorService,
    TechnicianService,
    UserService,
)
from app.views.widgets.toast import ToastManager
from app.views.pages import (
    AlertasPage,
    CalendarPage,
    ClientsPage,
    ConfigPage,
    DashboardPage,
    MonitoringPage,
    OSPage,
    PartsPage,
    PrintersPage,
    PurchaseRequisitionsPage,
    ReportsPage,
    TechnicianAgendaPage,
    TechnicianHistoryPage,
    TechniciansPage,
    TransfersPage,
)

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    session: Any
    user: dict[str, Any]
    audit_service: AuditService
    printer_service: PrinterService
    activity_service: ActivityService
    company_service: CompanyService
    part_service: PartService
    technician_service: TechnicianService
    user_service: UserService
    dashboard_service: DashboardService
    alert_service: AlertService
    maintenance_scheduler: MaintenanceScheduler
    login_history_service: LoginHistoryService
    snmp_monitor_service: SnmpMonitorService  # type: ignore[name-defined]
    printer_location_service: PrinterLocationService
    tray_icon: QSystemTrayIcon
    notificador: NotificadorService
    menu_buttons: list[QPushButton]
    _menu_indices: list[int]
    _menu_containers: list[QFrame]
    _menu_indicators: list[QFrame]
    btn_tema: QPushButton
    btn_toggle_sidebar: QPushButton
    content_area: QStackedWidget
    pagina_dashboard: DashboardPage
    pagina_impressoras: PrintersPage
    pagina_os: OSPage
    pagina_clientes: ClientsPage
    pagina_pecas: PartsPage
    pagina_transferencias: TransfersPage
    pagina_tecnicos: TechniciansPage
    pagina_historico: TechnicianHistoryPage
    pagina_relatorios: ReportsPage
    pagina_alertas: AlertasPage
    pagina_calendario: CalendarPage
    pagina_agenda: TechnicianAgendaPage
    pagina_requisicoes: PurchaseRequisitionsPage
    pagina_config: ConfigPage | None
    pagina_monitoramento: MonitoringPage

    def __init__(self, session: Any, user: dict[str, Any]) -> None:
        super().__init__()
        self.session = session
        self.user = user

        # ── Serviços ──────────────────────────────────────────
        self.audit_service = AuditService(session)
        self.printer_service = PrinterService(session, audit_service=self.audit_service, user_id=self.user.get("id"))
        self.printer_location_service = PrinterLocationService(session, audit_service=self.audit_service, user_id=self.user.get("id"))
        self.activity_service = ActivityService(session, audit_service=self.audit_service, user_id=self.user.get("id"))
        self.company_service = CompanyService(session, audit_service=self.audit_service, user_id=self.user.get("id"))
        self.part_service = PartService(session, audit_service=self.audit_service, user_id=self.user.get("id"))
        self.technician_service = TechnicianService(session, audit_service=self.audit_service, user_id=self.user.get("id"))
        self.user_service = UserService(session, audit_service=self.audit_service, user_id=self.user.get("id"))
        self.dashboard_service = DashboardService(session)
        self.alert_service = AlertService(session, audit_service=self.audit_service, user_id=self.user.get("id"))
        self.login_history_service = LoginHistoryService(session)
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("printer"))
        self.tray_icon.setToolTip("Controle de Impressoras Pro")
        self.tray_icon.show()

        self.notificador = NotificadorService(tray_icon=self.tray_icon)

        self.snmp_monitor_service = SnmpMonitorService(
            session,
            alert_service=self.alert_service,
            notificador=self.notificador,
        )

        self.maintenance_scheduler = MaintenanceScheduler(
            session,
            activity_service=self.activity_service,
            alert_service=self.alert_service,
            audit_service=self.audit_service,
            user_id=self.user.get("id"),
        )

        for svc in [self.alert_service]:
            if hasattr(svc, "notificador"):
                svc.notificador = self.notificador

        self.menu_buttons = []
        self._menu_indices = []
        self._menu_containers = []
        self._menu_indicators = []
        self.init_ui()

    def closeEvent(self, event: Any) -> None:
        login_id = self.user.get("login_history_id")
        if login_id:
            try:
                self.login_history_service.registrar_logout(self.user["id"])
            except Exception:
                log.exception("Erro ao registrar logout")
        super().closeEvent(event)

    # ── UI ──────────────────────────────────────────────────────
    def init_ui(self) -> None:
        self.setWindowTitle("Controle de Impressoras Pro")
        self.setMinimumSize(1200, 700)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(224)
        sidebar.setStyleSheet("QFrame#sidebar { background-color: #0f0f16; border-right: 1px solid #1e1e2e; }")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        scroll_sidebar = QScrollArea()
        scroll_sidebar.setWidgetResizable(True)
        scroll_sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_sidebar.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollBar:vertical { width: 0; }")
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(8, 0, 8, 0)
        scroll_layout.setSpacing(0)

        # Logo
        self._adicionar_logo(scroll_layout)
        scroll_layout.addSpacing(6)

        # ── Seção Principal (ordem Figma) ──
        self._adicionar_label_secao(scroll_layout, "Principal")
        menus_principais = [
            ("📊", "Dashboard", 0),
            ("🖨️", "Impressoras", 1),
            ("🔧", "Peças", 4),
            ("📋", "Ordens de Serviço", 2),
            ("🚚", "Transferências", 5),
            ("📈", "Relatórios", 8),
        ]
        for icon, text, index in menus_principais:
            container = self._criar_botao_menu(icon, text, index)
            scroll_layout.addWidget(container)

        scroll_layout.addSpacing(8)

        # ── Seção Extra (páginas sem Figma) ──
        self._adicionar_label_secao(scroll_layout, "Outros")
        menus_extra = [
            ("👥", "Empresas/Clientes", 3),
            ("👨‍🔧", "Técnicos", 6),
            ("🗓️", "Agenda", 11),
            ("🛒", "Requisições", 12),
            ("📜", "Histórico", 7),
            ("🔔", "Alertas", 9),
            ("📅", "Calendário", 10),
            ("📡", "Monitoramento", 13),
        ]
        for icon, text, index in menus_extra:
            container = self._criar_botao_menu(icon, text, index)
            scroll_layout.addWidget(container)

        if self.user.get('perfil') == 'admin':
            scroll_layout.addSpacing(8)
            self._adicionar_label_secao(scroll_layout, "Sistema")
            container = self._criar_botao_menu("⚙️", "Configurações", 14)
            scroll_layout.addWidget(container)

        scroll_layout.addStretch()
        scroll_sidebar.setWidget(scroll_content)
        sidebar_layout.addWidget(scroll_sidebar)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background-color: #1e1e2e; max-height: 1px; margin: 0 12px;")
        sidebar_layout.addWidget(sep2)

        self._adicionar_botao_tema(sidebar_layout)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet("background-color: #1e1e2e; max-height: 1px; margin: 0 12px;")
        sidebar_layout.addWidget(sep3)

        # User card + sair
        self._adicionar_card_usuario(sidebar_layout)

        # ── Right Panel (Topbar + Content) ─────────────────────
        right_panel = QFrame()
        right_panel.setObjectName("rightPanel")
        right_panel.setStyleSheet("QFrame#rightPanel { background-color: #0a0a0f; border: none; }")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Topbar
        self._adicionar_topbar(right_layout)

        # ── Pages ─────────────────────────────────────────────
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("background-color: #0a0a0f; border: none;")

        self.pagina_dashboard = DashboardPage(
            self.session, self.printer_service,
            self.activity_service, self.dashboard_service
        )
        self.pagina_impressoras = PrintersPage(
            self.session, self.printer_service,
            self.company_service, self.technician_service,
            self.activity_service, self.part_service,
            self.printer_location_service,
            scheduler=self.maintenance_scheduler,
            monitor_service=self.snmp_monitor_service,
        )
        self.pagina_os = OSPage(
            self.session, self.printer_service,
            self.activity_service, self.company_service,
            self.technician_service,
            alert_service=self.alert_service,
        )
        self.pagina_clientes = ClientsPage(
            self.session, self.company_service, self.printer_service
        )
        self.pagina_pecas = PartsPage(
            self.session, self.part_service, self.printer_service, self.activity_service
        )
        self.pagina_transferencias = TransfersPage(
            self.session, self.printer_service,
            self.activity_service, self.company_service,
        )
        self.pagina_tecnicos = TechniciansPage(
            self.session, self.technician_service, printer_service=self.printer_service
        )
        self.pagina_historico = TechnicianHistoryPage(
            self.session, self.technician_service,
            self.activity_service, self.user_service,
            self.login_history_service, self.printer_service
        )
        self.pagina_relatorios = ReportsPage(
            self.session, self.printer_service, self.activity_service, self.company_service
        )
        self.pagina_alertas = AlertasPage(
            self.session, self.alert_service, self.printer_service, part_service=self.part_service
        )
        self.pagina_calendario = CalendarPage(
            scheduler=self.maintenance_scheduler,
            activity_service=self.activity_service,
            technician_service=self.technician_service,
            alert_service=self.alert_service,
        )
        self.pagina_agenda = TechnicianAgendaPage(
            self.session, self.technician_service,
            self.activity_service, self.printer_service,
        )
        self.pagina_requisicoes = PurchaseRequisitionsPage(
            self.session, self.part_service,
        )

        self.content_area.addWidget(self.pagina_dashboard)        # 0
        self.content_area.addWidget(self.pagina_impressoras)      # 1
        self.content_area.addWidget(self.pagina_os)               # 2
        self.content_area.addWidget(self.pagina_clientes)         # 3
        self.content_area.addWidget(self.pagina_pecas)            # 4
        self.content_area.addWidget(self.pagina_transferencias)   # 5
        self.content_area.addWidget(self.pagina_tecnicos)         # 6
        self.content_area.addWidget(self.pagina_historico)        # 7
        self.content_area.addWidget(self.pagina_relatorios)       # 8
        self.content_area.addWidget(self.pagina_alertas)          # 9
        self.content_area.addWidget(self.pagina_calendario)       # 10
        self.content_area.addWidget(self.pagina_agenda)           # 11
        self.content_area.addWidget(self.pagina_requisicoes)      # 12

        self.pagina_monitoramento = MonitoringPage(
            self.session,
            monitor_service=self.snmp_monitor_service,
        )
        self.content_area.addWidget(self.pagina_monitoramento)    # 13

        if self.user.get('perfil') == 'admin':
            self.pagina_config = ConfigPage(
                self.session, self.user_service, self.user,
                notificador=self.notificador,
                audit_service=self.audit_service,
                printer_service=self.printer_service,
                part_service=self.part_service,
                company_service=self.company_service,
                activity_service=self.activity_service,
                technician_service=self.technician_service,
                alert_service=self.alert_service,
            )
            self.content_area.addWidget(self.pagina_config)       # 14

        # ── Conexões de sinais ─────────────────────────────────
        self.pagina_dashboard.signal_trocar_pagina.connect(self._trocar_pagina)
        self.pagina_clientes.abrir_impressora.connect(self._abrir_impressora_por_patrimonio)
        self.pagina_pecas.abrir_atividade.connect(self._abrir_atividade_por_id)
        self.pagina_historico.abrir_os.connect(self._abrir_atividade_por_id)
        self.pagina_calendario.abrir_atividade.connect(self._abrir_atividade_por_id)
        self.pagina_calendario.abrir_impressora.connect(self._abrir_impressora_por_patrimonio)

        main_layout.addWidget(sidebar)
        right_layout.addWidget(self.content_area, 1)
        main_layout.addWidget(right_panel, 1)

        ToastManager.instalar(self)

        QTimer.singleShot(0, self._verificar_alertas)
        self._timer_alertas = QTimer(self)
        self._timer_alertas.timeout.connect(self._verificar_alertas)
        self._timer_alertas.start(3600000)

        self._trocar_pagina(0)

    def _adicionar_botao_tema(self, layout: QVBoxLayout) -> None:
        from app.views.styles.theme_manager import TemaManager
        tema_frame = QFrame()
        tema_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        tema_frame_layout = QHBoxLayout(tema_frame)
        tema_frame_layout.setContentsMargins(14, 6, 14, 6)
        tema_frame_layout.setSpacing(8)

        self.btn_tema = QPushButton()
        self.btn_tema.setCursor(Qt.PointingHandCursor)
        self.btn_tema.setFixedHeight(30)
        self._atualizar_texto_tema()
        self.btn_tema.clicked.connect(self._alternar_tema)
        tema_frame_layout.addWidget(self.btn_tema)
        layout.addWidget(tema_frame)

    def _atualizar_texto_tema(self) -> None:
        from app.views.styles.theme_manager import TemaManager
        is_dark = TemaManager.atual() == "dark"
        icone = "🌙" if is_dark else "☀️"
        label = " Escuro" if is_dark else " Claro"
        self.btn_tema.setText(f"{icone}{label}")
        base = (
            "QPushButton { background: transparent; color: #717182; border: 1px solid #2a2a3e;"
            " border-radius: 6px; font-size: 11px; font-weight: 500; padding: 4px 12px;"
            " text-align: left; }"
            " QPushButton:hover { background: #1e1e2e; color: #e8e8f0; border-color: #6366f1; }"
        )
        self.btn_tema.setStyleSheet(base)

    def _alternar_tema(self) -> None:
        from app.views.styles.theme_manager import TemaManager
        TemaManager.limpar_estilos(self)
        TemaManager.alternar()
        self._atualizar_texto_tema()
        self._restyle_sidebar()
        paginas = [self.content_area.widget(i) for i in range(self.content_area.count())]
        TemaManager.reestilizar_paginas([w for w in paginas if w])

    def _restyle_sidebar(self) -> None:
        from app.views.styles.theme_manager import TemaManager
        is_dark = TemaManager.atual() == "dark"
        if is_dark:
            bg = "#0f0f16"
            border = "#1e1e2e"
            sep = "#1e1e2e"
            nav_hover = "#1e1e2e"
            nav_active = "rgba(99, 102, 241, 0.12)"
            nav_text = "#717182"
            nav_text_hover = "#e8e8f0"
            nav_text_active = "#6366f1"
            user_bg = "transparent"
            user_text = "#e8e8f0"
            user_role = "#717182"
            btn_border = "#2a2a3e"
            btn_text = "#717182"
        else:
            bg = "#ffffff"
            border = "#e2e8f0"
            sep = "#e2e8f0"
            nav_hover = "#f1f5f9"
            nav_active = "#eef2ff"
            nav_text = "#64748b"
            nav_text_hover = "#334155"
            nav_text_active = "#7c3aed"
            user_bg = "#f8fafc"
            user_text = "#0f172a"
            user_role = "#64748b"
            btn_border = "#e2e8f0"
            btn_text = "#64748b"
        sidebar = self.findChild(QFrame, "sidebar")
        if sidebar:
            sidebar.setStyleSheet(f"QFrame#sidebar {{ background-color: {bg}; border-right: 1px solid {border}; }}")
        for sep_frame in self.findChildren(QFrame):
            if sep_frame.frameShape() == QFrame.HLine:
                sep_frame.setStyleSheet(f"background-color: {sep}; max-height: 1px; margin: 0 12px;")


    # ── Sidebar helpers ─────────────────────────────────────────
    def _adicionar_topbar(self, layout: QVBoxLayout) -> None:
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(56)
        topbar.setStyleSheet(
            "QFrame#topbar { background-color: rgba(20, 20, 31, 0.5);"
            " border-bottom: 1px solid #2a2a3e; }"
        )
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(24, 0, 24, 0)
        topbar_layout.setSpacing(12)

        self.btn_toggle_sidebar = QPushButton("☰")
        self.btn_toggle_sidebar.setFixedSize(32, 32)
        self.btn_toggle_sidebar.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_sidebar.setStyleSheet(
            "QPushButton { background: transparent; color: #717182; border: none;"
            " border-radius: 6px; font-size: 16px; }"
            " QPushButton:hover { background-color: #1e1e2e; color: #e8e8f0; }"
        )
        self.btn_toggle_sidebar.clicked.connect(self._toggle_sidebar)
        topbar_layout.addWidget(self.btn_toggle_sidebar)

        topbar_layout.addStretch()

        modo_frame = QFrame()
        modo_frame.setStyleSheet(
            "QFrame { background-color: rgba(99, 102, 241, 0.08);"
            " border: 1px solid rgba(99, 102, 241, 0.15); border-radius: 6px; padding: 3px 10px; }"
        )
        modo_layout = QHBoxLayout(modo_frame)
        modo_layout.setContentsMargins(8, 4, 8, 4)
        modo_layout.setSpacing(4)
        modo_text = QLabel("🌙  Escuro")
        modo_text.setStyleSheet("color: #6366f1; font-size: 11px; font-weight: 500; background: transparent;")
        modo_layout.addWidget(modo_text)
        topbar_layout.addWidget(modo_frame)

        layout.addWidget(topbar)

    def _toggle_sidebar(self) -> None:
        sidebar = self.findChild(QFrame, "sidebar")
        if sidebar:
            visible = sidebar.isVisible()
            sidebar.setVisible(not visible)
            self.btn_toggle_sidebar.setText("✕" if visible else "☰")

    def _adicionar_label_secao(self, layout: QVBoxLayout, texto: str) -> None:
        lbl = QLabel(texto.upper())
        lbl.setStyleSheet(
            "color: #717182; font-size: 9px; font-weight: 700;"
            " letter-spacing: 1.2px; padding: 12px 10px 4px 10px;"
            " background: transparent;"
        )
        layout.addWidget(lbl)

    def _adicionar_logo(self, layout: QVBoxLayout) -> None:
        logo_frame = QFrame()
        logo_frame.setStyleSheet("background: transparent; border: none;")
        logo_frame_layout = QHBoxLayout(logo_frame)
        logo_frame_layout.setContentsMargins(10, 20, 10, 14)
        logo_frame_layout.setSpacing(10)

        logo_icon = QLabel("🖨")
        logo_icon.setFixedSize(36, 36)
        logo_icon.setAlignment(Qt.AlignCenter)
        logo_icon.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #4f46e5,stop:1 #7c3aed);"
            " color: white; border-radius: 8px; font-size: 18px; font-weight: 700;"
        )
        logo_frame_layout.addWidget(logo_icon)

        logo_text_frame = QVBoxLayout()
        logo_text_frame.setSpacing(0)
        logo_text1 = QLabel("Controle de")
        logo_text1.setStyleSheet(
            "color: #e8e8f0; font-size: 11px; font-weight: 700;"
            " background: transparent; letter-spacing: 0.3px;"
        )
        logo_text2 = QLabel("Impressoras Pro")
        logo_text2.setStyleSheet(
            "color: #e8e8f0; font-size: 11px; font-weight: 700;"
            " background: transparent; letter-spacing: 0.3px;"
        )
        logo_text_frame.addWidget(logo_text1)
        logo_text_frame.addWidget(logo_text2)
        logo_frame_layout.addLayout(logo_text_frame)
        logo_frame_layout.addStretch()
        layout.addWidget(logo_frame)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #1e1e2e; max-height: 1px; margin: 0 12px;")
        layout.addWidget(sep)

    def _adicionar_card_usuario(self, layout: QVBoxLayout) -> None:
        user_frame = QFrame()
        user_frame.setStyleSheet(
            "QFrame { background: transparent; border: none; }"
        )
        user_frame_layout = QVBoxLayout(user_frame)
        user_frame_layout.setContentsMargins(12, 10, 12, 12)
        user_frame_layout.setSpacing(8)

        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)

        avatar = QLabel(self.user["nome"][:2].upper())
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #8b5cf6,stop:1 #ec4899);"
            " color: white; border-radius: 18px; font-size: 11px; font-weight: 700;"
        )
        info_layout.addWidget(avatar)

        user_info = QVBoxLayout()
        user_info.setSpacing(1)
        user_name = QLabel(self.user["nome"])
        user_name.setStyleSheet("color: #e8e8f0; font-size: 12px; font-weight: 500; background: transparent; border: none;")
        user_info.addWidget(user_name)
        user_role = QLabel(self.user["perfil"].capitalize())
        user_role.setStyleSheet("color: #717182; font-size: 10px; background: transparent; border: none;")
        user_info.addWidget(user_role)
        info_layout.addLayout(user_info)
        info_layout.addStretch()
        user_frame_layout.addLayout(info_layout)

        btn_sair = QPushButton("Sair")
        btn_sair.setCursor(Qt.PointingHandCursor)
        btn_sair.setMinimumHeight(32)
        btn_sair.setStyleSheet(
            "QPushButton { background: transparent; color: #717182; border: 1px solid #2a2a3e;"
            " border-radius: 6px; font-size: 11px; font-weight: 500; }"
            " QPushButton:hover { background: #ef444415; color: #ef4444; border-color: #ef444433; }"
        )
        btn_sair.clicked.connect(self.close)
        user_frame_layout.addWidget(btn_sair)

        layout.addWidget(user_frame)

    def _criar_botao_menu(self, icone: str, texto: str, indice: int) -> QFrame:
        container = QFrame()
        container.setObjectName("menuContainer")
        container.setStyleSheet("QFrame#menuContainer { background: transparent; border: none; }")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        indicador = QFrame()
        indicador.setFixedWidth(2)
        indicador.setObjectName("activeIndicator")
        indicador.setStyleSheet("QFrame#activeIndicator { background: transparent; border-radius: 0 2px 2px 0; }")
        indicador.setAttribute(Qt.WA_TransparentForMouseEvents)
        container_layout.addWidget(indicador)

        btn = QPushButton(f"{icone}  {texto}")
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(36)
        btn.setObjectName("menuBtn")
        btn.setStyleSheet(
            "QPushButton#menuBtn { background: transparent; color: #94949f; border: none;"
            " text-align: left; font-size: 13px; padding: 6px 12px; border-radius: 0px; font-weight: 500; }"
            " QPushButton#menuBtn:hover { background: #1e1e2e; color: #e8e8f0; }"
            " QPushButton#menuBtn:checked { background: rgba(99, 102, 241, 0.2); color: #6366f1; font-weight: 600; }"
        )
        container_layout.addWidget(btn)
        btn.clicked.connect(lambda: self._trocar_pagina(indice))

        self._menu_containers.append(container)
        self._menu_indicators.append(indicador)
        self.menu_buttons.append(btn)
        self._menu_indices.append(indice)
        return container

    # ── Navegação ────────────────────────────────────────────────
    def _trocar_pagina(self, index: int) -> None:
        for i, btn in enumerate(self.menu_buttons):
            is_active = self._menu_indices[i] == index
            btn.setChecked(is_active)
            if i < len(self._menu_indicators):
                ind = self._menu_indicators[i]
                ind.setStyleSheet(
                    "QFrame#activeIndicator { background: #6366f1; border-radius: 0 2px 2px 0; }"
                    if is_active
                    else "QFrame#activeIndicator { background: transparent; border-radius: 0 2px 2px 0; }"
                )
        self.content_area.setCurrentIndex(index)

        pagina_atual = self.content_area.currentWidget()
        if hasattr(pagina_atual, 'recarregar'):
            pagina_atual.recarregar()

    # ── Ações ────────────────────────────────────────────────────
    def _abrir_atividade_por_id(self, activity_id: int) -> None:
        self.pagina_os.editar_atividade_por_id(activity_id)

    def _abrir_impressora_por_patrimonio(self, patrimonio: str) -> None:
        self._trocar_pagina(1)
        self.pagina_impressoras.filtrar(patrimonio)
        for row in range(self.pagina_impressoras.tabela.rowCount()):
            if self.pagina_impressoras.tabela.item(row, 0).text() == patrimonio:
                self.pagina_impressoras._detalhes(row)
                break

    def carregar_dados(self) -> None:
        """Recarrega todas as páginas"""
        for pagina in [
            self.pagina_dashboard, self.pagina_impressoras,
            self.pagina_os, self.pagina_clientes,
            self.pagina_pecas, self.pagina_transferencias,
            self.pagina_tecnicos, self.pagina_historico,
            self.pagina_relatorios, self.pagina_alertas,
            self.pagina_calendario, self.pagina_agenda,
            self.pagina_monitoramento,
        ]:
            if hasattr(pagina, 'recarregar'):
                pagina.recarregar()

    def _verificar_alertas(self) -> None:
        try:
            novos_estoque = self.alert_service.verificar_estoque_baixo()
            if novos_estoque:
                log.info(f"Gerados {novos_estoque} alerta(s) de estoque baixo")
        except Exception as e:
            log.warning(f"Erro ao verificar estoque baixo: {e}")

        pendentes = self.alert_service.contar_pendentes()
        if pendentes:
            ToastManager.aviso(f"{pendentes} alerta(s) pendente(s) — clique em 🔔 Alertas para ver", persistente=True)
        else:
            ToastManager.sucesso("Nenhum alerta pendente")

        try:
            alertas_agendados = self.alert_service.verificar_agendados()
            for a in alertas_agendados:
                ref = a.printer.patrimonio if a.printer else (a.part.nome if a.part else "")
                ToastManager.aviso(f"⏰ {a.titulo}{' — '+ref if ref else ''}")
            if alertas_agendados:
                log.info(f"Notificados {len(alertas_agendados)} alerta(s) agendados")
        except Exception as e:
            log.warning(f"Erro ao verificar alertas agendados: {e}")

        try:
            res = self.maintenance_scheduler.verificar_vencimentos()
            if res["alertas_criados"] or res["os_geradas"]:
                log.info(
                    "Manutenção programada: %d alerta(s), %d OS gerada(s)",
                    res["alertas_criados"], res["os_geradas"],
                )
            if res["os_geradas"]:
                ToastManager.sucesso(f"{res['os_geradas']} OS de manutenção gerada(s) automaticamente")
        except Exception as e:
            log.warning(f"Erro ao verificar manutenção programada: {e}")

    # ── Exportação ───────────────────────────────────────────────
    def _exportar(self, tipo: str, formato: str):
        import os
        from datetime import datetime as dt

        from PySide6.QtWidgets import QFileDialog

        from app.services.relatorio_service import RelatorioService

        default_name = f"{tipo}_{dt.now().strftime('%Y%m%d')}.{formato}"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório", default_name,
            f"{'PDF' if formato == 'pdf' else 'Excel'} (*.{formato})"
        )
        if not filepath:
            return

        try:
            if tipo == "impressoras":
                data = self.printer_service.listar_todos()
            else:
                data = self.activity_service.listar(limite=500)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao buscar dados: {str(e)}")
            return

        export_fn = None
        if tipo == "impressoras":
            export_fn = RelatorioService.exportar_impressoras_pdf if formato == "pdf" else RelatorioService.exportar_impressoras_excel
        else:
            export_fn = RelatorioService.exportar_atividades_pdf if formato == "pdf" else RelatorioService.exportar_atividades_excel

        def _ao_finalizar(fp: str) -> None:
            try:
                os.startfile(fp)
            except Exception:
                log.exception("Erro ao abrir arquivo exportado")
            QMessageBox.information(self, "Sucesso", f"Relatório salvo em:\n{fp}")

        exportar_em_thread(export_fn, data, filepath, on_finish=_ao_finalizar)
