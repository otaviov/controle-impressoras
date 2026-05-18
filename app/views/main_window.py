from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from app.services import (
    PrinterService, ActivityService, CompanyService,
    PartService, TechnicianService, UserService, DashboardService,
    AlertService, AuditService, TransferService
)
from app.views.pages import (
    DashboardPage, PrintersPage, OSPage, ClientsPage,
    PartsPage, TransfersPage, TechniciansPage, ReportsPage, ConfigPage
)


class MainWindow(QMainWindow):
    def __init__(self, session, user):
        super().__init__()
        self.session = session
        self.user = user

        # ── Serviços ──────────────────────────────────────────
        self.printer_service = PrinterService(session)
        self.activity_service = ActivityService(session)
        self.company_service = CompanyService(session)
        self.part_service = PartService(session)
        self.technician_service = TechnicianService(session)
        self.user_service = UserService(session)
        self.dashboard_service = DashboardService(session)
        self.alert_service = AlertService(session)
        self.audit_service = AuditService(session)
        self.transfer_service = TransferService(session)

        self.menu_buttons = []
        self.init_ui()

    # ── UI ──────────────────────────────────────────────────────
    def init_ui(self):
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
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet("QFrame#sidebar { background-color: #0d0d14; border-right: 1px solid #1a1a2a; }")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 0, 8, 0)
        sidebar_layout.setSpacing(0)

        # Logo
        self._adicionar_logo(sidebar_layout)
        sidebar_layout.addSpacing(8)

        # ── Seção Principal ──
        self._adicionar_label_secao(sidebar_layout, "Principal")
        menus_principal = [
            ("📊", "Dashboard", 0),
            ("🖨️", "Impressoras", 1),
            ("📋", "Ordens de Serviço", 2),
        ]
        for icon, text, index in menus_principal:
            btn = self._criar_botao_menu(icon, text)
            btn.clicked.connect(lambda checked, i=index: self._trocar_pagina(i))
            sidebar_layout.addWidget(btn)
            self.menu_buttons.append(btn)

        sidebar_layout.addSpacing(12)

        # ── Seção Gestão ──
        self._adicionar_label_secao(sidebar_layout, "Gestão")
        menus_gestao = [
            ("👥", "Empresas/Clientes", 3),
            ("🔧", "Peças", 4),
            ("🚚", "Transferências", 5),
            ("👨‍🔧", "Técnicos", 6),
            ("📈", "Relatórios", 7),
        ]
        for icon, text, index in menus_gestao:
            btn = self._criar_botao_menu(icon, text)
            btn.clicked.connect(lambda checked, i=index: self._trocar_pagina(i))
            sidebar_layout.addWidget(btn)
            self.menu_buttons.append(btn)

        if self.user.get('perfil') == 'admin':
            sidebar_layout.addSpacing(12)
            self._adicionar_label_secao(sidebar_layout, "Sistema")
            btn_config = self._criar_botao_menu("⚙️", "Configurações")
            btn_config.clicked.connect(lambda: self._trocar_pagina(8))
            sidebar_layout.addWidget(btn_config)
            self.menu_buttons.append(btn_config)

        sidebar_layout.addStretch()

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background-color: #1a1a2a; max-height: 1px; margin: 8px 12px;")
        sidebar_layout.addWidget(sep2)

        # User card + sair
        self._adicionar_card_usuario(sidebar_layout)

        # ── Pages ─────────────────────────────────────────────
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("background-color: #1e1e2e;")
        self.content_area.setMinimumWidth(400)

        self.pagina_dashboard = DashboardPage(
            self.session, self.printer_service,
            self.activity_service, self.dashboard_service
        )
        self.pagina_impressoras = PrintersPage(
            self.session, self.printer_service,
            self.company_service, self.technician_service,
            self.activity_service
        )
        self.pagina_os = OSPage(
            self.session, self.printer_service,
            self.activity_service, self.company_service
        )
        self.pagina_clientes = ClientsPage(
            self.session, self.company_service, self.printer_service
        )
        self.pagina_pecas = PartsPage(
            self.session, self.part_service, self.printer_service
        )
        self.pagina_transferencias = TransfersPage(
            self.session, self.printer_service,
            self.activity_service, self.company_service
        )
        self.pagina_tecnicos = TechniciansPage(
            self.session, self.technician_service
        )
        self.pagina_relatorios = ReportsPage(
            self.session, self.printer_service, self.activity_service
        )

        self.content_area.addWidget(self.pagina_dashboard)        # 0
        self.content_area.addWidget(self.pagina_impressoras)      # 1
        self.content_area.addWidget(self.pagina_os)               # 2
        self.content_area.addWidget(self.pagina_clientes)         # 3
        self.content_area.addWidget(self.pagina_pecas)            # 4
        self.content_area.addWidget(self.pagina_transferencias)   # 5
        self.content_area.addWidget(self.pagina_tecnicos)         # 6
        self.content_area.addWidget(self.pagina_relatorios)       # 7

        if self.user.get('perfil') == 'admin':
            self.pagina_config = ConfigPage(
                self.session, self.user_service, self.user
            )
            self.content_area.addWidget(self.pagina_config)       # 8

        # ── Conexões de sinais ─────────────────────────────────
        self.pagina_dashboard.signal_trocar_pagina.connect(self._trocar_pagina)
        self.pagina_clientes.abrir_impressora.connect(self._abrir_impressora_por_patrimonio)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.content_area)
        self._trocar_pagina(0)

    # ── Sidebar helpers ─────────────────────────────────────────
    def _adicionar_label_secao(self, layout, texto):
        lbl = QLabel(texto.upper())
        lbl.setStyleSheet(
            "color: #3a3a5a; font-size: 9px; font-weight: 700;"
            " letter-spacing: 1.2px; padding: 12px 16px 4px;"
            " background: transparent;"
        )
        layout.addWidget(lbl)

    def _adicionar_logo(self, layout):
        import os
        logo_frame = QFrame()
        logo_frame.setStyleSheet("background: transparent; border: none;")
        logo_frame_layout = QHBoxLayout(logo_frame)
        logo_frame_layout.setContentsMargins(14, 18, 14, 14)
        logo_frame_layout.setSpacing(10)

        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "1.PNG")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "1.png")
        if os.path.exists(logo_path):
            from PySide6.QtGui import QPixmap
            logo_img = QLabel()
            pix = QPixmap(logo_path).scaled(34, 34, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_img.setPixmap(pix)
            logo_img.setStyleSheet("background: transparent; border: none;")
            logo_frame_layout.addWidget(logo_img)

        logo_text = QLabel("CONTROLE DE\nIMPRESSORAS PRO")
        logo_text.setStyleSheet(
            "color: #e2e8f0; font-size: 12px; font-weight: 700;"
            " background: transparent; letter-spacing: 0.5px; line-height: 1.3;"
        )
        logo_frame_layout.addWidget(logo_text)
        logo_frame_layout.addStretch()
        layout.addWidget(logo_frame)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #1a1a2a; max-height: 1px; margin: 0 14px;")
        layout.addWidget(sep)

    def _adicionar_card_usuario(self, layout):
        user_frame = QFrame()
        user_frame.setStyleSheet(
            "QFrame { background-color: #141422; border: 1px solid #1e1e30;"
            " border-radius: 8px; margin: 8px 10px 4px; }"
        )
        user_frame_layout = QHBoxLayout(user_frame)
        user_frame_layout.setContentsMargins(10, 8, 10, 8)
        user_frame_layout.setSpacing(8)

        avatar = QLabel(self.user["nome"][:2].upper())
        avatar.setFixedSize(30, 30)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #7c3aed,stop:1 #e94560);"
            " color: white; border-radius: 15px; font-size: 11px; font-weight: 700;"
        )
        user_frame_layout.addWidget(avatar)

        user_info = QVBoxLayout()
        user_info.setSpacing(1)
        user_name = QLabel(self.user["nome"])
        user_name.setStyleSheet("color: #c4c4e0; font-size: 11px; font-weight: 600; background: transparent; border: none;")
        user_info.addWidget(user_name)
        user_role = QLabel(self.user["perfil"].capitalize())
        user_role.setStyleSheet("color: #4a4a6a; font-size: 9px; background: transparent; border: none;")
        user_info.addWidget(user_role)
        user_frame_layout.addLayout(user_info)
        user_frame_layout.addStretch()

        exit_btn = QPushButton("✕")
        exit_btn.setFixedSize(22, 22)
        exit_btn.setCursor(Qt.PointingHandCursor)
        exit_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #4a4a6a; border: none;"
            " font-size: 12px; border-radius: 11px; }"
            " QPushButton:hover { background: #e9456022; color: #e94560; }"
        )
        exit_btn.clicked.connect(self.close)
        user_frame_layout.addWidget(exit_btn)

        layout.addWidget(user_frame)

    def _criar_botao_menu(self, icone, texto):
        btn = QPushButton(f"{icone}  {texto}")
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(38)
        btn.setObjectName("menuBtn")
        btn.setStyleSheet(
            "QPushButton#menuBtn { background: transparent; color: #6b7280; border: none;"
            " text-align: left; font-size: 12px; padding: 7px 12px; border-radius: 8px; font-weight: 500; }"
            " QPushButton#menuBtn:hover { background-color: #1a1a2e; color: #9ca3af; }"
            " QPushButton#menuBtn:checked { background-color: #1e1040; color: #a78bfa; font-weight: 600; }"
        )
        return btn

    # ── Navegação ────────────────────────────────────────────────
    def _trocar_pagina(self, index):
        for i, btn in enumerate(self.menu_buttons):
            btn.setChecked(i == index)
        self.content_area.setCurrentIndex(index)

        # Recarrega dados da página atual
        pagina_atual = self.content_area.currentWidget()
        if hasattr(pagina_atual, 'recarregar'):
            pagina_atual.recarregar()

    # ── Ações ────────────────────────────────────────────────────
    def _abrir_impressora_por_patrimonio(self, patrimonio):
        self._trocar_pagina(1)
        self.pagina_impressoras.filtrar(patrimonio)
        for row in range(self.pagina_impressoras.tabela.rowCount()):
            if self.pagina_impressoras.tabela.item(row, 0).text() == patrimonio:
                self.pagina_impressoras._detalhes(row)
                break

    def carregar_dados(self):
        """Recarrega todas as páginas"""
        for pagina in [
            self.pagina_dashboard, self.pagina_impressoras,
            self.pagina_os, self.pagina_clientes,
            self.pagina_pecas, self.pagina_transferencias,
            self.pagina_tecnicos, self.pagina_relatorios
        ]:
            if hasattr(pagina, 'recarregar'):
                pagina.recarregar()

    # ── Exportação ───────────────────────────────────────────────
    def _exportar_impressoras(self, formato):
        from PySide6.QtWidgets import QFileDialog
        from app.services.relatorio_service import RelatorioService
        from datetime import datetime as dt
        import os

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório",
            f"impressoras_{dt.now().strftime('%Y%m%d')}.{formato}",
            f"{'PDF' if formato == 'pdf' else 'Excel'} (*.{formato})"
        )
        if not filepath:
            return

        printers = self.printer_service.listar_todos()
        try:
            if formato == 'pdf':
                RelatorioService.exportar_impressoras_pdf(printers, filepath)
            else:
                RelatorioService.exportar_impressoras_excel(printers, filepath)
            os.startfile(filepath)
            QMessageBox.information(self, "Sucesso", f"Relatório salvo em:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório: {str(e)}")

    def _exportar_atividades(self, formato):
        from PySide6.QtWidgets import QFileDialog
        from app.services.relatorio_service import RelatorioService
        from datetime import datetime as dt
        import os

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório",
            f"atividades_{dt.now().strftime('%Y%m%d')}.{formato}",
            f"{'PDF' if formato == 'pdf' else 'Excel'} (*.{formato})"
        )
        if not filepath:
            return

        atividades = self.activity_service.listar(limite=500)
        try:
            if formato == 'pdf':
                RelatorioService.exportar_atividades_pdf(atividades, filepath)
            else:
                RelatorioService.exportar_atividades_excel(atividades, filepath)
            os.startfile(filepath)
            QMessageBox.information(self, "Sucesso", f"Relatório salvo em:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório: {str(e)}")
