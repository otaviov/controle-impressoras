from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QLineEdit, QComboBox, QTextEdit, QDialog, QFormLayout,
    QDialogButtonBox, QTabWidget, QGroupBox, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from collections import Counter
from datetime import datetime as dt
from sqlalchemy import func
from models import Printer, Activity, Company, Part, Attachment
import os
from pathlib import Path


class MainWindow(QMainWindow):
    def __init__(self, session, user):
        super().__init__()
        self.session = session
        self.user = user
        self.menu_buttons = []
        self.init_ui()
        self.carregar_dados()
    
    def init_ui(self):
        self.setWindowTitle("Controle de Impressoras Pro")
        self.setMinimumSize(1200, 700)
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet("#sidebar { background-color: #0f3460; border-right: 2px solid #533483; }")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 15, 10, 15)
        sidebar_layout.setSpacing(3)
        
        logo = QLabel("🖨️  CONTROLE DE\n   IMPRESSORAS")
        logo.setStyleSheet("color: #e94560; font-size: 14px; font-weight: bold; background: transparent; padding: 10px 5px;")
        sidebar_layout.addWidget(logo)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #533483; max-height: 1px;")
        sidebar_layout.addWidget(sep)
        sidebar_layout.addSpacing(8)
        
        menus = [("📊", "Dashboard", 0), ("🖨️", "Impressoras", 1), ("📋", "Ordens de Serviço", 2), ("👥", "Empresas/Clientes", 3), ("🔧", "Peças", 4), ("🚚", "Transferências", 5), ("📈", "Relatórios", 6)]
        for icon, text, index in menus:
            btn = self._criar_botao_menu(icon, text)
            btn.clicked.connect(lambda checked, i=index: self._trocar_pagina(i))
            sidebar_layout.addWidget(btn)
            self.menu_buttons.append(btn)
        
        sidebar_layout.addStretch()
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background-color: #533483; max-height: 1px;")
        sidebar_layout.addWidget(sep2)
        sidebar_layout.addSpacing(5)
        
        user_info = QLabel(f"👤 {self.user['nome']}\n🔒 {self.user['perfil']}")
        user_info.setStyleSheet("color: #a0a0b0; font-size: 11px; background: transparent; padding: 5px;")
        sidebar_layout.addWidget(user_info)
        
        btn_sair = QPushButton("🚪 Sair")
        btn_sair.setCursor(Qt.PointingHandCursor)
        btn_sair.setStyleSheet("QPushButton { background: transparent; color: #a0a0b0; border: none; text-align: left; font-size: 12px; padding: 5px; } QPushButton:hover { color: #e94560; }")
        btn_sair.clicked.connect(self.close)
        sidebar_layout.addWidget(btn_sair)
        
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("background-color: #1a1a2e;")
        self.content_area.addWidget(self._criar_pagina_dashboard())
        self.content_area.addWidget(self._criar_pagina_impressoras())
        self.content_area.addWidget(self._criar_pagina_os())
        self.content_area.addWidget(self._criar_pagina_clientes())
        self.content_area.addWidget(self._criar_pagina_pecas())
        self.content_area.addWidget(self._criar_pagina_transferencias())
        self.content_area.addWidget(self._criar_pagina_relatorios())
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.content_area)
        self._trocar_pagina(0)
    
    def _criar_botao_menu(self, icone, texto):
        btn = QPushButton(f"{icone}  {texto}")
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(40)
        btn.setStyleSheet("QPushButton { background: transparent; color: #c0c0d0; border: none; text-align: left; font-size: 13px; padding: 10px 14px; border-radius: 8px; } QPushButton:hover { background-color: #1a1a3e; color: #ffffff; } QPushButton:checked { background-color: #e94560; color: white; font-weight: bold; }")
        return btn
    
    def _trocar_pagina(self, index):
        for i, btn in enumerate(self.menu_buttons):
            btn.setChecked(i == index)
        self.content_area.setCurrentIndex(index)
    
    def _limpar_local(self, texto):
        """Remove prefixos de local"""
        if not texto:
            return ""
        # Remove prefixos (emoji + espaço = 3 chars visuais, mas emojis podem ter tamanhos diferentes)
        for prefix in ["🏢 ", "📍 "]:
            if texto.startswith(prefix):
                # Corta depois do prefixo
                return texto[len(prefix):].strip()
        return texto.strip()
    
    def _criar_card(self, icon, title, value, color, callback=None):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background-color: #0f3460; border-radius: 12px; border: 1px solid #533483; padding: 18px; }} QFrame:hover {{ border-color: {color}; }}")
        card.setMinimumHeight(130)
        
        # Torna clicável
        if callback:
            card.setCursor(Qt.PointingHandCursor)
            card.mousePressEvent = lambda event: callback()
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 28px; background: transparent;")
        layout.addWidget(icon_label)
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 30px; font-weight: bold; background: transparent;")
        value_label.setObjectName("cardValue")
        layout.addWidget(value_label)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #a0a0b0; font-size: 12px; background: transparent;")
        layout.addWidget(title_label)
        return card
    
    def _criar_card_mini(self, icon, title, value, color):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background-color: #0f3460; border-radius: 10px; border: 1px solid #533483; padding: 12px; }} QFrame:hover {{ border-color: {color}; }}")
        card.setMinimumHeight(80)
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px; background: transparent;")
        header.addWidget(icon_label)
        header.addStretch()
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold; background: transparent;")
        value_label.setObjectName("miniValue")
        header.addWidget(value_label)
        layout.addLayout(header)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #a0a0b0; font-size: 10px; background: transparent;")
        layout.addWidget(title_label)
        return card

    def _filtrar_dashboard_status(self, tipo):
        """Abre popup com impressoras filtradas por status"""
        if tipo == "manutencao":
            titulo = "⚠️ Impressoras em Manutenção"
            status_list = ["Em manutenção", "Manutenção", "Aguardando peça", "Parada"]
        elif tipo == "operacional":
            titulo = "✅ Impressoras Operacionais"
            status_list = ["Operacional", "Em uso"]
        else:
            return
        
        impressoras = self.session.query(Printer).filter(
            Printer.status.in_(status_list)
        ).order_by(Printer.patrimonio).all()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(titulo)
        dialog.setMinimumSize(800, 500)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #e0e0e0; font-size: 18px; font-weight: bold; background: transparent; }
            QTableWidget { background-color: #0f3460; color: #e0e0e0; border: 1px solid #533483; border-radius: 10px; gridline-color: #1a1a3e; font-size: 13px; }
            QTableWidget::item { padding: 8px; }
            QHeaderView::section { background-color: #16213e; color: #89b4fa; font-weight: bold; padding: 10px; border: none; border-bottom: 2px solid #e94560; }
            QPushButton { background-color: #e94560; color: white; border: none; border-radius: 8px; padding: 10px 30px; font-size: 14px; font-weight: bold; }
        """)
        
        layout = QVBoxLayout(dialog)
        
        # Título
        lbl_titulo = QLabel(f"{titulo} ({len(impressoras)})")
        layout.addWidget(lbl_titulo)
        layout.addSpacing(10)
        
        # Tabela
        tabela = QTableWidget()
        tabela.setColumnCount(5)
        tabela.setHorizontalHeaderLabels(["Patrimônio", "Modelo", "Status", "Local Atual", "Última Revisão"])
        tabela.setRowCount(len(impressoras))
        
        for i, p in enumerate(impressoras):
            tabela.setItem(i, 0, QTableWidgetItem(p.patrimonio))
            tabela.setItem(i, 1, QTableWidgetItem(p.modelo))
            
            status_item = QTableWidgetItem(p.status)
            if p.status in ["Operacional", "Em uso"]:
                status_item.setForeground(QColor("#a6e3a1"))
            else:
                status_item.setForeground(QColor("#f9e2af"))
            tabela.setItem(i, 2, status_item)
            
            tabela.setItem(i, 3, QTableWidgetItem(p.local_atual or "-"))
            
            # Última manutenção
            ultima = self.session.query(Activity).filter(
                Activity.printer_id == p.id,
                Activity.kind == "MANUTENCAO"
            ).order_by(Activity.event_at.desc()).first()
            rev = ultima.event_at.strftime("%d/%m/%Y") if ultima and ultima.event_at else "Nunca"
            tabela.setItem(i, 4, QTableWidgetItem(rev))
        
        tabela.horizontalHeader().setStretchLastSection(True)
        tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tabela.verticalHeader().setVisible(False)
        tabela.resizeColumnsToContents()
        tabela.cellDoubleClicked.connect(lambda row, col: self._abrir_detalhes_do_popup(row, tabela, dialog))
        layout.addWidget(tabela)
        
        # Botão fechar
        btn_fechar = QPushButton("Fechar")
        btn_fechar.setCursor(Qt.PointingHandCursor)
        btn_fechar.clicked.connect(dialog.accept)
        layout.addWidget(btn_fechar, alignment=Qt.AlignCenter)
        
        dialog.exec()

    def _abrir_detalhes_do_popup(self, row, tabela, parent_dialog):
        """Abre os detalhes de uma impressora a partir do popup"""
        patrimonio = tabela.item(row, 0).text()
        printer = self.session.query(Printer).filter(Printer.patrimonio == patrimonio).first()
        
        if not printer:
            return
        
        # Fecha o popup atual
        parent_dialog.accept()
        
        # Abre os detalhes da impressora
        dialog = QDialog(self)
        dialog.setWindowTitle(f"🖨️ Impressora {printer.patrimonio} - {printer.modelo}")
        dialog.setMinimumSize(750, 550)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #c0c0d0; font-size: 13px; background: transparent; }
            QLineEdit, QTextEdit { background-color: #16213e; color: #e0e0e0; border: 1px solid #313244; border-radius: 6px; padding: 6px; font-size: 13px; }
            QTableWidget { background-color: #0f3460; color: #e0e0e0; border: 1px solid #533483; border-radius: 8px; gridline-color: #1a1a3e; font-size: 12px; }
            QTableWidget::item { padding: 6px; }
            QHeaderView::section { background-color: #16213e; color: #89b4fa; font-weight: bold; padding: 8px; border: none; border-bottom: 1px solid #533483; }
            QPushButton { background-color: #e94560; color: white; border: none; border-radius: 8px; padding: 10px 30px; font-size: 14px; font-weight: bold; }
        """)
        
        layout = QVBoxLayout(dialog)
        
        # Título
        titulo = QLabel(f"🖨️ {printer.patrimonio} - {printer.modelo}")
        titulo.setStyleSheet("color: #e94560; font-size: 18px; font-weight: bold;")
        layout.addWidget(titulo)
        
        # Grid de informações
        grid = QGridLayout()
        grid.setSpacing(10)
        
        campos = [
            ("Status:", printer.status, "Marca:", printer.marca or "-"),
            ("Serial:", printer.serial or "-", "Tipo:", printer.tipo or "-"),
            ("Local:", printer.local_atual or "-", "IP:", printer.ip_rede or "-"),
            ("Técnico:", printer.tecnico or "-", "Última Revisão:", ""),
        ]
        
        # Última revisão
        ultima = self.session.query(Activity).filter(
            Activity.printer_id == printer.id,
            Activity.kind == "MANUTENCAO"
        ).order_by(Activity.event_at.desc()).first()
        rev = ultima.event_at.strftime("%d/%m/%Y") if ultima and ultima.event_at else "Nunca"
        campos[3] = ("Técnico:", printer.tecnico or "-", "Última Revisão:", rev)
        
        for r, (l1, v1, l2, v2) in enumerate(campos):
            grid.addWidget(QLabel(l1), r, 0)
            val1 = QLabel(v1)
            val1.setStyleSheet("font-weight: bold;")
            grid.addWidget(val1, r, 1)
            grid.addWidget(QLabel(l2), r, 2)
            val2 = QLabel(v2)
            val2.setStyleSheet("font-weight: bold;")
            grid.addWidget(val2, r, 3)
        
        layout.addLayout(grid)
        
        # Observação
        if printer.observacao:
            layout.addWidget(QLabel("Observação:"))
            obs = QLabel(printer.observacao)
            obs.setWordWrap(True)
            layout.addWidget(obs)
        
        # Peças faltantes
        if printer.pecas_faltantes:
            layout.addWidget(QLabel("⚠️ Peças Faltantes:"))
            pecas = QLabel(printer.pecas_faltantes)
            pecas.setWordWrap(True)
            pecas.setStyleSheet("color: #f9e2af;")
            layout.addWidget(pecas)
        
        # Histórico resumido
        atividades = self.session.query(Activity).filter(
            Activity.printer_id == printer.id
        ).order_by(Activity.event_at.desc()).limit(5).all()
        
        if atividades:
            layout.addWidget(QLabel(f"📜 Últimas {len(atividades)} atividades:"))
            hist_tabela = QTableWidget()
            hist_tabela.setColumnCount(3)
            hist_tabela.setHorizontalHeaderLabels(["Data", "Tipo", "Descrição"])
            hist_tabela.setRowCount(len(atividades))
            for i, a in enumerate(atividades):
                hist_tabela.setItem(i, 0, QTableWidgetItem(a.event_at.strftime("%d/%m/%Y %H:%M") if a.event_at else "-"))
                tipo = "🔧" if a.kind == "MANUTENCAO" else "🚚"
                hist_tabela.setItem(i, 1, QTableWidgetItem(tipo))
                hist_tabela.setItem(i, 2, QTableWidgetItem(a.notes or "-"))
            hist_tabela.horizontalHeader().setStretchLastSection(True)
            hist_tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
            hist_tabela.verticalHeader().setVisible(False)
            hist_tabela.setMaximumHeight(150)
            layout.addWidget(hist_tabela)
        
        # Botão fechar
        btn = QPushButton("Fechar")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn, alignment=Qt.AlignCenter)
        
        dialog.exec()
    
    def _atualizar_card(self, card, valor):
        value_label = card.findChild(QLabel, "cardValue")
        if value_label:
            value_label.setText(valor)
    
    def _atualizar_card_mini(self, card, valor):
        value_label = card.findChild(QLabel)
        if value_label and hasattr(value_label, 'objectName'):
            if 'miniValue' in value_label.objectName():
                value_label.setText(valor)
                return
        # Procura todos os QLabel
        for child in card.findChildren(QLabel):
            if 'miniValue' in (child.objectName() or ''):
                child.setText(valor)
                return
    
    def _criar_pagina_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 25, 25, 25)
        titulo = QLabel("📊 Dashboard")
        titulo.setStyleSheet("color: #e94560; font-size: 22px; font-weight: bold; background: transparent;")
        layout.addWidget(titulo)
        sub = QLabel("Visão geral do sistema")
        sub.setStyleSheet("color: #a0a0b0; font-size: 13px; background: transparent;")
        layout.addWidget(sub)
        layout.addSpacing(15)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        self.card_total = self._criar_card("🖨️", "Total Impressoras", "0", "#89b4fa", lambda: self._trocar_pagina(1))
        self.card_manut = self._criar_card("⚠️", "Em Manutenção", "0", "#f9e2af", lambda: self._filtrar_dashboard_status("manutencao"))
        self.card_op = self._criar_card("✅", "Operacionais", "0", "#a6e3a1", lambda: self._filtrar_dashboard_status("operacional"))
        self.card_os = self._criar_card("📋", "Atividades", "0", "#cba6f7", lambda: self._trocar_pagina(2))
        cards_layout.addWidget(self.card_total)
        cards_layout.addWidget(self.card_manut)
        cards_layout.addWidget(self.card_op)
        cards_layout.addWidget(self.card_os)
        layout.addLayout(cards_layout)
        layout.addStretch()
        return page


    
    def _criar_pagina_impressoras(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        header = QHBoxLayout()
        titulo = QLabel("🖨️ Impressoras")
        titulo.setStyleSheet("color: #e94560; font-size: 20px; font-weight: bold; background: transparent;")
        header.addWidget(titulo)
        header.addStretch()
        btn_nova = QPushButton("➕ Nova Impressora")
        btn_nova.setCursor(Qt.PointingHandCursor)
        btn_nova.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #1a1a2e; border: none; border-radius: 6px; padding: 8px 16px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #94d89f; }")
        btn_nova.clicked.connect(self._nova_impressora)
        header.addWidget(btn_nova)
        btn_atualizar = QPushButton("🔄 Atualizar")
        btn_atualizar.setCursor(Qt.PointingHandCursor)
        btn_atualizar.setStyleSheet("QPushButton { background-color: #0f3460; color: #89b4fa; border: 1px solid #533483; border-radius: 6px; padding: 8px 16px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #1a1a4e; }")
        btn_atualizar.clicked.connect(self.carregar_dados)
        header.addWidget(btn_atualizar)
        layout.addLayout(header)
        layout.addSpacing(10)
        busca_layout = QHBoxLayout()
        busca_label = QLabel("🔍")
        busca_label.setStyleSheet("font-size: 16px; background: transparent;")
        busca_layout.addWidget(busca_label)
        self.busca_input = QLineEdit()
        self.busca_input.setPlaceholderText("Buscar por patrimônio, modelo, serial ou local...")
        self.busca_input.setMinimumHeight(36)
        self.busca_input.setStyleSheet("QLineEdit { background-color: #0f3460; color: #ffffff; border: 2px solid #533483; border-radius: 8px; padding: 8px 14px; font-size: 13px; } QLineEdit:focus { border-color: #89b4fa; }")
        self.busca_input.textChanged.connect(self.filtrar_impressoras)
        busca_layout.addWidget(self.busca_input)
        layout.addLayout(busca_layout)
        layout.addSpacing(10)
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(7)
        self.tabela.setHorizontalHeaderLabels(["Patrimônio", "Modelo", "Serial", "Marca", "Status", "Local Atual", "Atividades"])
        self.tabela.setStyleSheet("QTableWidget { background-color: #0f3460; color: #e0e0e0; border: 1px solid #533483; border-radius: 10px; gridline-color: #1a1a3e; selection-background-color: #533483; font-size: 13px; } QTableWidget::item { padding: 8px; } QTableWidget::item:hover { background-color: #1a1a4e; } QTableWidget::item:selected { background-color: #533483; color: white; } QHeaderView::section { background-color: #16213e; color: #89b4fa; font-weight: bold; padding: 10px 8px; border: none; border-bottom: 2px solid #e94560; font-size: 12px; }")
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.cellDoubleClicked.connect(self._abrir_detalhes_impressora)
        layout.addWidget(self.tabela)
        return page
    
    def _nova_impressora(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nova Impressora")
        dialog.setFixedSize(500, 480)
        dialog.setStyleSheet("QDialog { background-color: #1a1a2e; color: #e0e0e0; } QLabel { color: #c0c0d0; font-size: 12px; } QLineEdit, QTextEdit { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; } QComboBox { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; } QPushButton { background-color: #e94560; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }")
        layout = QFormLayout(dialog)
        layout.setSpacing(8)
        
        patrimonio_input = QLineEdit()
        patrimonio_input.setPlaceholderText("Número do patrimônio")
        layout.addRow("Patrimônio *:", patrimonio_input)
        modelo_input = QLineEdit()
        modelo_input.setPlaceholderText("Modelo da impressora")
        layout.addRow("Modelo:", modelo_input)
        marca_input = QLineEdit()
        marca_input.setPlaceholderText("Marca (HP, Brother, etc)")
        layout.addRow("Marca:", marca_input)
        serial_input = QLineEdit()
        serial_input.setPlaceholderText("Número de série")
        layout.addRow("Serial:", serial_input)
        
        tipo_combo = QComboBox()
        tipo_combo.addItems(["", "Laser", "Jato de tinta", "Multifuncional"])
        layout.addRow("Tipo:", tipo_combo)
        
        local_combo = QComboBox()
        local_combo.setEditable(True)
        local_combo.addItem("")
        empresas = self.session.query(Company).order_by(Company.nome).all()
        for emp in empresas:
            local_combo.addItem(f"🏢 {emp.nome}")
        locais_existentes = self.session.query(Printer.local_atual).filter(Printer.local_atual != "").distinct().order_by(Printer.local_atual).all()
        for loc in locais_existentes:
            nome = loc[0]
            if nome and nome not in [emp.nome for emp in empresas]:
                local_combo.addItem(f"📍 {nome}")
        local_combo.setCurrentText("")
        layout.addRow("Local Atual:", local_combo)
        
        status_combo = QComboBox()
        status_combo.addItems(["Operacional", "Em uso", "Em manutenção", "Manutenção", "Parada", "Aguardando peça", "Sucata"])
        layout.addRow("Status:", status_combo)
        ip_input = QLineEdit()
        ip_input.setPlaceholderText("192.168.0.100")
        layout.addRow("IP Rede:", ip_input)
        obs_input = QTextEdit()
        obs_input.setMaximumHeight(60)
        obs_input.setPlaceholderText("Observações gerais...")
        layout.addRow("Observação:", obs_input)
        
        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.accepted.connect(lambda: self._salvar_impressora(dialog, patrimonio_input, modelo_input, marca_input, serial_input, tipo_combo, local_combo, status_combo, ip_input, obs_input))
        botoes.rejected.connect(dialog.reject)
        layout.addRow(botoes)
        dialog.exec()
    
    def _salvar_impressora(self, dialog, pat, mod, marca, serial, tipo, local, status, ip, obs):
        patrimonio = pat.text().strip()
        if not patrimonio:
            return
        
        # Verifica se já existe
        existente = self.session.query(Printer).filter(Printer.patrimonio == patrimonio).first()
        if existente:
            QMessageBox.warning(dialog, "Patrimônio Duplicado", 
                f"Já existe uma impressora com o patrimônio '{patrimonio}'!\n\n"
                f"Modelo: {existente.modelo}\n"
                f"Local: {existente.local_atual or 'N/A'}\n"
                f"Status: {existente.status or 'N/A'}")
            return
        
        from models import simple_uid
        printer = Printer(id=simple_uid(), patrimonio=patrimonio, modelo=mod.text().strip(), marca=marca.text().strip(), serial=serial.text().strip(), tipo=tipo.currentText(), local_atual=self._limpar_local(local.currentText()), status=status.currentText(), ip_rede=ip.text().strip(), observacao=obs.toPlainText().strip())
        self.session.add(printer)
        self.session.commit()
        self.carregar_dados()
        dialog.accept()
    
    def _abrir_detalhes_impressora(self, row, col):
        patrimonio = self.tabela.item(row, 0).text()
        printer = self.session.query(Printer).filter(Printer.patrimonio == patrimonio).first()
        if not printer:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"🖨️ Impressora {printer.patrimonio} - {printer.modelo}")
        dialog.setMinimumSize(750, 550)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #c0c0d0; font-size: 12px; background: transparent; }
            QLineEdit, QTextEdit { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 6px; font-size: 13px; }
            QLineEdit[readOnly="true"], QTextEdit[readOnly="true"] { background-color: #16213e; color: #a0a0b0; border: 1px solid #313244; }
            QComboBox { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 6px; }
            QComboBox:disabled { background-color: #16213e; color: #a0a0b0; }
            QTableWidget { background-color: #0f3460; color: #e0e0e0; border: 1px solid #533483; border-radius: 8px; gridline-color: #1a1a3e; font-size: 12px; }
            QTableWidget::item { padding: 6px; }
            QHeaderView::section { background-color: #16213e; color: #89b4fa; font-weight: bold; padding: 8px; border: none; border-bottom: 1px solid #533483; }
            QTabWidget::pane { border: 1px solid #533483; background-color: #1a1a2e; border-radius: 8px; }
            QTabBar::tab { background-color: #0f3460; color: #a0a0b0; padding: 10px 20px; border: 1px solid #533483; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; font-size: 13px; }
            QTabBar::tab:selected { background-color: #1a1a2e; color: #e94560; font-weight: bold; }
            QPushButton { border: none; border-radius: 8px; padding: 10px 20px; font-size: 13px; font-weight: bold; }
        """)
        
        layout = QVBoxLayout(dialog)
        tabs = QTabWidget()
        
        # ==================== TAB DADOS ====================
        tab_dados = QWidget()
        dados_layout = QGridLayout(tab_dados)
        dados_layout.setSpacing(8)
        dados_layout.setContentsMargins(15, 15, 15, 15)
        
        # Patrimônio (agora editável quando em modo edição)
        dados_layout.addWidget(QLabel("Patrimônio:"), 0, 0)
        pat_input = QLineEdit(printer.patrimonio)
        pat_input.setReadOnly(True)
        pat_input.setStyleSheet("QLineEdit { background-color: #16213e; color: #a0a0b0; border: 1px solid #313244; }")
        dados_layout.addWidget(pat_input, 0, 1)
        
        # Status
        dados_layout.addWidget(QLabel("Status:"), 0, 2)
        status_combo = QComboBox()
        status_combo.addItems(["Operacional", "Em uso", "Em manutenção", "Manutenção", "Parada", "Aguardando peça", "Sucata"])
        status_combo.setCurrentText(printer.status or "Operacional")
        status_combo.setEnabled(False)
        dados_layout.addWidget(status_combo, 0, 3)
        
        # Modelo
        dados_layout.addWidget(QLabel("Modelo:"), 1, 0)
        modelo_input = QLineEdit(printer.modelo or "")
        modelo_input.setReadOnly(True)
        dados_layout.addWidget(modelo_input, 1, 1)
        
        # Marca
        dados_layout.addWidget(QLabel("Marca:"), 1, 2)
        marca_input = QLineEdit(printer.marca or "")
        marca_input.setReadOnly(True)
        dados_layout.addWidget(marca_input, 1, 3)
        
        # Serial
        dados_layout.addWidget(QLabel("Serial:"), 2, 0)
        serial_input = QLineEdit(printer.serial or "")
        serial_input.setReadOnly(True)
        dados_layout.addWidget(serial_input, 2, 1)
        
        # Tipo
        dados_layout.addWidget(QLabel("Tipo:"), 2, 2)
        tipo_combo = QComboBox()
        tipo_combo.addItems(["", "Laser", "Jato de tinta", "Multifuncional"])
        tipo_combo.setCurrentText(printer.tipo or "")
        tipo_combo.setEnabled(False)
        dados_layout.addWidget(tipo_combo, 2, 3)
        
        # Local Atual
        dados_layout.addWidget(QLabel("Local Atual:"), 3, 0)
        local_combo = QComboBox()
        local_combo.setEditable(True)
        local_combo.addItem("")
        empresas = self.session.query(Company).order_by(Company.nome).all()
        for emp in empresas:
            local_combo.addItem(f"🏢 {emp.nome}")
        locais = self.session.query(Printer.local_atual).filter(Printer.local_atual != "").distinct().order_by(Printer.local_atual).all()
        for loc in locais:
            nome = loc[0]
            if nome and nome not in [e.nome for e in empresas]:
                local_combo.addItem(f"📍 {nome}")
        atual = printer.local_atual or ""
        idx = local_combo.findText(f"🏢 {atual}")
        if idx < 0:
            idx = local_combo.findText(f"📍 {atual}")
        if idx >= 0:
            local_combo.setCurrentIndex(idx)
        else:
            local_combo.setCurrentText(atual)
        local_combo.setEnabled(False)
        dados_layout.addWidget(local_combo, 3, 1)
        
        # IP Rede
        dados_layout.addWidget(QLabel("IP Rede:"), 3, 2)
        ip_input = QLineEdit(printer.ip_rede or "")
        ip_input.setReadOnly(True)
        dados_layout.addWidget(ip_input, 3, 3)
        
        # Técnico
        dados_layout.addWidget(QLabel("Técnico:"), 4, 0)
        tec_input = QLineEdit(printer.tecnico or "")
        tec_input.setReadOnly(True)
        dados_layout.addWidget(tec_input, 4, 1)
        
        # Última Revisão
        # Busca a data da última manutenção
        ultima_manutencao = self.session.query(Activity).filter(
            Activity.printer_id == printer.id,
            Activity.kind == "MANUTENCAO"
        ).order_by(Activity.event_at.desc()).first()
        
        dados_layout.addWidget(QLabel("Última Revisão:"), 4, 2)
        rev_text = ""
        if ultima_manutencao and ultima_manutencao.event_at:
            rev_text = ultima_manutencao.event_at.strftime("%d/%m/%Y")
        elif printer.proxima_revisao:
            rev_text = printer.proxima_revisao.strftime("%d/%m/%Y")
        rev_input = QLineEdit(rev_text)
        rev_input.setPlaceholderText("dd/mm/aaaa")
        rev_input.setReadOnly(True)
        dados_layout.addWidget(rev_input, 4, 3)
        
        # Observação
        dados_layout.addWidget(QLabel("Observação:"), 5, 0)
        obs_input = QTextEdit()
        obs_input.setMaximumHeight(80)
        obs_input.setPlainText(printer.observacao or "")
        obs_input.setReadOnly(True)
        dados_layout.addWidget(obs_input, 5, 1, 1, 3)
        
        # Peças Faltantes
        lbl_pecas = QLabel("Peças Faltantes:")
        lbl_pecas.setStyleSheet("color: #f9e2af; font-weight: bold;")
        dados_layout.addWidget(lbl_pecas, 6, 0)
        pecas_input = QTextEdit()
        pecas_input.setMaximumHeight(60)
        pecas_input.setPlainText(printer.pecas_faltantes or "")
        pecas_input.setReadOnly(True)
        dados_layout.addWidget(pecas_input, 6, 1, 1, 3)
        
        # Corrige labels
        for i in range(dados_layout.count()):
            item = dados_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if isinstance(w, QLabel) and w.text().endswith(":") and "Peças" not in w.text():
                    w.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 12px;")
        
        tabs.addTab(tab_dados, "📋 Dados Gerais")
        
        # ==================== TAB HISTÓRICO ====================
        tab_historico = QWidget()
        hist_layout = QVBoxLayout(tab_historico)
        atividades = self.session.query(Activity).filter(Activity.printer_id == printer.id).order_by(Activity.event_at.desc()).all()
        hist_label = QLabel(f"Total de atividades: {len(atividades)}")
        hist_label.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 13px;")
        hist_layout.addWidget(hist_label)
        
        hist_tabela = QTableWidget()
        hist_tabela.setColumnCount(6)
        hist_tabela.cellDoubleClicked.connect(lambda row, col: self._editar_atividade(row, atividades, printer, dialog))
        hist_tabela.setHorizontalHeaderLabels(["Data", "Tipo", "Descrição", "Peças", "Origem", "Destino"])
        hist_tabela.setRowCount(len(atividades))
        for i, a in enumerate(atividades):
            hist_tabela.setItem(i, 0, QTableWidgetItem(a.event_at.strftime("%d/%m/%Y %H:%M") if a.event_at else "-"))
            tipo = "🔧 Manutenção" if a.kind == "MANUTENCAO" else "🚚 Movimentação"
            tipo_item = QTableWidgetItem(tipo)
            tipo_item.setForeground(QColor("#f9e2af") if a.kind == "MANUTENCAO" else QColor("#89b4fa"))
            hist_tabela.setItem(i, 1, tipo_item)
            hist_tabela.setItem(i, 2, QTableWidgetItem(a.notes or "-"))
            hist_tabela.setItem(i, 3, QTableWidgetItem(a.parts_used or "-"))
            hist_tabela.setItem(i, 4, QTableWidgetItem(a.from_location or "-"))
            hist_tabela.setItem(i, 5, QTableWidgetItem(a.to_location or "-"))
        hist_tabela.horizontalHeader().setStretchLastSection(True)
        hist_tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        hist_tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        hist_tabela.verticalHeader().setVisible(False)
        hist_tabela.resizeColumnsToContents()
        hist_layout.addWidget(hist_tabela)
        tabs.addTab(tab_historico, "📜 Histórico")
        
        layout.addWidget(tabs)
        
        # ==================== BOTÕES ====================
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # Botão EDITAR (só aparece no modo leitura)
        btn_editar = QPushButton("✏️ Editar")
        btn_editar.setCursor(Qt.PointingHandCursor)
        btn_editar.setStyleSheet("QPushButton { background-color: #f9e2af; color: #1a1a2e; border: none; border-radius: 8px; padding: 10px 20px; font-size: 13px; font-weight: bold; } QPushButton:hover { background-color: #f5d78c; }")
        
        # Botão SALVAR (só aparece no modo edição)
        btn_salvar = QPushButton("💾 Salvar Alterações")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #1a1a2e; border: none; border-radius: 8px; padding: 10px 20px; font-size: 13px; font-weight: bold; } QPushButton:hover { background-color: #94d89f; }")
        btn_salvar.setVisible(False)
        
        # Botão CANCELAR (só aparece no modo edição)
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet("QPushButton { background-color: #f38ba8; color: #1a1a2e; border: none; border-radius: 8px; padding: 10px 20px; font-size: 13px; font-weight: bold; } QPushButton:hover { background-color: #eb7a94; }")
        btn_cancelar.setVisible(False)
        
        # Botão FECHAR
        btn_fechar = QPushButton("Fechar")
        btn_fechar.setCursor(Qt.PointingHandCursor)
        btn_fechar.setStyleSheet("QPushButton { background-color: #e94560; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-size: 13px; font-weight: bold; } QPushButton:hover { background-color: #d63850; }")
        btn_fechar.clicked.connect(dialog.accept)
        
        # Lista de widgets para habilitar/desabilitar
        widgets_editaveis = [pat_input, status_combo, modelo_input, marca_input, serial_input, tipo_combo, local_combo, ip_input, tec_input, rev_input, obs_input, pecas_input]
        
        def entrar_modo_edicao():
            btn_editar.setVisible(False)
            btn_salvar.setVisible(True)
            btn_cancelar.setVisible(True)
            for w in widgets_editaveis:
                if isinstance(w, QLineEdit):
                    w.setReadOnly(False)
                    w.setStyleSheet("QLineEdit { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 6px; font-size: 13px; }")
                elif isinstance(w, QTextEdit):
                    w.setReadOnly(False)
                    w.setStyleSheet("QTextEdit { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 6px; font-size: 13px; }")
                elif isinstance(w, QComboBox):
                    w.setEnabled(True)
        
        def sair_modo_edicao():
            btn_editar.setVisible(True)
            btn_salvar.setVisible(False)
            btn_cancelar.setVisible(False)
            for w in widgets_editaveis:
                if isinstance(w, QLineEdit):
                    w.setReadOnly(True)
                    w.setStyleSheet("QLineEdit { background-color: #16213e; color: #a0a0b0; border: 1px solid #313244; }")
                elif isinstance(w, QTextEdit):
                    w.setReadOnly(True)
                    w.setStyleSheet("QTextEdit { background-color: #16213e; color: #a0a0b0; border: 1px solid #313244; }")
                elif isinstance(w, QComboBox):
                    w.setEnabled(False)
        
        btn_editar.clicked.connect(entrar_modo_edicao)
        btn_cancelar.clicked.connect(sair_modo_edicao)
        btn_salvar.clicked.connect(lambda: self._salvar_edicao_impressora(dialog, printer, pat_input, status_combo, modelo_input, marca_input, serial_input, tipo_combo, local_combo, ip_input, tec_input, rev_input, obs_input, pecas_input, sair_modo_edicao))
        
        # Ordem dos botões: Editar | Salvar | Cancelar | Fechar
        btn_layout.addWidget(btn_editar)
        btn_layout.addWidget(btn_salvar)
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_fechar)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()


    def _salvar_edicao_impressora(self, dialog, printer, pat_input, status, modelo, marca, serial, tipo, local, ip, tecnico, revisao, obs, pecas, callback=None):
        # Atualiza patrimônio
        novo_pat = pat_input.text().strip()
        if novo_pat and novo_pat != printer.patrimonio:
            # Verifica se já existe
            existente = self.session.query(Printer).filter(Printer.patrimonio == novo_pat).first()
            if existente:
                QMessageBox.warning(dialog, "Patrimônio Duplicado",
                    f"Já existe uma impressora com o patrimônio '{novo_pat}'!")
                return
            printer.patrimonio = novo_pat
        
        printer.status = status.currentText()
        printer.modelo = modelo.text().strip()
        printer.marca = marca.text().strip()
        printer.serial = serial.text().strip()
        printer.tipo = tipo.currentText()
        printer.local_atual = self._limpar_local(local.currentText())
        printer.ip_rede = ip.text().strip()
        printer.tecnico = tecnico.text().strip()
        
        rev_text = revisao.text().strip()
        if rev_text:
            try:
                printer.proxima_revisao = dt.strptime(rev_text, "%d/%m/%Y")
            except:
                pass
        else:
            printer.proxima_revisao = None
        
        printer.observacao = obs.toPlainText().strip()
        printer.pecas_faltantes = pecas.toPlainText().strip()
        
        self.session.commit()
        self.carregar_dados()
        if callback:
            callback()

    def _criar_pagina_os(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        header = QHBoxLayout()
        titulo = QLabel("📋 Ordens de Serviço / Atividades")
        titulo.setStyleSheet("color: #e94560; font-size: 20px; font-weight: bold; background: transparent;")
        header.addWidget(titulo)
        header.addStretch()
        
        # BOTÃO NOVA OS
        btn_nova_os = QPushButton("➕ Nova OS")
        btn_nova_os.setCursor(Qt.PointingHandCursor)
        btn_nova_os.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #1a1a2e; border: none; border-radius: 6px; padding: 8px 16px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #94d89f; }")
        btn_nova_os.clicked.connect(self._nova_os)
        header.addWidget(btn_nova_os)
        
        for texto, tipo in [("🔧 Manutenções", "MANUTENCAO"), ("🚚 Movimentações", "MOVIMENTACAO"), ("📋 Todas", "TODAS")]:
            btn = QPushButton(texto)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("QPushButton { background-color: #0f3460; color: #89b4fa; border: 1px solid #533483; border-radius: 6px; padding: 6px 12px; font-size: 11px; } QPushButton:hover { background-color: #1a1a4e; }")
            btn.clicked.connect(lambda checked, t=tipo: self._filtrar_os(t))
            header.addWidget(btn)
        
        btn_atualizar = QPushButton("🔄 Atualizar")
        btn_atualizar.setCursor(Qt.PointingHandCursor)
        btn_atualizar.setStyleSheet("QPushButton { background-color: #e94560; color: white; border: none; border-radius: 6px; padding: 6px 12px; font-size: 11px; font-weight: bold; } QPushButton:hover { background-color: #d63850; }")
        btn_atualizar.clicked.connect(lambda: self._carregar_tabela_os())
        header.addWidget(btn_atualizar)
        layout.addLayout(header)
        layout.addSpacing(10)

        # Buscar e filtro
        busca_layout = QHBoxLayout()
        busca_label = QLabel("🔍")
        busca_layout.addWidget(busca_label)

        self.busca_os_input = QLineEdit()
        self.busca_os_input.setPlaceholderText("Buscar por patrimônio, descrição, peças, origem ou destino...")
        self.busca_os_input.setMinimumHeight(32)
        self.busca_os_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f3460; color: #ffffff;
                border: 2px solid #533483; border-radius: 8px;
                padding: 6px 12px; font-size: 13px;
            }
            QLineEdit:focus { border-color: #89b4fa; }
        """)
        self.busca_os_input.textChanged.connect(self._filtrar_os_busca)
        busca_layout.addWidget(self.busca_os_input)
        
        layout.addLayout(busca_layout)
        layout.addSpacing(8)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(10)
        self.card_total_os = self._criar_card_mini_clicavel("📋", "Total OS", "0", "#89b4fa", "TODAS")
        self.card_em_andamento = self._criar_card_mini_clicavel("🔄", "Em Andamento", "0", "#f9e2af", "Em Andamento")
        self.card_pendentes = self._criar_card_mini_clicavel("⏳", "Pendentes", "0", "#f38ba8", "Pendente")
        self.card_concluidas = self._criar_card_mini_clicavel("✅", "Concluídas", "0", "#a6e3a1", "Concluida")
        cards_layout.addWidget(self.card_total_os)
        cards_layout.addWidget(self.card_em_andamento)
        cards_layout.addWidget(self.card_pendentes)
        cards_layout.addWidget(self.card_concluidas)
        layout.addLayout(cards_layout)
        layout.addSpacing(10)
        self.tabela_os = QTableWidget()
        self.tabela_os.setColumnCount(8)
        self.tabela_os.setHorizontalHeaderLabels(["Data/Hora", "Patrimônio", "Tipo", "Descrição", "Peças", "Origem", "Destino", "Técnico"])
        self.tabela_os.setStyleSheet("QTableWidget { background-color: #0f3460; color: #e0e0e0; border: 1px solid #533483; border-radius: 10px; gridline-color: #1a1a3e; selection-background-color: #533483; font-size: 12px; } QTableWidget::item { padding: 6px; } QTableWidget::item:hover { background-color: #1a1a4e; } QTableWidget::item:selected { background-color: #533483; color: white; } QHeaderView::section { background-color: #16213e; color: #89b4fa; font-weight: bold; padding: 8px 6px; border: none; border-bottom: 2px solid #e94560; font-size: 11px; }")
        self.tabela_os.horizontalHeader().setStretchLastSection(True)
        self.tabela_os.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela_os.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela_os.verticalHeader().setVisible(False)
        layout.addWidget(self.tabela_os)
        self.tabela_os.cellDoubleClicked.connect(self._editar_atividade_os)
        self._carregar_tabela_os()
        self._atualizar_cards_os()
        return page

    def _criar_card_mini_clicavel(self, icon, title, value, color, status_filtro):
        """Cria um card mini que ao clicar filtra a tabela de OS"""
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background-color: #0f3460; border-radius: 10px; border: 1px solid #533483; padding: 12px; }} QFrame:hover {{ border-color: {color}; }}")
        card.setMinimumHeight(80)
        card.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px; background: transparent;")
        header.addWidget(icon_label)
        header.addStretch()
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold; background: transparent;")
        value_label.setObjectName("miniValue_" + status_filtro)
        header.addWidget(value_label)
        layout.addLayout(header)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #a0a0b0; font-size: 10px; background: transparent;")
        layout.addWidget(title_label)
        
        # Guarda referência
        if status_filtro == "TODAS":
            self.card_total_os = card
        elif status_filtro == "Em Andamento":
            self.card_em_andamento = card
        elif status_filtro == "Pendente":
            self.card_pendentes = card
        elif status_filtro == "Concluida":
            self.card_concluidas = card
        
        # Conecta evento de clique
        def on_click(event):
            self._filtrar_os_por_status(status_filtro)
            event.accept()  # Impede propagação
        
        card.mousePressEvent = on_click
        return card

    def _filtrar_os_por_status(self, status):
        """Filtra a tabela de OS por status"""
        if status == "TODAS":
            self._carregar_tabela_os()
        else:
            query = self.session.query(Activity).order_by(Activity.event_at.desc())
            query = query.filter(Activity.status_atividade.in_([status, status.lower(), status.capitalize()]))
            atividades = query.limit(200).all()
            
            self.tabela_os.setRowCount(len(atividades))
            for i, a in enumerate(atividades):
                self.tabela_os.setItem(i, 0, QTableWidgetItem(a.event_at.strftime("%d/%m/%Y %H:%M") if a.event_at else "-"))
                printer = self.session.query(Printer).filter(Printer.id == a.printer_id).first()
                self.tabela_os.setItem(i, 1, QTableWidgetItem(printer.patrimonio if printer else "?"))
                if a.kind == "MANUTENCAO":
                    tipo_texto = "🔧 Manutenção"
                    cor = QColor("#f9e2af")
                else:
                    tipo_texto = "🚚 Movimentação"
                    cor = QColor("#89b4fa")
                tipo_item = QTableWidgetItem(tipo_texto)
                tipo_item.setForeground(cor)
                self.tabela_os.setItem(i, 2, tipo_item)
                self.tabela_os.setItem(i, 3, QTableWidgetItem(a.notes or "-"))
                self.tabela_os.setItem(i, 4, QTableWidgetItem(a.parts_used or "-"))
                self.tabela_os.setItem(i, 5, QTableWidgetItem(a.from_location or "-"))
                self.tabela_os.setItem(i, 6, QTableWidgetItem(a.to_location or "-"))
                self.tabela_os.setItem(i, 7, QTableWidgetItem("-"))
            
            header = self.tabela_os.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.Stretch)
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(7, QHeaderView.ResizeToContents)

    def _filtrar_os_busca(self, texto):
        """Filtra a tabela de OS por patrimônio"""
        if not texto.strip():
            self._carregar_tabela_os()
            return
        
        query = self.session.query(Activity).order_by(Activity.event_at.desc())
        
        # Busca impressoras que contenham o texto no patrimônio
        printers = self.session.query(Printer).filter(
            Printer.patrimonio.like(f"%{texto}%")
        ).all()
        
        printer_ids = [p.id for p in printers]
        
        if printer_ids:
            query = query.filter(Activity.printer_id.in_(printer_ids))
        else:
            query = query.filter(Activity.printer_id == "NENHUM")  # Força vazio
        
        atividades = query.limit(200).all()
        
        self.tabela_os.setRowCount(len(atividades))
        for i, a in enumerate(atividades):
            self.tabela_os.setItem(i, 0, QTableWidgetItem(a.event_at.strftime("%d/%m/%Y %H:%M") if a.event_at else "-"))
            printer = self.session.query(Printer).filter(Printer.id == a.printer_id).first()
            self.tabela_os.setItem(i, 1, QTableWidgetItem(printer.patrimonio if printer else "?"))
            if a.kind == "MANUTENCAO":
                tipo_texto = "🔧 Manutenção"
                cor = QColor("#f9e2af")
            else:
                tipo_texto = "🚚 Movimentação"
                cor = QColor("#89b4fa")
            tipo_item = QTableWidgetItem(tipo_texto)
            tipo_item.setForeground(cor)
            self.tabela_os.setItem(i, 2, tipo_item)
            self.tabela_os.setItem(i, 3, QTableWidgetItem(a.notes or "-"))
            self.tabela_os.setItem(i, 4, QTableWidgetItem(a.parts_used or "-"))
            self.tabela_os.setItem(i, 5, QTableWidgetItem(a.from_location or "-"))
            self.tabela_os.setItem(i, 6, QTableWidgetItem(a.to_location or "-"))
            self.tabela_os.setItem(i, 7, QTableWidgetItem("-"))
        
        header = self.tabela_os.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
    
    def _carregar_tabela_os(self, filtro_tipo=None):
        query = self.session.query(Activity).order_by(Activity.event_at.desc())
        if filtro_tipo and filtro_tipo != "TODAS":
            query = query.filter(Activity.kind == filtro_tipo)
        atividades = query.limit(200).all()
        self.tabela_os.setRowCount(len(atividades))
        for i, a in enumerate(atividades):
            self.tabela_os.setItem(i, 0, QTableWidgetItem(a.event_at.strftime("%d/%m/%Y %H:%M") if a.event_at else "-"))
            printer = self.session.query(Printer).filter(Printer.id == a.printer_id).first()
            self.tabela_os.setItem(i, 1, QTableWidgetItem(printer.patrimonio if printer else "?"))
            if a.kind == "MANUTENCAO":
                tipo_texto = "🔧 Manutenção"
                cor = QColor("#f9e2af")
            else:
                tipo_texto = "🚚 Movimentação"
                cor = QColor("#89b4fa")
            tipo_item = QTableWidgetItem(tipo_texto)
            tipo_item.setForeground(cor)
            self.tabela_os.setItem(i, 2, tipo_item)
            self.tabela_os.setItem(i, 3, QTableWidgetItem(a.notes or "-"))
            self.tabela_os.setItem(i, 4, QTableWidgetItem(a.parts_used or "-"))
            self.tabela_os.setItem(i, 5, QTableWidgetItem(a.from_location or "-"))
            self.tabela_os.setItem(i, 6, QTableWidgetItem(a.to_location or "-"))
            self.tabela_os.setItem(i, 7, QTableWidgetItem("-"))
        header = self.tabela_os.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
    
    def _atualizar_cards_os(self):
        total = self.session.query(Activity).count()
        em_andamento = self.session.query(Activity).filter(Activity.status_atividade.in_(["Em Andamento", "em_andamento"])).count()
        pendentes = self.session.query(Activity).filter(Activity.status_atividade.in_(["Pendente", "pendente"])).count()
        concluidas = total - em_andamento - pendentes
        
        self._atualizar_card_mini(self.card_total_os, str(total))
        self._atualizar_card_mini(self.card_em_andamento, str(em_andamento))
        self._atualizar_card_mini(self.card_pendentes, str(pendentes))
        self._atualizar_card_mini(self.card_concluidas, str(concluidas))
    
    def _filtrar_os(self, tipo):
        self._carregar_tabela_os(tipo)
    
    def _criar_pagina_clientes(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        header = QHBoxLayout()
        titulo = QLabel("👥 Clientes / Empresas")
        titulo.setStyleSheet("color: #e94560; font-size: 20px; font-weight: bold; background: transparent;")
        header.addWidget(titulo)
        header.addStretch()
        btn_novo = QPushButton("➕ Nova Empresa")
        btn_novo.setCursor(Qt.PointingHandCursor)
        btn_novo.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #1a1a2e; border: none; border-radius: 6px; padding: 8px 16px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #94d89f; }")
        btn_novo.clicked.connect(self._nova_empresa)
        header.addWidget(btn_novo)
        layout.addLayout(header)
        layout.addSpacing(10)
        self.tabela_clientes = QTableWidget()
        self.tabela_clientes.setColumnCount(6)
        self.tabela_clientes.setHorizontalHeaderLabels(["Nome", "CNPJ", "Cidade/UF", "Telefone", "Email", "Impressoras"])
        self.tabela_clientes.setStyleSheet("QTableWidget { background-color: #0f3460; color: #e0e0e0; border: 1px solid #533483; border-radius: 10px; gridline-color: #1a1a3e; selection-background-color: #533483; font-size: 13px; } QTableWidget::item { padding: 8px; } QTableWidget::item:hover { background-color: #1a1a4e; } QTableWidget::item:selected { background-color: #533483; color: white; } QHeaderView::section { background-color: #16213e; color: #89b4fa; font-weight: bold; padding: 10px 8px; border: none; border-bottom: 2px solid #e94560; font-size: 12px; }")
        self.tabela_clientes.horizontalHeader().setStretchLastSection(True)
        self.tabela_clientes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela_clientes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela_clientes.verticalHeader().setVisible(False)
        self.tabela_clientes.cellDoubleClicked.connect(self._editar_empresa)
        layout.addWidget(self.tabela_clientes)
        self._carregar_tabela_clientes()
        return page

    def _editar_empresa(self, row, col):
        """Abre diálogo para editar uma empresa"""
        nome_empresa = self.tabela_clientes.item(row, 0).text()
        empresa = self.session.query(Company).filter(Company.nome == nome_empresa).first()
        
        if not empresa:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"✏️ Editar Empresa: {empresa.nome}")
        dialog.setFixedSize(500, 450)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #c0c0d0; font-size: 12px; }
            QLineEdit { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; font-size: 13px; }
            QComboBox { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; }
            QPushButton { border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 12px; }
        """)
        
        layout = QFormLayout(dialog)
        layout.setSpacing(8)
        
        # Nome
        nome_input = QLineEdit(empresa.nome or "")
        layout.addRow("Nome:", nome_input)
        
        # CNPJ
        cnpj_input = QLineEdit(empresa.cnpj or "")
        cnpj_input.setPlaceholderText("00.000.000/0000-00")
        layout.addRow("CNPJ:", cnpj_input)
        
        # Tipo
        tipo_combo = QComboBox()
        tipo_combo.addItems(["Cliente", "Filial", "Parceiro"])
        tipo_combo.setCurrentText(empresa.tipo or "cliente")
        layout.addRow("Tipo:", tipo_combo)
        
        # Telefone
        tel_input = QLineEdit(empresa.telefone or "")
        tel_input.setPlaceholderText("(00) 00000-0000")
        layout.addRow("Telefone:", tel_input)
        
        # Email
        email_input = QLineEdit(empresa.email or "")
        email_input.setPlaceholderText("email@empresa.com")
        layout.addRow("Email:", email_input)
        
        # Endereço
        end_input = QLineEdit(empresa.endereco or "")
        end_input.setPlaceholderText("Rua/Av, número")
        layout.addRow("Endereço:", end_input)
        
        # Cidade
        cidade_input = QLineEdit(empresa.cidade or "")
        cidade_input.setPlaceholderText("Cidade")
        layout.addRow("Cidade:", cidade_input)
        
        # UF
        uf_input = QLineEdit(empresa.uf or "")
        uf_input.setPlaceholderText("UF")
        uf_input.setMaxLength(2)
        layout.addRow("UF:", uf_input)
        
        # Observação
        from PySide6.QtWidgets import QTextEdit
        obs_input = QTextEdit()
        obs_input.setMaximumHeight(60)
        obs_input.setPlainText(empresa.observacao or "")
        layout.addRow("Observação:", obs_input)
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_salvar = QPushButton("💾 Salvar")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #1a1a2e; } QPushButton:hover { background-color: #94d89f; }")
        btn_salvar.clicked.connect(lambda: self._salvar_edicao_empresa(
            dialog, empresa, nome_input, cnpj_input, tipo_combo, tel_input, email_input,
            end_input, cidade_input, uf_input, obs_input
        ))
        btn_layout.addWidget(btn_salvar)
        
        btn_excluir = QPushButton("🗑️ Excluir")
        btn_excluir.setCursor(Qt.PointingHandCursor)
        btn_excluir.setStyleSheet("QPushButton { background-color: #f38ba8; color: #1a1a2e; } QPushButton:hover { background-color: #eb7a94; }")
        btn_excluir.clicked.connect(lambda: self._excluir_empresa(dialog, empresa))
        btn_layout.addWidget(btn_excluir)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet("QPushButton { background-color: #e94560; color: white; } QPushButton:hover { background-color: #d63850; }")
        btn_cancelar.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancelar)
        
        layout.addRow(btn_layout)
        dialog.exec()

    def _salvar_edicao_empresa(self, dialog, empresa, nome, cnpj, tipo, telefone, email, endereco, cidade, uf, obs):
        nome_antigo = empresa.nome
        nome_novo = nome.text().strip()
        
        empresa.cnpj = cnpj.text().strip()
        empresa.tipo = tipo.currentText()
        empresa.telefone = telefone.text().strip()
        empresa.email = email.text().strip()
        empresa.endereco = endereco.text().strip()
        empresa.cidade = cidade.text().strip()
        empresa.uf = uf.text().strip().upper()
        empresa.observacao = obs.toPlainText().strip()
        
        if nome_antigo != nome_novo and nome_novo:
            impressoras = self.session.query(Printer).filter(
                Printer.local_atual == nome_antigo
            ).all()
            for p in impressoras:
                p.local_atual = nome_novo
                print(f"✅ Impressora {p.patrimonio}: '{nome_antigo}' -> '{nome_novo}'")
        
        empresa.nome = nome_novo
        self.session.commit()
        self._carregar_tabela_clientes()
        self.carregar_dados()
        dialog.accept()

    def _excluir_empresa(self, dialog, empresa):
        """Exclui uma empresa após confirmação"""
        resposta = QMessageBox.question(
            dialog,
            "Confirmar Exclusão",
            f"Deseja realmente excluir a empresa '{empresa.nome}'?\n\n"
            "As impressoras associadas NÃO serão excluídas, apenas ficarão sem empresa vinculada.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if resposta == QMessageBox.Yes:
            self.session.delete(empresa)
            self.session.commit()
            self._carregar_tabela_clientes()
            dialog.accept()
    
    def _carregar_tabela_clientes(self):
        empresas = self.session.query(Company).order_by(Company.nome).all()
        self.tabela_clientes.setRowCount(len(empresas))
        for i, emp in enumerate(empresas):
            self.tabela_clientes.setItem(i, 0, QTableWidgetItem(emp.nome))
            self.tabela_clientes.setItem(i, 1, QTableWidgetItem(emp.cnpj or "-"))
            cidade_uf = f"{emp.cidade or ''}/{emp.uf or ''}".strip("/")
            self.tabela_clientes.setItem(i, 2, QTableWidgetItem(cidade_uf if cidade_uf else "-"))
            self.tabela_clientes.setItem(i, 3, QTableWidgetItem(emp.telefone or "-"))
            self.tabela_clientes.setItem(i, 4, QTableWidgetItem(emp.email or "-"))
            num = self.session.query(Printer).filter(Printer.local_atual.like(f"%{emp.nome}%")).count()
            self.tabela_clientes.setItem(i, 5, QTableWidgetItem(str(num)))
        self.tabela_clientes.resizeColumnsToContents()
    
    def _nova_empresa(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nova Empresa")
        dialog.setFixedSize(400, 300)
        dialog.setStyleSheet("QDialog { background-color: #1a1a2e; color: #e0e0e0; } QLabel { color: #c0c0d0; font-size: 12px; } QLineEdit { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; } QPushButton { background-color: #e94560; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }")
        layout = QFormLayout(dialog)
        nome_input = QLineEdit()
        nome_input.setPlaceholderText("Nome da empresa")
        layout.addRow("Nome:", nome_input)
        cnpj_input = QLineEdit()
        cnpj_input.setPlaceholderText("00.000.000/0000-00")
        layout.addRow("CNPJ:", cnpj_input)
        telefone_input = QLineEdit()
        telefone_input.setPlaceholderText("(00) 00000-0000")
        layout.addRow("Telefone:", telefone_input)
        email_input = QLineEdit()
        email_input.setPlaceholderText("email@empresa.com")
        layout.addRow("Email:", email_input)
        tipo_input = QComboBox()
        tipo_input.addItems(["Cliente", "Filial", "Parceiro"])
        layout.addRow("Tipo:", tipo_input)
        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.accepted.connect(lambda: self._salvar_empresa(dialog, nome_input, cnpj_input, telefone_input, email_input, tipo_input))
        botoes.rejected.connect(dialog.reject)
        layout.addRow(botoes)
        dialog.exec()
    
    def _salvar_empresa(self, dialog, nome, cnpj, telefone, email, tipo):
        nome_text = nome.text().strip()
        if not nome_text:
            return
        empresa = Company(nome=nome_text, cnpj=cnpj.text().strip(), telefone=telefone.text().strip(), email=email.text().strip(), tipo=tipo.currentText())
        self.session.add(empresa)
        self.session.commit()
        self._carregar_tabela_clientes()
        dialog.accept()
    
    def _criar_pagina_pecas(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        header = QHBoxLayout()
        titulo = QLabel("🔧 Peças / Estoque")
        titulo.setStyleSheet("color: #e94560; font-size: 20px; font-weight: bold; background: transparent;")
        header.addWidget(titulo)
        header.addStretch()
        btn_nova = QPushButton("➕ Nova Peça")
        btn_nova.setCursor(Qt.PointingHandCursor)
        btn_nova.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #1a1a2e; border: none; border-radius: 6px; padding: 8px 16px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #94d89f; }")
        btn_nova.clicked.connect(self._nova_peca)
        header.addWidget(btn_nova)
        layout.addLayout(header)
        layout.addSpacing(10)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(10)
        self.card_total_pecas = self._criar_card_mini("🔩", "Total Peças", "0", "#89b4fa")
        self.card_estoque = self._criar_card_mini("📦", "Em Estoque", "0", "#a6e3a1")
        self.card_sem_estoque = self._criar_card_mini("⚠️", "Sem Estoque", "0", "#f38ba8")
        cards_layout.addWidget(self.card_total_pecas)
        cards_layout.addWidget(self.card_estoque)
        cards_layout.addWidget(self.card_sem_estoque)
        layout.addLayout(cards_layout)
        layout.addSpacing(10)
        self.tabela_pecas = QTableWidget()
        self.tabela_pecas.setColumnCount(4)
        self.tabela_pecas.setHorizontalHeaderLabels(["Código", "Nome", "Descrição", "Estoque"])
        self.tabela_pecas.setStyleSheet("QTableWidget { background-color: #0f3460; color: #e0e0e0; border: 1px solid #533483; border-radius: 10px; gridline-color: #1a1a3e; selection-background-color: #533483; font-size: 13px; } QTableWidget::item { padding: 8px; } QTableWidget::item:hover { background-color: #1a1a4e; } QTableWidget::item:selected { background-color: #533483; color: white; } QHeaderView::section { background-color: #16213e; color: #89b4fa; font-weight: bold; padding: 10px 8px; border: none; border-bottom: 2px solid #e94560; font-size: 12px; }")
        self.tabela_pecas.horizontalHeader().setStretchLastSection(True)
        self.tabela_pecas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela_pecas.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela_pecas.verticalHeader().setVisible(False)
        layout.addWidget(self.tabela_pecas)
        self.tabela_pecas.cellDoubleClicked.connect(self._editar_peca)
        self._carregar_tabela_pecas()
        return page
    
    def _carregar_tabela_pecas(self):
        pecas = self.session.query(Part).order_by(Part.nome).all()
        self.tabela_pecas.setRowCount(len(pecas))
        total_pecas = 0
        total_estoque = 0
        sem_estoque = 0
        
        for i, p in enumerate(pecas):
            self.tabela_pecas.setItem(i, 0, QTableWidgetItem(p.codigo or "-"))
            self.tabela_pecas.setItem(i, 1, QTableWidgetItem(p.nome))
            self.tabela_pecas.setItem(i, 2, QTableWidgetItem(p.descricao or "-"))
            self.tabela_pecas.setItem(i, 3, QTableWidgetItem(p.modelo_compativel or "Qualquer"))
            
            estoque_item = QTableWidgetItem(str(p.quantidade_estoque))
            estoque_item.setTextAlignment(Qt.AlignCenter)
            if p.quantidade_estoque > 10:
                estoque_item.setForeground(QColor("#a6e3a1"))
            elif p.quantidade_estoque > 0:
                estoque_item.setForeground(QColor("#f9e2af"))
            else:
                estoque_item.setForeground(QColor("#f38ba8"))
            self.tabela_pecas.setItem(i, 4, estoque_item)
            
            total_pecas += 1
            total_estoque += p.quantidade_estoque
            if p.quantidade_estoque == 0:
                sem_estoque += 1
        
        self.tabela_pecas.resizeColumnsToContents()
        self._atualizar_card_mini(self.card_total_pecas, str(total_pecas))
        self._atualizar_card_mini(self.card_estoque, str(total_estoque))
        self._atualizar_card_mini(self.card_sem_estoque, str(sem_estoque))
    
    def _nova_peca(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nova Peça")
        dialog.setFixedSize(450, 320)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #c0c0d0; font-size: 12px; }
            QLineEdit { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; }
            QComboBox { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; }
            QPushButton { background-color: #e94560; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }
        """)
        
        layout = QFormLayout(dialog)
        layout.setSpacing(10)
        
        # Gera código automático
        count = self.session.query(Part).count()
        codigo_auto = f"PEC{count + 1:04d}"
        
        codigo_input = QLineEdit(codigo_auto)
        codigo_input.setReadOnly(True)
        codigo_input.setStyleSheet("QLineEdit { background-color: #16213e; color: #a0a0b0; border: 1px solid #313244; }")
        layout.addRow("Código:", codigo_input)
        
        nome_input = QLineEdit()
        nome_input.setPlaceholderText("Nome da peça")
        layout.addRow("Nome *:", nome_input)
        
        desc_input = QLineEdit()
        desc_input.setPlaceholderText("Descrição da peça")
        layout.addRow("Descrição:", desc_input)
        
        # Modelo compatível
        modelo_combo = QComboBox()
        modelo_combo.setEditable(True)
        modelo_combo.addItem("")  # Qualquer modelo
        modelos = self.session.query(Printer.modelo).filter(Printer.modelo != "").distinct().order_by(Printer.modelo).all()
        for m in modelos:
            if m[0]:
                modelo_combo.addItem(m[0])
        layout.addRow("Modelo Compatível:", modelo_combo)
        
        qtd_input = QLineEdit()
        qtd_input.setPlaceholderText("0")
        layout.addRow("Quantidade:", qtd_input)
        
        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.accepted.connect(lambda: self._salvar_peca(dialog, codigo_input, nome_input, desc_input, modelo_combo, qtd_input))
        botoes.rejected.connect(dialog.reject)
        layout.addRow(botoes)
        
        dialog.exec()

    def _salvar_peca(self, dialog, codigo, nome, desc, modelo, qtd):
        nome_text = nome.text().strip()
        if not nome_text:
            return
        
        try:
            quantidade = int(qtd.text()) if qtd.text().strip() else 0
        except:
            quantidade = 0
        
        peca = Part(
            codigo=codigo.text().strip(),
            nome=nome_text,
            descricao=desc.text().strip(),
            modelo_compativel=modelo.currentText().strip(),
            quantidade_estoque=quantidade,
            preco_unitario=0.0
        )
        
        self.session.add(peca)
        self.session.commit()
        self._carregar_tabela_pecas()
        dialog.accept()

    def _editar_peca(self, row, col):
        """Abre diálogo para editar/excluir uma peça"""
        nome_peca = self.tabela_pecas.item(row, 1).text()
        peca = self.session.query(Part).filter(Part.nome == nome_peca).first()
        
        if not peca:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"✏️ Editar Peça: {peca.nome}")
        dialog.setFixedSize(400, 280)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #c0c0d0; font-size: 12px; }
            QLineEdit { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; font-size: 13px; }
            QPushButton { border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 12px; }
        """)
        
        layout = QFormLayout(dialog)
        layout.setSpacing(8)
        
        codigo_input = QLineEdit(peca.codigo or "")
        codigo_input.setReadOnly(True)
        codigo_input.setStyleSheet("QLineEdit { background-color: #16213e; color: #a0a0b0; border: 1px solid #313244; }")
        layout.addRow("Código:", codigo_input)
        
        nome_input = QLineEdit(peca.nome or "")
        layout.addRow("Nome:", nome_input)
        
        desc_input = QLineEdit(peca.descricao or "")
        desc_input.setPlaceholderText("Descrição da peça")
        layout.addRow("Descrição:", desc_input)
        
        qtd_input = QLineEdit(str(peca.quantidade_estoque))
        layout.addRow("Quantidade:", qtd_input)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_salvar = QPushButton("💾 Salvar")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #1a1a2e; } QPushButton:hover { background-color: #94d89f; }")
        btn_salvar.clicked.connect(lambda: self._salvar_edicao_peca(dialog, peca, nome_input, desc_input, qtd_input))
        btn_layout.addWidget(btn_salvar)
        
        btn_excluir = QPushButton("🗑️ Excluir")
        btn_excluir.setCursor(Qt.PointingHandCursor)
        btn_excluir.setStyleSheet("QPushButton { background-color: #f38ba8; color: #1a1a2e; } QPushButton:hover { background-color: #eb7a94; }")
        btn_excluir.clicked.connect(lambda: self._excluir_peca(dialog, peca))
        btn_layout.addWidget(btn_excluir)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet("QPushButton { background-color: #e94560; color: white; } QPushButton:hover { background-color: #d63850; }")
        btn_cancelar.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancelar)
        
        layout.addRow(btn_layout)
        dialog.exec()

    def _salvar_edicao_peca(self, dialog, peca, nome, desc, qtd):
        peca.nome = nome.text().strip()
        peca.descricao = desc.text().strip()
        try:
            peca.quantidade_estoque = int(qtd.text()) if qtd.text().strip() else 0
        except:
            pass
        
        self.session.commit()
        self._carregar_tabela_pecas()
        dialog.accept()
    
    def _excluir_peca(self, dialog, peca):
        resposta = QMessageBox.question(
            dialog,
            "Confirmar Exclusão",
            f"Deseja realmente excluir a peça '{peca.nome}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if resposta == QMessageBox.Yes:
            self.session.delete(peca)
            self.session.commit()
            self._carregar_tabela_pecas()
            dialog.accept()
    
    def _criar_pagina_transferencias(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        header = QHBoxLayout()
        titulo = QLabel("🚚 Transferências / Movimentações")
        titulo.setStyleSheet("color: #e94560; font-size: 20px; font-weight: bold; background: transparent;")
        header.addWidget(titulo)
        header.addStretch()
        btn_nova = QPushButton("➕ Nova Transferência")
        btn_nova.setCursor(Qt.PointingHandCursor)
        btn_nova.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #1a1a2e; border: none; border-radius: 6px; padding: 8px 16px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #94d89f; }")
        btn_nova.clicked.connect(self._nova_transferencia)
        header.addWidget(btn_nova)
        layout.addLayout(header)
        layout.addSpacing(10)
        resumo_layout = QHBoxLayout()
        resumo_layout.setSpacing(10)
        self.card_total_transf = self._criar_card_mini("🚚", "Total Transf.", "0", "#89b4fa")
        self.card_saidas = self._criar_card_mini("📤", "Saídas", "0", "#f9e2af")
        self.card_entradas = self._criar_card_mini("📥", "Entradas", "0", "#a6e3a1")
        self.card_pendentes = self._criar_card_mini("⏳", "Pendentes", "0", "#f38ba8")
        resumo_layout.addWidget(self.card_total_transf)
        resumo_layout.addWidget(self.card_saidas)
        resumo_layout.addWidget(self.card_entradas)
        resumo_layout.addWidget(self.card_pendentes)
        layout.addLayout(resumo_layout)
        layout.addSpacing(10)
        # Barra de busca
        busca_layout = QHBoxLayout()
        busca_label = QLabel("🔍")
        busca_label.setStyleSheet("font-size: 16px; background: transparent;")
        busca_layout.addWidget(busca_label)
        
        self.busca_transf_input = QLineEdit()
        self.busca_transf_input.setPlaceholderText("Buscar por patrimônio, origem, destino ou peça...")
        self.busca_transf_input.setMinimumHeight(32)
        self.busca_transf_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f3460; color: #ffffff;
                border: 2px solid #533483; border-radius: 8px;
                padding: 6px 12px; font-size: 13px;
            }
            QLineEdit:focus { border-color: #89b4fa; }
        """)
        self.busca_transf_input.textChanged.connect(self._filtrar_transferencias)
        busca_layout.addWidget(self.busca_transf_input)
        
        layout.addLayout(busca_layout)
        layout.addSpacing(8)
        self.tabela_transf = QTableWidget()
        self.tabela_transf.setColumnCount(7)
        self.tabela_transf.setHorizontalHeaderLabels(["Data", "Patrimônio", "Origem", "Destino", "Peças/Equipamento", "Nº Recibo", "Status"])
        self.tabela_transf.setStyleSheet("QTableWidget { background-color: #0f3460; color: #e0e0e0; border: 1px solid #533483; border-radius: 10px; gridline-color: #1a1a3e; selection-background-color: #533483; font-size: 13px; } QTableWidget::item { padding: 8px; } QTableWidget::item:hover { background-color: #1a1a4e; } QTableWidget::item:selected { background-color: #533483; color: white; } QHeaderView::section { background-color: #16213e; color: #89b4fa; font-weight: bold; padding: 10px 8px; border: none; border-bottom: 2px solid #e94560; font-size: 12px; }")
        self.tabela_transf.horizontalHeader().setStretchLastSection(True)
        self.tabela_transf.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela_transf.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela_transf.verticalHeader().setVisible(False)
        layout.addWidget(self.tabela_transf)
        self.tabela_transf.cellDoubleClicked.connect(self._editar_transferencia)
        self._carregar_tabela_transferencias()
        return page

    def _filtrar_transferencias(self, texto):
        """Filtra a tabela de transferências"""
        if not texto.strip():
            self._carregar_tabela_transferencias()
            return
        
        query = self.session.query(Activity).filter(
            Activity.kind == "MOVIMENTACAO"
        )
        
        # Busca por texto em vários campos
        filtro = f"%{texto}%"
        
        # Busca IDs de impressoras com patrimônio que contenha o texto
        printers = self.session.query(Printer).filter(
            Printer.patrimonio.like(filtro)
        ).all()
        printer_ids = [p.id for p in printers]
        
        if printer_ids:
            query = query.filter(
                Activity.printer_id.in_(printer_ids) |
                Activity.from_location.like(filtro) |
                Activity.to_location.like(filtro) |
                Activity.parts_used.like(filtro) |
                Activity.notes.like(filtro) |
                Activity.numero_recibo.like(filtro)
            )
        else:
            query = query.filter(
                Activity.from_location.like(filtro) |
                Activity.to_location.like(filtro) |
                Activity.parts_used.like(filtro) |
                Activity.notes.like(filtro) |
                Activity.numero_recibo.like(filtro)
            )
        
        atividades = query.order_by(Activity.event_at.desc()).limit(100).all()
        
        self.tabela_transf.setRowCount(len(atividades))
        for i, a in enumerate(atividades):
            self.tabela_transf.setItem(i, 0, QTableWidgetItem(a.event_at.strftime("%d/%m/%Y %H:%M") if a.event_at else "-"))
            printer = self.session.query(Printer).filter(Printer.id == a.printer_id).first()
            pat = printer.patrimonio if printer else "?"
            self.tabela_transf.setItem(i, 1, QTableWidgetItem(pat))
            self.tabela_transf.setItem(i, 2, QTableWidgetItem(a.from_location or "-"))
            dest_item = QTableWidgetItem(a.to_location or "-")
            dest_item.setForeground(QColor("#89b4fa"))
            self.tabela_transf.setItem(i, 3, dest_item)
            pecas = a.parts_used or a.notes or "Equipamento"
            if len(pecas) > 40:
                pecas = pecas[:37] + "..."
            self.tabela_transf.setItem(i, 4, QTableWidgetItem(pecas))
            self.tabela_transf.setItem(i, 5, QTableWidgetItem(a.numero_recibo or "-"))
            if a.status_atividade and a.status_atividade == "pendente":
                status_text = "⏳ Pendente"
                status_cor = QColor("#f9e2af")
            else:
                status_text = "✅ Concluída"
                status_cor = QColor("#a6e3a1")
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(status_cor)
            self.tabela_transf.setItem(i, 6, status_item)
        self.tabela_transf.resizeColumnsToContents()
        
        total = len(atividades)
        self._atualizar_card_mini(self.card_total_transf, str(total))
        self._atualizar_card_mini(self.card_entradas, str(total))
    
    def _carregar_tabela_transferencias(self):
        atividades = self.session.query(Activity).filter(Activity.kind == "MOVIMENTACAO").order_by(Activity.event_at.desc()).limit(100).all()
        self.tabela_transf.setRowCount(len(atividades))
        for i, a in enumerate(atividades):
            self.tabela_transf.setItem(i, 0, QTableWidgetItem(a.event_at.strftime("%d/%m/%Y %H:%M") if a.event_at else "-"))
            printer = self.session.query(Printer).filter(Printer.id == a.printer_id).first()
            pat = printer.patrimonio if printer else "?"
            self.tabela_transf.setItem(i, 1, QTableWidgetItem(pat))
            self.tabela_transf.setItem(i, 2, QTableWidgetItem(a.from_location or "-"))
            dest_item = QTableWidgetItem(a.to_location or "-")
            dest_item.setForeground(QColor("#89b4fa"))
            self.tabela_transf.setItem(i, 3, dest_item)
            pecas = a.parts_used or a.notes or "Equipamento"
            if len(pecas) > 40:
                pecas = pecas[:37] + "..."
            self.tabela_transf.setItem(i, 4, QTableWidgetItem(pecas))
            self.tabela_transf.setItem(i, 5, QTableWidgetItem(a.numero_recibo or "-"))
            status = (a.status_atividade or "").lower()
            if status == "pendente":
                status_text = "⏳ Pendente"
                status_cor = QColor("#f9e2af")
            elif status in ["em andamento", "em_andamento"]:
                status_text = "🔄 Em Andamento"
                status_cor = QColor("#89b4fa")
            else:
                status_text = "✅ Concluída"
                status_cor = QColor("#a6e3a1")
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(status_cor)
            self.tabela_transf.setItem(i, 6, status_item)
        self.tabela_transf.resizeColumnsToContents()
        total = len(atividades)
        self._atualizar_card_mini(self.card_total_transf, str(total))
        self._atualizar_card_mini(self.card_entradas, str(total))
    
    def _nova_transferencia(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("📦 Nova Transferência / Movimentação")
        dialog.setMinimumSize(550, 550)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #c0c0d0; font-size: 12px; }
            QLineEdit, QTextEdit { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; font-size: 13px; }
            QComboBox { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; }
            QPushButton { border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 12px; }
            QTabWidget::pane { border: 1px solid #533483; background-color: #1a1a2e; }
            QTabBar::tab { background-color: #0f3460; color: #a0a0b0; padding: 8px 15px; border: 1px solid #533483; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; }
            QTabBar::tab:selected { background-color: #1a1a2e; color: #e94560; font-weight: bold; }
        """)
        
        tabs = QTabWidget()
        atividade_salva = None  # Guarda a atividade após salvar
        
        # ========== TAB DADOS ==========
        tab_dados = QWidget()
        layout = QFormLayout(tab_dados)
        layout.setSpacing(8)
        
        # Tipo
        tipo_combo = QComboBox()
        tipo_combo.addItems(["Impressora Completa", "Apenas Peça(s)"])
        layout.addRow("Tipo:", tipo_combo)
        
        # Impressora
        printer_combo = QComboBox()
        printer_combo.setEditable(True)
        printer_combo.addItem("")
        printers = self.session.query(Printer).order_by(Printer.patrimonio).all()
        for p in printers:
            printer_combo.addItem(f"{p.patrimonio} - {p.modelo} ({p.local_atual or 'Sem local'})")
        layout.addRow("Impressora:", printer_combo)
        
        # Peças
        pecas_input = QLineEdit()
        pecas_input.setPlaceholderText("Ex: Fusor, Placa Fonte...")
        layout.addRow("Peças:", pecas_input)
        
        # Origem
        origem_combo = QComboBox()
        origem_combo.setEditable(True)
        origem_combo.addItem("")
        empresas = self.session.query(Company).order_by(Company.nome).all()
        for emp in empresas:
            origem_combo.addItem(emp.nome)
        layout.addRow("Origem:", origem_combo)
        
        # Destino
        destino_combo = QComboBox()
        destino_combo.setEditable(True)
        destino_combo.addItem("")
        for emp in empresas:
            destino_combo.addItem(emp.nome)
        layout.addRow("Destino:", destino_combo)
        
        # Nº Recibo
        recibo_input = QLineEdit()
        recibo_input.setPlaceholderText("Número do recibo (opcional)")
        layout.addRow("Nº Recibo:", recibo_input)
        
        # Observação
        obs_input = QTextEdit()
        obs_input.setMinimumHeight(80)
        obs_input.setMaximumHeight(100)
        obs_input.setPlaceholderText("Detalhes da movimentação...")
        layout.addRow("Observação:", obs_input)
        
        # Status
        status_combo = QComboBox()
        status_combo.addItems(["Concluida", "Pendente", "Em Andamento"])
        layout.addRow("Status:", status_combo)
        
        # Botão salvar
        def salvar_nova():
            nonlocal atividade_salva
            # Validações
            if not origem_combo.currentText().strip() or not destino_combo.currentText().strip():
                QMessageBox.warning(dialog, "Erro", "Preencha origem e destino!")
                return
            
            printer_text = printer_combo.currentText().strip()
            printer_id = "00000000-0000-0000-0000-000000000000"
            
            if printer_text and " - " in printer_text:
                pat = printer_text.split(" - ")[0].strip()
                p = self.session.query(Printer).filter(Printer.patrimonio == pat).first()
                if p:
                    printer_id = p.id
            
            desc = obs_input.toPlainText().strip()
            parts = pecas_input.text().strip()
            
            if tipo_combo.currentText() == "Apenas Peça(s)" and not parts:
                QMessageBox.warning(dialog, "Erro", "Informe a(s) peça(s)!")
                return
            
            atividade = Activity(
                printer_id=printer_id,
                kind="MOVIMENTACAO",
                event_at=dt.now(),
                notes=desc or f"Movimentação de {'peça(s)' if parts else 'impressora'}",
                parts_used=parts,
                from_location=origem_combo.currentText().strip(),
                to_location=destino_combo.currentText().strip(),
                numero_recibo=recibo_input.text().strip(),
                status_atividade=status_combo.currentText()
            )
            self.session.add(atividade)
            self.session.commit()
            atividade_salva = atividade
            self._carregar_tabela_transferencias()
            
            # Atualiza a aba de anexos
            tabs.removeTab(1)
            tab_anexos = self._criar_tab_anexos_com_salvar("activity", atividade.id, dialog, salvar_nova)
            tabs.addTab(tab_anexos, "📎 Anexos")
            tabs.setCurrentIndex(1)
            QMessageBox.information(dialog, "Sucesso", "Transferência salva!")
        
        btn_salvar = QPushButton("💾 Salvar")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #1a1a2e; } QPushButton:hover { background-color: #94d89f; }")
        btn_salvar.clicked.connect(salvar_nova)
        layout.addRow(btn_salvar)
        
        tabs.addTab(tab_dados, "📋 Dados")
        
        # ========== TAB ANEXOS (vazia inicialmente) ==========
        tab_anexos = QWidget()
        anexos_layout = QVBoxLayout(tab_anexos)
        lbl = QLabel("💡 Salve a transferência primeiro para adicionar anexos.")
        lbl.setStyleSheet("color: #a0a0b0; font-size: 14px; padding: 30px;")
        lbl.setAlignment(Qt.AlignCenter)
        anexos_layout.addWidget(lbl)
        anexos_layout.addStretch()
        tabs.addTab(tab_anexos, "📎 Anexos")
        
        main_layout = QVBoxLayout(dialog)
        main_layout.addWidget(tabs)
        dialog.exec()
    
    def _salvar_transferencia(self, dialog, tipo, printer, peca, origem, destino, recibo, obs, status):
        tipo_text = tipo.currentText()
        
        # Pega a impressora (pode ser vazia se for só peça)
        printer_text = printer.currentText().strip()
        printer_id = None
        patrimonio = ""
        
        if printer_text and " - " in printer_text:
            pat = printer_text.split(" - ")[0].strip()
            p = self.session.query(Printer).filter(Printer.patrimonio == pat).first()
            if p:
                printer_id = p.id
                patrimonio = p.patrimonio
        elif printer_text:
            p = self.session.query(Printer).filter(Printer.patrimonio == printer_text).first()
            if p:
                printer_id = p.id
                patrimonio = p.patrimonio
        
        if not printer_id and tipo_text == "Impressora Completa":
            QMessageBox.warning(dialog, "Erro", "Selecione uma impressora!")
            return
        
        if not origem.currentText().strip() or not destino.currentText().strip():
            QMessageBox.warning(dialog, "Erro", "Preencha origem e destino!")
            return
        
        # Monta descrição
        descricao = obs.toPlainText().strip()
        if tipo_text == "Apenas Peça(s)":
            pecas = peca.text().strip()
            if not pecas:
                QMessageBox.warning(dialog, "Erro", "Informe a(s) peça(s)!")
                return
            parts_used = pecas
            if not descricao:
                descricao = f"Envio de peça(s): {pecas}"
        else:
            parts_used = ""
            if not descricao:
                descricao = f"Impressora {patrimonio} movimentada"
        
        # Se não tem impressora (só peça), usa um ID especial
        if not printer_id:
            printer_id = "00000000-0000-0000-0000-000000000000"
        
        atividade = Activity(
            printer_id=printer_id,
            kind="MOVIMENTACAO",
            event_at=dt.now(),
            notes=descricao,
            parts_used=parts_used,
            from_location=origem.currentText().strip(),
            to_location=destino.currentText().strip(),
            numero_recibo=recibo.text().strip(),
            status_atividade=status.currentText()
        )
        
        self.session.add(atividade)
        self.session.commit()
        self._carregar_tabela_transferencias()
        dialog.accept()

    def _editar_transferencia(self, row, col):
        """Abre diálogo para editar/excluir uma transferência"""
        patrimonio = self.tabela_transf.item(row, 1).text()
        origem_text = self.tabela_transf.item(row, 2).text()
        destino_text = self.tabela_transf.item(row, 3).text()
        
        atividade = self.session.query(Activity).filter(
            Activity.kind == "MOVIMENTACAO",
            Activity.from_location == origem_text,
            Activity.to_location == destino_text
        ).order_by(Activity.event_at.desc()).first()
        
        if not atividade:
            QMessageBox.warning(self, "Erro", "Atividade não encontrada!")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("✏️ Editar Transferência")
        dialog.setMinimumSize(550, 550)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #c0c0d0; font-size: 12px; }
            QLineEdit, QTextEdit { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; font-size: 13px; }
            QComboBox { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; }
            QPushButton { border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 12px; }
            QTabWidget::pane { border: 1px solid #533483; background-color: #1a1a2e; }
            QTabBar::tab { background-color: #0f3460; color: #a0a0b0; padding: 8px 15px; border: 1px solid #533483; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; }
            QTabBar::tab:selected { background-color: #1a1a2e; color: #e94560; font-weight: bold; }
        """)
        
        # Flag para controle
        alteracoes_salvas = False
        
        def salvar():
            nonlocal alteracoes_salvas
            self._salvar_edicao_transferencia(
                dialog, atividade, printer_combo, data_input, pecas_input,
                origem_combo, destino_combo, recibo_input, obs_input, status_combo
            )
            alteracoes_salvas = True
        
        # Tabs
        tabs = QTabWidget()
        
        # ========== TAB DADOS ==========
        tab_dados = QWidget()
        layout = QFormLayout(tab_dados)
        layout.setSpacing(8)
        
        printer_combo = QComboBox()
        printer_combo.setEditable(True)
        printer_combo.addItem("")
        printers = self.session.query(Printer).order_by(Printer.patrimonio).all()
        for p in printers:
            printer_combo.addItem(f"{p.patrimonio} - {p.modelo} ({p.local_atual or 'Sem local'})")
        printer = self.session.query(Printer).filter(Printer.id == atividade.printer_id).first()
        if printer:
            printer_combo.setCurrentText(f"{printer.patrimonio} - {printer.modelo} ({printer.local_atual or 'Sem local'})")
        layout.addRow("Impressora:", printer_combo)
        
        data_input = QLineEdit()
        data_input.setText(atividade.event_at.strftime("%d/%m/%Y %H:%M") if atividade.event_at else "")
        layout.addRow("Data/Hora:", data_input)
        
        pecas_input = QLineEdit()
        pecas_input.setText(atividade.parts_used or "")
        pecas_input.setPlaceholderText("Ex: Fusor, Placa Fonte...")
        layout.addRow("Peças:", pecas_input)
        
        origem_combo = QComboBox()
        origem_combo.setEditable(True)
        origem_combo.addItem("")
        empresas = self.session.query(Company).order_by(Company.nome).all()
        for emp in empresas:
            origem_combo.addItem(emp.nome)
        origem_combo.setCurrentText(atividade.from_location or "")
        layout.addRow("Origem:", origem_combo)
        
        destino_combo = QComboBox()
        destino_combo.setEditable(True)
        destino_combo.addItem("")
        for emp in empresas:
            destino_combo.addItem(emp.nome)
        destino_combo.setCurrentText(atividade.to_location or "")
        layout.addRow("Destino:", destino_combo)
        
        recibo_input = QLineEdit()
        recibo_input.setText(atividade.numero_recibo or "")
        recibo_input.setPlaceholderText("Número do recibo")
        layout.addRow("Nº Recibo:", recibo_input)
        
        obs_input = QTextEdit()
        obs_input.setMinimumHeight(80)
        obs_input.setMaximumHeight(100)
        obs_input.setPlainText(atividade.notes or "")
        obs_input.setPlaceholderText("Observações sobre a movimentação...")
        layout.addRow("Observação:", obs_input)
        
        status_combo = QComboBox()
        status_combo.addItems(["Concluida", "Pendente", "Em Andamento"])
        status_combo.setCurrentText(atividade.status_atividade or "Concluida")
        layout.addRow("Status:", status_combo)
        
        # Botões da aba Dados
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_salvar_dados = QPushButton("💾 Salvar")
        btn_salvar_dados.setCursor(Qt.PointingHandCursor)
        btn_salvar_dados.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #1a1a2e; } QPushButton:hover { background-color: #94d89f; }")
        btn_salvar_dados.clicked.connect(salvar)
        btn_layout.addWidget(btn_salvar_dados)
        
        btn_excluir = QPushButton("🗑️ Excluir")
        btn_excluir.setCursor(Qt.PointingHandCursor)
        btn_excluir.setStyleSheet("QPushButton { background-color: #f38ba8; color: #1a1a2e; } QPushButton:hover { background-color: #eb7a94; }")
        btn_excluir.clicked.connect(lambda: self._excluir_transferencia(dialog, atividade))
        btn_layout.addWidget(btn_excluir)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet("QPushButton { background-color: #e94560; color: white; } QPushButton:hover { background-color: #d63850; }")
        btn_cancelar.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancelar)
        
        layout.addRow(btn_layout)
        tabs.addTab(tab_dados, "📋 Dados")
        
        # ========== TAB ANEXOS ==========
        tab_anexos = self._criar_tab_anexos_com_salvar("activity", atividade.id, dialog, salvar)
        tabs.addTab(tab_anexos, "📎 Anexos")
        
        # Alerta ao fechar
        def ao_fechar():
            if alteracoes_salvas:
                dialog.accept()
                return
            
            # Cria um diálogo personalizado
            msg = QDialog(dialog)
            msg.setWindowTitle("Salvar Alterações?")
            msg.setFixedSize(350, 150)
            msg.setStyleSheet("""
                QDialog { background-color: #1a1a2e; border-radius: 12px; }
                QLabel { color: #e0e0e0; font-size: 14px; font-weight: bold; }
                QPushButton { border: none; border-radius: 8px; padding: 10px 20px; font-size: 13px; font-weight: bold; }
            """)
            
            msg_layout = QVBoxLayout(msg)
            msg_layout.setSpacing(15)
            
            lbl = QLabel("Deseja salvar as alterações antes de fechar?")
            lbl.setAlignment(Qt.AlignCenter)
            msg_layout.addWidget(lbl)
            
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(15)
            
            btn_sim = QPushButton("💾 Sim, Salvar")
            btn_sim.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #1a1a2e; } QPushButton:hover { background-color: #94d89f; }")
            
            btn_nao = QPushButton("❌ Não, Fechar")
            btn_nao.setStyleSheet("QPushButton { background-color: #f38ba8; color: #1a1a2e; } QPushButton:hover { background-color: #eb7a94; }")
            
            btn_layout.addWidget(btn_sim)
            btn_layout.addWidget(btn_nao)
            msg_layout.addLayout(btn_layout)
            
            btn_sim.clicked.connect(lambda: [salvar(), msg.accept(), dialog.accept()])
            btn_nao.clicked.connect(lambda: [msg.accept(), dialog.done(0)])
            
            msg.exec()
        
        dialog.reject = ao_fechar
        
        main_layout = QVBoxLayout(dialog)
        main_layout.addWidget(tabs)
        dialog.exec()

    def _criar_tab_anexos_com_salvar(self, entity_type, entity_id, parent_dialog, callback_salvar):
        """Cria a aba de anexos COM botão salvar"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        anexos = self.session.query(Attachment).filter(
            Attachment.entity_type == entity_type,
            Attachment.entity_id == entity_id
        ).all()
        
        anexos_label = QLabel(f"📎 Anexos ({len(anexos)})")
        anexos_label.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 14px;")
        layout.addWidget(anexos_label)
        
        if anexos:
            anexos_tabela = QTableWidget()
            anexos_tabela.setColumnCount(4)
            anexos_tabela.setHorizontalHeaderLabels(["Nome", "Tipo", "Tamanho", "Data"])
            anexos_tabela.setStyleSheet("""
                QTableWidget { background-color: #0f3460; color: #e0e0e0; border: 1px solid #533483; border-radius: 8px; gridline-color: #1a1a3e; font-size: 12px; }
                QTableWidget::item { padding: 8px; }
                QHeaderView::section { background-color: #16213e; color: #89b4fa; font-weight: bold; padding: 8px; border: none; }
            """)
            anexos_tabela.setRowCount(len(anexos))
            for i, anexo in enumerate(anexos):
                anexos_tabela.setItem(i, 0, QTableWidgetItem(anexo.original_name))
                anexos_tabela.setItem(i, 1, QTableWidgetItem(anexo.categoria))
                anexos_tabela.setItem(i, 2, QTableWidgetItem(f"{anexo.size_bytes / 1024:.1f} KB"))
                anexos_tabela.setItem(i, 3, QTableWidgetItem(anexo.created_at.strftime("%d/%m/%Y %H:%M") if anexo.created_at else "-"))
            
            header = anexos_tabela.horizontalHeader()
            header.setStretchLastSection(True)
            for i in range(4):
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            anexos_tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
            anexos_tabela.verticalHeader().setVisible(False)
            anexos_tabela.setMaximumHeight(200)
            
            anexos_tabela.setContextMenuPolicy(Qt.CustomContextMenu)
            anexos_tabela.customContextMenuRequested.connect(lambda pos: self._menu_anexo_simples(pos, anexos_tabela, anexos))
            anexos_tabela.cellDoubleClicked.connect(lambda r, c: os.startfile(anexos[r].file_path) if os.path.exists(anexos[r].file_path) else None)
            layout.addWidget(anexos_tabela)
        else:
            sem = QLabel("Nenhum anexo encontrado.")
            sem.setStyleSheet("color: #a0a0b0; font-size: 13px; padding: 20px;")
            sem.setAlignment(Qt.AlignCenter)
            layout.addWidget(sem)
        
        # Botão adicionar anexo
        btn_add = QPushButton("📎 Adicionar Anexo")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("QPushButton { background-color: #89b4fa; color: #1a1a2e; border-radius: 6px; padding: 10px; font-weight: bold; } QPushButton:hover { background-color: #74b4fa; }")
        btn_add.clicked.connect(lambda: self._anexar_atualizar_aba(entity_type, entity_id, parent_dialog, callback_salvar))
        layout.addWidget(btn_add)
        
        # Botão salvar (mesmo callback)
        btn_salvar = QPushButton("💾 Salvar Alterações")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #1a1a2e; border-radius: 6px; padding: 10px; font-weight: bold; } QPushButton:hover { background-color: #94d89f; }")
        btn_salvar.clicked.connect(callback_salvar)
        layout.addWidget(btn_salvar)
        
        layout.addStretch()
        return tab
    
    def _anexar_atualizar_aba(self, entity_type, entity_id, parent_dialog, callback_salvar):
        """Anexa arquivo e recria a aba de anexos"""
        from PySide6.QtWidgets import QFileDialog
        import shutil
        import os
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo", "", "Todos (*.*)")
        if not file_path:
            return
        
        anexos_dir = Path(__file__).parent.parent.parent / "anexos" / entity_type
        anexos_dir.mkdir(parents=True, exist_ok=True)
        
        original_name = os.path.basename(file_path)
        ext = os.path.splitext(original_name)[1]
        unique_name = f"{entity_type}_{entity_id}_{dt.now().strftime('%Y%m%d%H%M%S')}{ext}"
        dest_path = anexos_dir / unique_name
        shutil.copy2(file_path, dest_path)
        
        anexo = Attachment(
            entity_type=entity_type, entity_id=entity_id,
            filename=unique_name, original_name=original_name,
            file_path=str(dest_path), mime_type='application/octet-stream',
            size_bytes=os.path.getsize(dest_path), categoria='outro',
            uploader_id=self.user['id'] if self.user else None
        )
        self.session.add(anexo)
        self.session.commit()
        
        # Recria as abas
        tabs = parent_dialog.findChild(QTabWidget)
        if tabs:
            tabs.removeTab(1)
            nova_aba = self._criar_tab_anexos_com_salvar(entity_type, entity_id, parent_dialog, callback_salvar)
            tabs.addTab(nova_aba, "📎 Anexos")
            tabs.setCurrentIndex(1)

    def _anexar_e_recarregar(self, dialog, entity_type, entity_id, tabs):
        """Anexa arquivo e atualiza a tabela de anexos na mesma janela"""
        from PySide6.QtWidgets import QFileDialog
        import shutil
        import os
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo", "",
            "Todos os Arquivos (*.*);;Imagens (*.png *.jpg *.jpeg);;PDF (*.pdf)"
        )
        
        if not file_path:
            return
        
        # Pasta de anexos
        anexos_dir = Path(__file__).parent.parent.parent / "anexos" / entity_type
        anexos_dir.mkdir(parents=True, exist_ok=True)
        
        original_name = os.path.basename(file_path)
        ext = os.path.splitext(original_name)[1]
        unique_name = f"{entity_type}_{entity_id}_{dt.now().strftime('%Y%m%d%H%M%S')}{ext}"
        dest_path = anexos_dir / unique_name
        
        shutil.copy2(file_path, dest_path)
        
        ext_lower = ext.lower()
        mime_map = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.pdf': 'application/pdf'}
        mime = mime_map.get(ext_lower, 'application/octet-stream')
        
        categoria = 'foto' if ext_lower in ['.png', '.jpg', '.jpeg'] else ('pdf' if ext_lower == '.pdf' else 'outro')
        
        anexo = Attachment(
            entity_type=entity_type, entity_id=entity_id,
            filename=unique_name, original_name=original_name,
            file_path=str(dest_path), mime_type=mime,
            size_bytes=os.path.getsize(dest_path), categoria=categoria,
            uploader_id=self.user['id'] if self.user else None
        )
        
        self.session.add(anexo)
        self.session.commit()
        
        # Remove a aba de anexos antiga
        tabs.removeTab(1)
        
        # Cria nova aba de anexos atualizada
        tab_anexos = self._criar_tab_anexos(entity_type, entity_id, dialog)
        tabs.addTab(tab_anexos, "📎 Anexos")
        tabs.setCurrentIndex(1)

    def _criar_tab_anexos(self, entity_type, entity_id, parent_dialog):
        """Cria a aba de anexos atualizada"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        anexos = self.session.query(Attachment).filter(
            Attachment.entity_type == entity_type,
            Attachment.entity_id == entity_id
        ).all()
        
        anexos_label = QLabel(f"📎 Anexos ({len(anexos)})")
        anexos_label.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 14px;")
        layout.addWidget(anexos_label)
        
        if anexos:
            anexos_tabela = QTableWidget()
            anexos_tabela.setColumnCount(4)
            anexos_tabela.setHorizontalHeaderLabels(["Nome", "Tipo", "Tamanho", "Data"])
            anexos_tabela.setStyleSheet("""
                QTableWidget { background-color: #0f3460; color: #e0e0e0; border: 1px solid #533483; border-radius: 8px; gridline-color: #1a1a3e; font-size: 12px; }
                QTableWidget::item { padding: 8px; }
                QTableWidget::item:hover { background-color: #1a1a4e; }
                QHeaderView::section { background-color: #16213e; color: #89b4fa; font-weight: bold; padding: 8px; border: none; border-bottom: 1px solid #533483; }
            """)
            anexos_tabela.setRowCount(len(anexos))
            for i, anexo in enumerate(anexos):
                anexos_tabela.setItem(i, 0, QTableWidgetItem(anexo.original_name))
                anexos_tabela.setItem(i, 1, QTableWidgetItem(anexo.categoria))
                anexos_tabela.setItem(i, 2, QTableWidgetItem(f"{anexo.size_bytes / 1024:.1f} KB"))
                anexos_tabela.setItem(i, 3, QTableWidgetItem(anexo.created_at.strftime("%d/%m/%Y %H:%M") if anexo.created_at else "-"))
             # Faz a tabela ocupar toda a largura
            header = anexos_tabela.horizontalHeader()
            header.setStretchLastSection(True)
            for i in range(4):
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            anexos_tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
            anexos_tabela.verticalHeader().setVisible(False)
            anexos_tabela.setMaximumHeight(200)
            
            # Duplo clique para abrir
            anexos_tabela.cellDoubleClicked.connect(lambda r, c: os.startfile(anexos[r].file_path) if os.path.exists(anexos[r].file_path) else None)
            
            # Clique direito para menu
            anexos_tabela.setContextMenuPolicy(Qt.CustomContextMenu)
            # Guarda referência para usar no lambda
            _anexos = anexos
            _tabela = anexos_tabela
            anexos_tabela.customContextMenuRequested.connect(
                lambda pos: self._menu_anexo_simples(pos, _tabela, _anexos)
            )
            
            layout.addWidget(anexos_tabela)
        else:
            sem = QLabel("Nenhum anexo encontrado.")
            sem.setStyleSheet("color: #a0a0b0; font-size: 13px; padding: 20px;")
            sem.setAlignment(Qt.AlignCenter)
            layout.addWidget(sem)
        
        btn_add = QPushButton("📎 Adicionar Anexo")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("QPushButton { background-color: #89b4fa; color: #1a1a2e; border-radius: 6px; padding: 10px; font-weight: bold; } QPushButton:hover { background-color: #74b4fa; }")
        btn_add.clicked.connect(lambda: self._anexar_e_recarregar(parent_dialog, entity_type, entity_id, self._tab_anexos_parent))
        layout.addWidget(btn_add)

        # Botão salvar também na aba de anexos
        btn_salvar_anexo = QPushButton("💾 Salvar Alterações")
        btn_salvar_anexo.setCursor(Qt.PointingHandCursor)
        btn_salvar_anexo.setStyleSheet("""
            QPushButton { 
                background-color: #a6e3a1; color: #1a1a2e; 
                border: none; border-radius: 8px; 
                padding: 10px 20px; font-size: 13px; font-weight: bold; 
            }
            QPushButton:hover { background-color: #94d89f; }
        """)
        layout.addWidget(btn_salvar_anexo)
        
        layout.addStretch()
        return tab

    def _menu_anexo_simples(self, pos, tabela, anexos):
        """Menu de contexto simples para anexos"""
        from PySide6.QtWidgets import QMenu
        
        row = tabela.rowAt(pos.y())
        if row < 0 or row >= len(anexos):
            return
        
        anexo = anexos[row]
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 8px; padding: 5px; }
            QMenu::item { padding: 10px 25px; border-radius: 4px; font-size: 13px; }
            QMenu::item:selected { background-color: #e94560; }
        """)
        
        abrir = menu.addAction("📂 Abrir Arquivo")
        excluir = menu.addAction("🗑️ Excluir Anexo")
        
        acao = menu.exec(tabela.viewport().mapToGlobal(pos))
        
        if acao == abrir:
            if os.path.exists(anexo.file_path):
                os.startfile(anexo.file_path)
        elif acao == excluir:
            resp = QMessageBox.question(
                self, "Confirmar", f"Excluir anexo '{anexo.original_name}'?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if resp == QMessageBox.Yes:
                if os.path.exists(anexo.file_path):
                    os.remove(anexo.file_path)
                self.session.delete(anexo)
                self.session.commit()
                # Remove a linha da tabela
                tabela.removeRow(row)

    def _menu_anexo(self, pos, tabela, anexos, atividade):
        """Menu de contexto para excluir anexo"""
        from PySide6.QtWidgets import QMenu
        
        row = tabela.rowAt(pos.y())
        if row < 0:
            return
        
        anexo = anexos[row]
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #0f3460; color: #e0e0e0; border: 1px solid #533483; border-radius: 6px; padding: 5px; }
            QMenu::item { padding: 8px 20px; border-radius: 4px; }
            QMenu::item:selected { background-color: #533483; }
        """)
        
        acao_excluir = menu.addAction("🗑️ Excluir Anexo")
        acao_abrir = menu.addAction("📂 Abrir Arquivo")
        
        acao = menu.exec(tabela.viewport().mapToGlobal(pos))
        
        if acao == acao_excluir:
            resposta = QMessageBox.question(
                self, "Confirmar", f"Excluir anexo '{anexo.original_name}'?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if resposta == QMessageBox.Yes:
                # Remove arquivo físico
                if os.path.exists(anexo.file_path):
                    os.remove(anexo.file_path)
                # Remove do banco
                self.session.delete(anexo)
                self.session.commit()
                # Recarrega a janela (fecha e reabre)
                QMessageBox.information(self, "Sucesso", "Anexo excluído! Reabra a janela para ver as alterações.")
        elif acao == acao_abrir:
            if os.path.exists(anexo.file_path):
                os.startfile(anexo.file_path)

    def _salvar_edicao_transferencia(self, dialog, atividade, printer_combo, data, pecas, origem, destino, recibo, obs, status):
        # Impressora
        printer_text = printer_combo.currentText().strip()
        if printer_text and " - " in printer_text:
            pat = printer_text.split(" - ")[0].strip()
            p = self.session.query(Printer).filter(Printer.patrimonio == pat).first()
            if p:
                atividade.printer_id = p.id
        
        # Data
        data_text = data.text().strip()
        if data_text:
            try:
                atividade.event_at = dt.strptime(data_text, "%d/%m/%Y %H:%M")
            except:
                try:
                    atividade.event_at = dt.strptime(data_text, "%d/%m/%Y")
                except:
                    pass
        
        atividade.parts_used = pecas.text().strip()
        atividade.from_location = origem.currentText().strip()
        atividade.to_location = destino.currentText().strip()
        atividade.numero_recibo = recibo.text().strip()
        atividade.notes = obs.toPlainText().strip()
        atividade.status_atividade = status.currentText()
        
        self.session.commit()
        self._carregar_tabela_transferencias()
        dialog.accept()
    
    def _excluir_transferencia(self, dialog, atividade):
        resposta = QMessageBox.question(
            dialog,
            "Confirmar Exclusão",
            "Deseja realmente excluir esta transferência?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if resposta == QMessageBox.Yes:
            self.session.delete(atividade)
            self.session.commit()
            self._carregar_tabela_transferencias()
            dialog.accept()
    
    def carregar_dados(self):
        total = self.session.query(Printer).count()
        status_manutencao = ["Em manutenção", "Manutenção", "Aguardando peça", "Parada"]
        em_manutencao = self.session.query(Printer).filter(Printer.status.in_(status_manutencao)).count()
        status_operacional = ["Operacional", "Em uso"]
        operacionais = self.session.query(Printer).filter(Printer.status.in_(status_operacional)).count()
        total_activities = self.session.query(Activity).count()
        self._atualizar_card(self.card_total, str(total))
        self._atualizar_card(self.card_manut, str(em_manutencao))
        self._atualizar_card(self.card_op, str(operacionais))
        self._atualizar_card(self.card_os, str(total_activities))
        self._carregar_tabela_impressoras()
    
    def _carregar_tabela_impressoras(self, filtro=None):
        query = self.session.query(Printer)
        if filtro:
            f = f"%{filtro}%"
            query = query.filter(Printer.patrimonio.like(f) | Printer.modelo.like(f) | Printer.serial.like(f) | Printer.local_atual.like(f) | Printer.marca.like(f))
        impressoras = query.order_by(Printer.patrimonio).all()
        self.tabela.setRowCount(len(impressoras))
        for i, p in enumerate(impressoras):
            self.tabela.setItem(i, 0, QTableWidgetItem(p.patrimonio))
            self.tabela.setItem(i, 1, QTableWidgetItem(p.modelo))
            self.tabela.setItem(i, 2, QTableWidgetItem(p.serial or "-"))
            self.tabela.setItem(i, 3, QTableWidgetItem(p.marca or "-"))
            status_item = QTableWidgetItem(p.status)
            status_item.setTextAlignment(Qt.AlignCenter)
            if p.status in ["Operacional", "Em uso"]:
                status_item.setForeground(QColor("#a6e3a1"))
            elif p.status in ["Em manutenção", "Manutenção"]:
                status_item.setForeground(QColor("#f9e2af"))
            elif p.status in ["Parada", "Sucata"]:
                status_item.setForeground(QColor("#f38ba8"))
            else:
                status_item.setForeground(QColor("#a0a0b0"))
            self.tabela.setItem(i, 4, status_item)
            self.tabela.setItem(i, 5, QTableWidgetItem(p.local_atual or "-"))
            num = self.session.query(Activity).filter(Activity.printer_id == p.id).count()
            self.tabela.setItem(i, 6, QTableWidgetItem(str(num)))
        self.tabela.resizeColumnsToContents()
        self.tabela.setColumnWidth(5, 200)
    
    def filtrar_impressoras(self, texto):
        self._carregar_tabela_impressoras(texto if texto else None)

    def _criar_pagina_relatorios(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        titulo = QLabel("📈 Relatórios e Gráficos")
        titulo.setStyleSheet("color: #e94560; font-size: 20px; font-weight: bold; background: transparent;")
        layout.addWidget(titulo)
        layout.addSpacing(10)
        
        # ====== BOTÃO RELATÓRIO PERSONALIZADO ======
        btn_relatorio = QPushButton("📊 Gerar Relatório Personalizado")
        btn_relatorio.setCursor(Qt.PointingHandCursor)
        btn_relatorio.setStyleSheet("""
            QPushButton { 
                background-color: #cba6f7; color: #1a1a2e; 
                border-radius: 10px; padding: 15px; 
                font-size: 16px; font-weight: bold; 
            }
            QPushButton:hover { background-color: #bb96e7; }
        """)
        btn_relatorio.clicked.connect(self._abrir_relatorio_dialog)
        layout.addWidget(btn_relatorio)
        layout.addSpacing(15)
        
        # ====== GRÁFICOS ======
        grid = QHBoxLayout()
        grid.setSpacing(15)
        
        col1 = QVBoxLayout()
        col1.setSpacing(15)
        self.canvas_status = self._criar_grafico_pizza()
        col1.addWidget(self.canvas_status)
        self.canvas_modelos = self._criar_grafico_barras()
        col1.addWidget(self.canvas_modelos)
        
        col2 = QVBoxLayout()
        col2.setSpacing(15)
        self.canvas_ativ_mes = self._criar_grafico_linhas()
        col2.addWidget(self.canvas_ativ_mes)
        self.canvas_pecas = self._criar_grafico_barras_horiz()
        col2.addWidget(self.canvas_pecas)
        
        grid.addLayout(col1)
        grid.addLayout(col2)
        layout.addLayout(grid)
        return page

    def _abrir_relatorio_dialog(self):
        from app.views.relatorio_dialog import RelatorioDialog
        dialog = RelatorioDialog(self.session, self)
        dialog.exec()

    def _exportar_impressoras(self, formato):
        from PySide6.QtWidgets import QFileDialog
        from app.services.relatorio_service import RelatorioService
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório", f"impressoras_{dt.now().strftime('%Y%m%d')}.{formato}",
            f"{'PDF' if formato == 'pdf' else 'Excel'} (*.{formato})"
        )
        if not filepath:
            return
        
        printers = self.session.query(Printer).order_by(Printer.patrimonio).all()
        
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
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório", f"atividades_{dt.now().strftime('%Y%m%d')}.{formato}",
            f"{'PDF' if formato == 'pdf' else 'Excel'} (*.{formato})"
        )
        if not filepath:
            return
        
        atividades = self.session.query(Activity).order_by(Activity.event_at.desc()).limit(500).all()
        
        try:
            if formato == 'pdf':
                RelatorioService.exportar_atividades_pdf(atividades, filepath)
            else:
                RelatorioService.exportar_atividades_excel(atividades, filepath)
            os.startfile(filepath)
            QMessageBox.information(self, "Sucesso", f"Relatório salvo em:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório: {str(e)}")
    
    

    def _criar_grafico_pizza(self):
        fig = Figure(figsize=(5, 4), facecolor='#1a1a2e')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1a1a2e')
        statuses = self.session.query(Printer.status, func.count(Printer.status)).group_by(Printer.status).all()
        if statuses:
            labels = [s[0] for s in statuses]
            sizes = [s[1] for s in statuses]
            colors = ['#a6e3a1', '#f9e2af', '#f38ba8', '#89b4fa', '#cba6f7', '#fab387']
            wedges, texts, autotexts = ax.pie(sizes, labels=None, autopct='%1.1f%%', colors=colors[:len(labels)], startangle=90, textprops={'color': 'white', 'fontsize': 9})
            ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1, 0.5), frameon=False, labelcolor='white', fontsize=8)
        ax.set_title('Impressoras por Status', color='#e94560', fontsize=12, fontweight='bold', pad=15)
        canvas = FigureCanvas(fig)
        canvas.setStyleSheet("background-color: #0f3460; border-radius: 10px; border: 1px solid #533483;")
        return canvas
    
    def _criar_grafico_barras(self):
        fig = Figure(figsize=(5, 4), facecolor='#1a1a2e')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1a1a2e')
        modelos = self.session.query(Printer.modelo, func.count(Printer.modelo)).group_by(Printer.modelo).order_by(func.count(Printer.modelo).desc()).limit(5).all()
        if modelos:
            names = [m[0] for m in modelos]
            counts = [m[1] for m in modelos]
            bars = ax.bar(names, counts, color=['#89b4fa', '#a6e3a1', '#f9e2af', '#cba6f7', '#fab387'])
            ax.tick_params(axis='x', colors='white', labelsize=7, rotation=15)
            ax.tick_params(axis='y', colors='white')
            for bar, count in zip(bars, counts):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, str(count), ha='center', va='bottom', color='white', fontsize=9)
        ax.set_title('Top 5 Modelos', color='#e94560', fontsize=12, fontweight='bold', pad=15)
        ax.spines['bottom'].set_color('#533483')
        ax.spines['left'].set_color('#533483')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        canvas = FigureCanvas(fig)
        canvas.setStyleSheet("background-color: #0f3460; border-radius: 10px; border: 1px solid #533483;")
        return canvas
    
    def _criar_grafico_linhas(self):
        fig = Figure(figsize=(5, 4), facecolor='#1a1a2e')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1a1a2e')
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai']
        manut = [5, 15, 25, 10, 8]
        mov = [3, 8, 15, 5, 4]
        ax.plot(meses, manut, 'o-', color='#f9e2af', linewidth=2, markersize=6, label='Manutenções')
        ax.plot(meses, mov, 's-', color='#89b4fa', linewidth=2, markersize=6, label='Movimentações')
        ax.fill_between(range(len(meses)), manut, alpha=0.2, color='#f9e2af')
        ax.fill_between(range(len(meses)), mov, alpha=0.2, color='#89b4fa')
        ax.legend(frameon=False, fontsize=8, labelcolor='white')
        ax.tick_params(colors='white')
        ax.set_title('Atividades por Mês', color='#e94560', fontsize=12, fontweight='bold', pad=15)
        ax.spines['bottom'].set_color('#533483')
        ax.spines['left'].set_color('#533483')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.2, color='white')
        canvas = FigureCanvas(fig)
        canvas.setStyleSheet("background-color: #0f3460; border-radius: 10px; border: 1px solid #533483;")
        return canvas
    
    def _criar_grafico_barras_horiz(self):
        fig = Figure(figsize=(5, 4), facecolor='#1a1a2e')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1a1a2e')
        pecas_count = Counter()
        atividades = self.session.query(Activity).filter(Activity.parts_used != "").all()
        for a in atividades:
            if a.parts_used:
                for peca in a.parts_used.split(','):
                    peca = peca.strip()
                    if peca:
                        pecas_count[peca] += 1
        top_pecas = pecas_count.most_common(8)
        if top_pecas:
            names = [p[0] for p in top_pecas]
            counts = [p[1] for p in top_pecas]
            colors = ['#89b4fa', '#a6e3a1', '#f9e2af', '#cba6f7', '#fab387', '#f38ba8', '#94e2d5', '#b4befe']
            bars = ax.barh(names, counts, color=colors[:len(names)])
            ax.tick_params(colors='white', labelsize=8)
            ax.invert_yaxis()
            for bar, count in zip(bars, counts):
                ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2, str(count), va='center', color='white', fontsize=9)
        ax.set_title('Peças Mais Trocadas', color='#e94560', fontsize=12, fontweight='bold', pad=15)
        ax.spines['bottom'].set_color('#533483')
        ax.spines['left'].set_color('#533483')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        canvas = FigureCanvas(fig)
        canvas.setStyleSheet("background-color: #0f3460; border-radius: 10px; border: 1px solid #533483;")
        return canvas

    def _nova_os(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("📋 Nova Ordem de Serviço")
        dialog.setFixedSize(550, 500)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #c0c0d0; font-size: 12px; }
            QLineEdit, QTextEdit { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; font-size: 13px; }
            QComboBox { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; }
            QPushButton { background-color: #e94560; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }
        """)
        
        layout = QFormLayout(dialog)
        layout.setSpacing(10)
        
        # Impressora
        printer_combo = QComboBox()
        printer_combo.setEditable(True)  
        printers = self.session.query(Printer).order_by(Printer.patrimonio).all()
        for p in printers:
            printer_combo.addItem(f"{p.patrimonio} - {p.modelo} ({p.local_atual or 'Sem local'})")
        layout.addRow("Impressora:", printer_combo)
        
        # Tipo
        tipo_combo = QComboBox()
        tipo_combo.addItems(["MANUTENCAO", "MOVIMENTACAO"])
        layout.addRow("Tipo:", tipo_combo)
        
        # Data do evento
        data_input = QLineEdit()
        data_input.setPlaceholderText("dd/mm/aaaa HH:MM")
        data_input.setText(dt.now().strftime("%d/%m/%Y %H:%M"))
        layout.addRow("Data/Hora:", data_input)
        
        # Descrição
        desc_input = QTextEdit()
        desc_input.setMaximumHeight(100)
        desc_input.setPlaceholderText("O que foi feito, diagnóstico, etc...")
        layout.addRow("Descrição:", desc_input)
        
        # Peças usadas
        pecas_input = QLineEdit()
        pecas_input.setPlaceholderText("Ex: Fusor, Placa Fonte, Cabo Flat...")
        layout.addRow("Peças Trocadas:", pecas_input)
        
        # === ORIGEM - ComboBox editável ===
        origem_combo = QComboBox()
        origem_combo.setEditable(True)
        origem_combo.addItem("")
        empresas = self.session.query(Company).order_by(Company.nome).all()
        for emp in empresas:
            origem_combo.addItem(emp.nome)
        layout.addRow("Origem:", origem_combo)
        
        # === DESTINO - ComboBox editável ===
        destino_combo = QComboBox()
        destino_combo.setEditable(True)
        destino_combo.addItem("")
        for emp in empresas:
            destino_combo.addItem(emp.nome)
        layout.addRow("Destino:", destino_combo)
        
        # Status
        status_combo = QComboBox()
        status_combo.addItems(["Concluida", "Pendente", "Em Andamento"])
        layout.addRow("Status:", status_combo)

        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.accepted.connect(lambda: self._salvar_os(dialog, printer_combo, tipo_combo, data_input, desc_input, pecas_input, origem_combo, destino_combo, status_combo))
        botoes.rejected.connect(dialog.reject)
        # Impede duplo clique
        botoes.accepted.disconnect()
        botoes.accepted.connect(lambda: self._salvar_os(dialog, printer_combo, tipo_combo, data_input, desc_input, pecas_input, origem_combo, destino_combo, status_combo))
        layout.addRow(botoes)
        
        dialog.exec()

    def _salvar_os(self, dialog, printer_combo, tipo_combo, data_input, desc_input, pecas_input, origem_combo, destino_combo, status_combo):
        printer_text = printer_combo.currentText().strip()
        if not printer_text:
            return
        
        if " - " in printer_text:
            pat = printer_text.split(" - ")[0].strip()
        else:
            pat = printer_text
        
        printer = self.session.query(Printer).filter(Printer.patrimonio == pat).first()
        
        if not printer:
            QMessageBox.warning(dialog, "Erro", f"Impressora '{pat}' não encontrada!")
            return
        
        data_evento = dt.now()
        data_text = data_input.text().strip()
        if data_text:
            try:
                data_evento = dt.strptime(data_text, "%d/%m/%Y %H:%M")
            except:
                try:
                    data_evento = dt.strptime(data_text, "%d/%m/%Y")
                except:
                    pass
        
        atividade = Activity(
            printer_id=printer.id,
            kind=tipo_combo.currentText(),
            event_at=data_evento,
            notes=desc_input.toPlainText().strip(),
            parts_used=pecas_input.text().strip(),
            from_location=origem_combo.currentText().strip(),
            to_location=destino_combo.currentText().strip(),
            status_atividade=status_combo.currentText()
        )
        
        self.session.add(atividade)
        self.session.commit()
        self._carregar_tabela_os()
        self._atualizar_cards_os()
        dialog.accept()

    def _editar_atividade(self, row, atividades, printer, parent_dialog):
        """Abre diálogo para editar uma atividade (nos detalhes da impressora)"""
        atividade = atividades[row]
        
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle("✏️ Editar Atividade")
        dialog.setFixedSize(500, 480)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #c0c0d0; font-size: 12px; }
            QLineEdit, QTextEdit { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; font-size: 13px; }
            QComboBox { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; }
            QPushButton { border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 12px; }
        """)
        
        layout = QFormLayout(dialog)
        layout.setSpacing(10)
        
        # Tipo
        tipo_combo = QComboBox()
        tipo_combo.addItems(["MANUTENCAO", "MOVIMENTACAO"])
        tipo_combo.setCurrentText(atividade.kind)
        layout.addRow("Tipo:", tipo_combo)
        
        # Data
        data_input = QLineEdit()
        data_input.setText(atividade.event_at.strftime("%d/%m/%Y %H:%M") if atividade.event_at else "")
        layout.addRow("Data/Hora:", data_input)
        
        # Descrição
        desc_input = QTextEdit()
        desc_input.setMaximumHeight(100)
        desc_input.setPlainText(atividade.notes or "")
        layout.addRow("Descrição:", desc_input)
        
        # Peças
        pecas_input = QLineEdit()
        pecas_input.setText(atividade.parts_used or "")
        layout.addRow("Peças:", pecas_input)
        
        # === ORIGEM - ComboBox ===
        origem_combo = QComboBox()
        origem_combo.setEditable(True)
        origem_combo.addItem("")
        empresas = self.session.query(Company).order_by(Company.nome).all()
        for emp in empresas:
            origem_combo.addItem(emp.nome)
        origem_combo.setCurrentText(atividade.from_location or "")
        layout.addRow("Origem:", origem_combo)
        
        # === DESTINO - ComboBox ===
        destino_combo = QComboBox()
        destino_combo.setEditable(True)
        destino_combo.addItem("")
        for emp in empresas:
            destino_combo.addItem(emp.nome)
        destino_combo.setCurrentText(atividade.to_location or "")
        layout.addRow("Destino:", destino_combo)
        
        # Status
        status_combo = QComboBox()
        status_combo.addItems(["Concluida", "Pendente", "Em Andamento"])
        status_combo.setCurrentText(atividade.status_atividade or "concluida")
        layout.addRow("Status:", status_combo)
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_salvar = QPushButton("💾 Salvar")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #1a1a2e; } QPushButton:hover { background-color: #94d89f; }")
        btn_salvar.clicked.connect(lambda: self._salvar_edicao_atividade(
            dialog, atividade, tipo_combo, data_input, desc_input, pecas_input, origem_combo, destino_combo, status_combo, printer, parent_dialog
        ))
        btn_layout.addWidget(btn_salvar)
        
        btn_excluir = QPushButton("🗑️ Excluir")
        btn_excluir.setCursor(Qt.PointingHandCursor)
        btn_excluir.setStyleSheet("QPushButton { background-color: #f38ba8; color: #1a1a2e; } QPushButton:hover { background-color: #eb7a94; }")
        btn_excluir.clicked.connect(lambda: self._excluir_atividade(dialog, atividade, printer, parent_dialog))
        btn_layout.addWidget(btn_excluir)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet("QPushButton { background-color: #e94560; color: white; } QPushButton:hover { background-color: #d63850; }")
        btn_cancelar.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancelar)
        
        layout.addRow(btn_layout)
        
        dialog.exec()
    
    def _salvar_edicao_atividade(self, dialog, atividade, tipo, data, desc, pecas, origem, destino, status, printer, parent_dialog):
        atividade.kind = tipo.currentText()
        data_text = data.text().strip()
        if data_text:
            try:
                atividade.event_at = dt.strptime(data_text, "%d/%m/%Y %H:%M")
            except:
                try:
                    atividade.event_at = dt.strptime(data_text, "%d/%m/%Y")
                except:
                    pass
        atividade.notes = desc.toPlainText().strip()
        atividade.parts_used = pecas.text().strip()
        atividade.from_location = origem.currentText().strip()
        atividade.to_location = destino.currentText().strip()
        atividade.status_atividade = status.currentText()
        self.session.commit()
        self.carregar_dados()
        dialog.accept()
    
    def _excluir_atividade(self, dialog, atividade, printer, parent_dialog):
        """Exclui uma atividade após confirmação"""
        resposta = QMessageBox.question(
            dialog,
            "Confirmar Exclusão",
            f"Deseja realmente excluir esta atividade?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if resposta == QMessageBox.Yes:
            self.session.delete(atividade)
            self.session.commit()
            self.carregar_dados()
            dialog.accept()

    def _editar_atividade_os(self, row, col):
        """Edita uma atividade a partir da tabela de OS"""
        # Pega o texto da coluna de patrimônio e descrição
        patrimonio = self.tabela_os.item(row, 1).text()
        descricao = self.tabela_os.item(row, 3).text()
        tipo_texto = self.tabela_os.item(row, 2).text()
        
        printer = self.session.query(Printer).filter(Printer.patrimonio == patrimonio).first()
        if not printer:
            QMessageBox.warning(self, "Erro", f"Impressora {patrimonio} não encontrada!")
            return
        
        # Busca a atividade mais recente com essa descrição
        atividade = self.session.query(Activity).filter(
            Activity.printer_id == printer.id,
            Activity.notes == descricao
        ).order_by(Activity.event_at.desc()).first()
        
        if not atividade:
            QMessageBox.warning(self, "Erro", "Atividade não encontrada!")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("✏️ Editar Atividade")
        dialog.setFixedSize(500, 480)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #c0c0d0; font-size: 12px; }
            QLineEdit, QTextEdit { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; font-size: 13px; }
            QComboBox { background-color: #0f3460; color: white; border: 2px solid #533483; border-radius: 6px; padding: 8px; }
            QPushButton { border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 12px; }
        """)
        
        layout = QFormLayout(dialog)
        layout.setSpacing(10)
        
        tipo_combo = QComboBox()
        tipo_combo.addItems(["MANUTENCAO", "MOVIMENTACAO"])
        tipo_combo.setCurrentText(atividade.kind)
        layout.addRow("Tipo:", tipo_combo)
        
        data_input = QLineEdit()
        data_input.setText(atividade.event_at.strftime("%d/%m/%Y %H:%M") if atividade.event_at else "")
        layout.addRow("Data/Hora:", data_input)
        
        desc_input = QTextEdit()
        desc_input.setMaximumHeight(100)
        desc_input.setPlainText(atividade.notes or "")
        layout.addRow("Descrição:", desc_input)
        
        pecas_input = QLineEdit()
        pecas_input.setText(atividade.parts_used or "")
        layout.addRow("Peças:", pecas_input)
        
        # ORIGEM - ComboBox
        origem_combo = QComboBox()
        origem_combo.setEditable(True)
        origem_combo.addItem("")
        empresas = self.session.query(Company).order_by(Company.nome).all()
        for emp in empresas:
            origem_combo.addItem(emp.nome)
        origem_combo.setCurrentText(atividade.from_location or "")
        layout.addRow("Origem:", origem_combo)
        
        # DESTINO - ComboBox
        destino_combo = QComboBox()
        destino_combo.setEditable(True)
        destino_combo.addItem("")
        for emp in empresas:
            destino_combo.addItem(emp.nome)
        destino_combo.setCurrentText(atividade.to_location or "")
        layout.addRow("Destino:", destino_combo)
        
        status_combo = QComboBox()
        status_combo.addItems(["Concluida", "Pendente", "Em Andamento"])
        status_combo.setCurrentText(atividade.status_atividade or "Concluida")
        layout.addRow("Status:", status_combo)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_anexo = QPushButton("📎 Anexos")
        btn_anexo.setCursor(Qt.PointingHandCursor)
        btn_anexo.setStyleSheet("QPushButton { background-color: #89b4fa; color: #1a1a2e; } QPushButton:hover { background-color: #74b4fa; }")
        btn_anexo.clicked.connect(lambda: self._anexar_arquivo("activity", atividade.id))
        btn_layout.addWidget(btn_anexo)
        
        btn_salvar = QPushButton("💾 Salvar")
        btn_salvar.setCursor(Qt.PointingHandCursor)
        btn_salvar.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #1a1a2e; } QPushButton:hover { background-color: #94d89f; }")
        btn_salvar.clicked.connect(lambda: self._salvar_atividade_os(dialog, atividade, tipo_combo, data_input, desc_input, pecas_input, origem_combo, destino_combo, status_combo))
        btn_layout.addWidget(btn_salvar)
        
        btn_excluir = QPushButton("🗑️ Excluir")
        btn_excluir.setCursor(Qt.PointingHandCursor)
        btn_excluir.setStyleSheet("QPushButton { background-color: #f38ba8; color: #1a1a2e; } QPushButton:hover { background-color: #eb7a94; }")
        btn_excluir.clicked.connect(lambda: self._excluir_atividade_os(dialog, atividade))
        btn_layout.addWidget(btn_excluir)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet("QPushButton { background-color: #e94560; color: white; } QPushButton:hover { background-color: #d63850; }")
        btn_cancelar.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancelar)
        
        layout.addRow(btn_layout)
        dialog.exec()
    
    def _salvar_atividade_os(self, dialog, atividade, tipo, data, desc, pecas, origem, destino, status):
        atividade.kind = tipo.currentText()
        data_text = data.text().strip()
        if data_text:
            try:
                atividade.event_at = dt.strptime(data_text, "%d/%m/%Y %H:%M")
            except:
                try:
                    atividade.event_at = dt.strptime(data_text, "%d/%m/%Y")
                except:
                    pass
        atividade.notes = desc.toPlainText().strip()
        atividade.parts_used = pecas.text().strip()
        atividade.from_location = origem.currentText().strip()
        atividade.to_location = destino.currentText().strip()
        atividade.status_atividade = status.currentText()
        self.session.commit()
        self._carregar_tabela_os()
        self._atualizar_cards_os()
        dialog.accept()
    
    def _excluir_atividade_os(self, dialog, atividade):
        resposta = QMessageBox.question(dialog, "Confirmar", "Excluir esta atividade?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resposta == QMessageBox.Yes:
            self.session.delete(atividade)
            self.session.commit()
            self._carregar_tabela_os()
            self._atualizar_cards_os()
            dialog.accept()

    def _anexar_arquivo(self, entity_type, entity_id):
        """Abre diálogo para selecionar e anexar um arquivo"""
        from PySide6.QtWidgets import QFileDialog
        import shutil
        import os
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo", "",
            "Todos os Arquivos (*.*);;Imagens (*.png *.jpg *.jpeg);;PDF (*.pdf);;Documentos (*.doc *.docx *.xls *.xlsx)"
        )
        
        if not file_path:
            return
        
        # Pasta de anexos
        anexos_dir = Path(__file__).parent.parent.parent / "anexos" / entity_type
        anexos_dir.mkdir(parents=True, exist_ok=True)
        
        # Nome único
        original_name = os.path.basename(file_path)
        ext = os.path.splitext(original_name)[1]
        unique_name = f"{entity_type}_{entity_id}_{dt.now().strftime('%Y%m%d%H%M%S')}{ext}"
        dest_path = anexos_dir / unique_name
        
        # Copia o arquivo
        shutil.copy2(file_path, dest_path)
        
        # Determina mime type
        ext_lower = ext.lower()
        mime_map = {
            '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword', '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel', '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.txt': 'text/plain', '.csv': 'text/csv',
        }
        mime = mime_map.get(ext_lower, 'application/octet-stream')
        
        # Categoria
        if ext_lower in ['.png', '.jpg', '.jpeg']:
            categoria = 'foto'
        elif ext_lower == '.pdf':
            categoria = 'pdf'
        elif ext_lower in ['.doc', '.docx']:
            categoria = 'documento'
        elif ext_lower in ['.xls', '.xlsx']:
            categoria = 'planilha'
        else:
            categoria = 'outro'
        
        # Salva no banco
        anexo = Attachment(
            entity_type=entity_type,
            entity_id=entity_id,
            filename=unique_name,
            original_name=original_name,
            file_path=str(dest_path),
            mime_type=mime,
            size_bytes=os.path.getsize(dest_path),
            categoria=categoria,
            uploader_id=self.user['id'] if self.user else None
        )
        
        self.session.add(anexo)
        self.session.commit()
        
        QMessageBox.information(self, "Sucesso", f"Arquivo '{original_name}' anexado com sucesso!")


