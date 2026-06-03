import shutil
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import json

from app.utils.helpers import formatar_data_hora
from app.utils.ui_helpers import tratar_erro
from app.views.styles.theme import (
    COR,
    ESTILO_BOTAO_AVISO,
    ESTILO_BOTAO_FECHAR,
    ESTILO_BOTAO_PRIMARIO,
    ESTILO_BOTAO_SECUNDARIO,
    ESTILO_BOTAO_SUCESSO,
    ESTILO_BOTAO_ERRO,
    configurar_combo,
    ESTILO_COMBO,
    ESTILO_DIALOG,
    ESTILO_INPUT,
    ESTILO_INPUT_READONLY,
    ESTILO_SUBTITULO,
    ESTILO_TITULO_PAGINA,
)
from app.views.widgets.confirm_dialog import ConfirmacaoDigitarDialog
from app.views.widgets.table_widget import TabelaPadrao
from config import DB_PATH


class ConfigPage(QWidget):
    def __init__(self, session, user_service, user, notificador=None, audit_service=None, printer_service=None, part_service=None, company_service=None, activity_service=None, transfer_service=None, technician_service=None, alert_service=None, parent=None):
        super().__init__(parent)
        self.session = session
        self.user_service = user_service
        self.notificador = notificador
        self.audit_service = audit_service
        self.printer_service = printer_service
        self.part_service = part_service
        self.company_service = company_service
        self.activity_service = activity_service
        self.transfer_service = transfer_service
        self.technician_service = technician_service
        self.alert_service = alert_service
        self.user = user
        self._setup_ui()
        self.recarregar()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        header_text_layout = QVBoxLayout()
        titulo = QLabel("Configurações")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        header_text_layout.addWidget(titulo)
        subtitulo = QLabel("Gerencie usuários, backup e preferências")
        subtitulo.setStyleSheet(ESTILO_SUBTITULO)
        header_text_layout.addWidget(subtitulo)
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.abas = QTabWidget()
        self.abas.setStyleSheet("""
            QTabWidget::pane { border: none; background: transparent; margin-top: -1px; }
            QTabBar::tab { padding: 10px 20px; color: #94949f; font-weight: 600;
                background: transparent; border: none; border-bottom: 2px solid transparent; }
            QTabBar::tab:selected { color: #a78bfa; border-bottom: 2px solid #a78bfa; }
            QTabBar::tab:hover { color: #e8e8f0; }
        """)
        self.abas.addTab(self._criar_aba_usuarios(), "👥  Usuários")
        self.abas.addTab(self._criar_aba_backup(), "💾  Backup")
        self.abas.addTab(self._criar_aba_lixeira(), "🗑️  Lixeira")
        self.abas.addTab(self._criar_aba_auditoria(), "📋  Auditoria")
        self.abas.addTab(self._criar_aba_notificacoes(), "🔔  Notificações")
        layout.addWidget(self.abas)

    def _criar_aba_usuarios(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(12)

        self.tabela = TabelaPadrao(["Nome", "Usuário", "Email", "Perfil", "Ativo"])
        layout.addWidget(self.tabela)

        botoes = QHBoxLayout()
        botoes.setSpacing(10)
        self.btn_novo = QPushButton("➕ Novo Usuário")
        self.btn_novo.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        self.btn_novo.clicked.connect(self._novo_usuario)
        botoes.addWidget(self.btn_novo)
        self.btn_editar = QPushButton("✏️  Editar")
        self.btn_editar.setStyleSheet(ESTILO_BOTAO_AVISO)
        self.btn_editar.clicked.connect(self._editar_usuario)
        botoes.addWidget(self.btn_editar)
        botoes.addStretch()
        layout.addLayout(botoes)
        return tab

    def _criar_aba_backup(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(12)

        desc = QLabel("Faça backup do banco de dados SQLite para evitar perda de dados.")
        desc.setStyleSheet("color: #94a3b8; font-size: 12px; background: transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.btn_backup = QPushButton("📦  Fazer Backup Agora")
        self.btn_backup.setMinimumHeight(48)
        self.btn_backup.setCursor(Qt.PointingHandCursor)
        self.btn_backup.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #a78bfa, stop:1 #7c3aed);
                color: #ffffff;
                border: none; border-radius: 10px;
                padding: 14px 24px; font-size: 14px; font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #c4b5fd, stop:1 #a78bfa);
            }
        """)
        self.btn_backup.clicked.connect(self._fazer_backup)
        layout.addWidget(self.btn_backup)

        self.label_backup = QLabel("")
        self.label_backup.setStyleSheet("color: #475569; font-size: 12px; background: transparent; padding: 6px 0;")
        layout.addWidget(self.label_backup)

        layout.addStretch()
        return tab

    def _criar_aba_lixeira(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(12)

        desc = QLabel("Restaura registros que foram excluídos (soft delete).")
        desc.setStyleSheet("color: #94a3b8; font-size: 12px; background: transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.btn_lixeira = QPushButton("📂  Ver Registros Excluídos")
        self.btn_lixeira.setMinimumHeight(44)
        self.btn_lixeira.setCursor(Qt.PointingHandCursor)
        self.btn_lixeira.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ef4444, stop:1 #dc2626);
                color: #ffffff;
                border: none; border-radius: 10px;
                padding: 12px 20px; font-size: 13px; font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f87171, stop:1 #ef4444);
            }
        """)
        self.btn_lixeira.clicked.connect(self._abrir_lixeira)
        layout.addWidget(self.btn_lixeira)

        layout.addStretch()
        return tab

    def _criar_aba_notificacoes(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(12)

        desc = QLabel("Configure notificações para alertas críticos do sistema.")
        desc.setStyleSheet("color: #94a3b8; font-size: 12px; background: transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self._criar_notificacao_ui(layout)

        layout.addStretch()
        return tab

    def _criar_notificacao_ui(self, parent_layout):
        from app.services.notification_service import NotificacaoConfig

        self._notif_config = NotificacaoConfig.carregar()

        self._chk_desktop = QCheckBox("Notificação na área de trabalho (sistema)")
        self._chk_desktop.setChecked(self._notif_config.desktop_ativado)
        self._chk_desktop.setStyleSheet(
            "QCheckBox { color: #e2e8f0; font-size: 12px; spacing: 8px; }"
            " QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px;"
            " border: 2px solid #475569; background: transparent; }"
            " QCheckBox::indicator:checked { background-color: #a78bfa; border-color: #a78bfa; }"
        )
        parent_layout.addWidget(self._chk_desktop)

        self._chk_email = QCheckBox("Notificação por e-mail")
        self._chk_email.setChecked(self._notif_config.email_ativado)
        self._chk_email.setStyleSheet(
            "QCheckBox { color: #e2e8f0; font-size: 12px; spacing: 8px; margin-top: 4px; }"
            " QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px;"
            " border: 2px solid #475569; background: transparent; }"
            " QCheckBox::indicator:checked { background-color: #a78bfa; border-color: #a78bfa; }"
        )
        parent_layout.addWidget(self._chk_email)

        form_notif = QFormLayout()
        form_notif.setSpacing(8)
        form_notif.setContentsMargins(16, 8, 16, 0)

        self._input_smtp_host = QLineEdit()
        self._input_smtp_host.setStyleSheet(ESTILO_INPUT)
        self._input_smtp_host.setText(self._notif_config.smtp_host)
        self._input_smtp_host.setPlaceholderText("smtp.gmail.com")
        form_notif.addRow("SMTP Servidor:", self._input_smtp_host)

        self._input_smtp_port = QSpinBox()
        self._input_smtp_port.setRange(1, 65535)
        self._input_smtp_port.setValue(self._notif_config.smtp_port)
        self._input_smtp_port.setStyleSheet(ESTILO_INPUT)
        form_notif.addRow("SMTP Porta:", self._input_smtp_port)

        self._input_smtp_user = QLineEdit()
        self._input_smtp_user.setStyleSheet(ESTILO_INPUT)
        self._input_smtp_user.setText(self._notif_config.smtp_usuario)
        self._input_smtp_user.setPlaceholderText("seuemail@gmail.com")
        form_notif.addRow("SMTP Usuário:", self._input_smtp_user)

        self._input_smtp_senha = QLineEdit()
        self._input_smtp_senha.setStyleSheet(ESTILO_INPUT)
        self._input_smtp_senha.setText(self._notif_config.smtp_senha)
        self._input_smtp_senha.setEchoMode(QLineEdit.Password)
        self._input_smtp_senha.setPlaceholderText("senha ou app password")
        form_notif.addRow("SMTP Senha:", self._input_smtp_senha)

        self._input_email_de = QLineEdit()
        self._input_email_de.setStyleSheet(ESTILO_INPUT)
        self._input_email_de.setText(self._notif_config.email_remetente)
        self._input_email_de.setPlaceholderText("remetente@email.com")
        form_notif.addRow("E-mail remetente:", self._input_email_de)

        self._input_email_para = QLineEdit()
        self._input_email_para.setStyleSheet(ESTILO_INPUT)
        self._input_email_para.setText(self._notif_config.email_destinatario)
        self._input_email_para.setPlaceholderText("destinatario@email.com")
        form_notif.addRow("E-mail destinatário:", self._input_email_para)

        parent_layout.addLayout(form_notif)

        botoes_notif = QHBoxLayout()
        botoes_notif.setSpacing(10)

        btn_salvar_notif = QPushButton("💾 Salvar Configuração")
        btn_salvar_notif.setCursor(Qt.PointingHandCursor)
        btn_salvar_notif.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        btn_salvar_notif.clicked.connect(self._salvar_notificacao)
        botoes_notif.addWidget(btn_salvar_notif)

        btn_testar = QPushButton("📧 Testar E-mail")
        btn_testar.setCursor(Qt.PointingHandCursor)
        btn_testar.setStyleSheet(ESTILO_BOTAO_AVISO)
        btn_testar.clicked.connect(self._testar_email)
        botoes_notif.addWidget(btn_testar)

        botoes_notif.addStretch()
        parent_layout.addLayout(botoes_notif)

        self._lbl_status_notif = QLabel("")
        self._lbl_status_notif.setStyleSheet("color: #475569; font-size: 12px; background: transparent; padding: 4px 0;")
        parent_layout.addWidget(self._lbl_status_notif)

    def _salvar_notificacao(self):
        cfg = self._notif_config
        cfg.desktop_ativado = self._chk_desktop.isChecked()
        cfg.email_ativado = self._chk_email.isChecked()
        cfg.smtp_host = self._input_smtp_host.text().strip()
        cfg.smtp_port = self._input_smtp_port.value()
        cfg.smtp_usuario = self._input_smtp_user.text().strip()
        cfg.smtp_senha = self._input_smtp_senha.text()
        cfg.email_remetente = self._input_email_de.text().strip()
        cfg.email_destinatario = self._input_email_para.text().strip()
        cfg.salvar()
        if hasattr(self, "_notificador"):
            self._notificador.recarregar_config()
        self._lbl_status_notif.setStyleSheet("color: #34d399; font-size: 12px; background: transparent;")
        self._lbl_status_notif.setText("Configuração salva com sucesso!")

    def _testar_email(self):
        from app.services.notification_service import NotificacaoConfig
        cfg = NotificacaoConfig()
        cfg.desktop_ativado = self._chk_desktop.isChecked()
        cfg.email_ativado = True
        cfg.smtp_host = self._input_smtp_host.text().strip()
        cfg.smtp_port = self._input_smtp_port.value()
        cfg.smtp_usuario = self._input_smtp_user.text().strip()
        cfg.smtp_senha = self._input_smtp_senha.text()
        cfg.email_remetente = self._input_email_de.text().strip()
        cfg.email_destinatario = self._input_email_para.text().strip()

        self._lbl_status_notif.setStyleSheet("color: #fbbf24; font-size: 12px; background: transparent;")
        self._lbl_status_notif.setText("Enviando e-mail de teste...")
        ok, msg = cfg.testar_email()
        if ok:
            self._lbl_status_notif.setStyleSheet("color: #34d399; font-size: 12px; background: transparent;")
        else:
            self._lbl_status_notif.setStyleSheet("color: #f87171; font-size: 12px; background: transparent;")
        self._lbl_status_notif.setText(msg)

    def recarregar(self):
        usuarios = self.user_service.listar_todos()
        self.tabela.limpar()
        self.tabela.setRowCount(len(usuarios))
        for i, u in enumerate(usuarios):
            self.tabela.setItem(i, 0, QTableWidgetItem(u.nome))
            self.tabela.setItem(i, 1, QTableWidgetItem(u.username))
            self.tabela.setItem(i, 2, QTableWidgetItem(u.email))

            cor_perfil = "#a78bfa" if u.perfil == "admin" else "#60a5fa"
            self.tabela.definir_badge(i, 3, u.perfil.capitalize(), cor_perfil)

            cor_ativo = "#34d399" if u.ativo else "#475569"
            self.tabela.definir_badge(i, 4, "Sim" if u.ativo else "Não", cor_ativo)

        self.tabela.redimensionar()

    def _novo_usuario(self):
        dialog = _UserDialog(self, self.user_service, modo="novo")
        if dialog.exec() == QDialog.Accepted:
            self.recarregar()

    def _editar_usuario(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um usuário para editar.")
            return
        usuarios = self.user_service.listar_todos()
        if linha >= len(usuarios):
            return
        usuario = usuarios[linha]
        dialog = _UserDialog(self, self.user_service, modo="editar", usuario=usuario)
        if dialog.exec() == QDialog.Accepted:
            self.recarregar()

    def _abrir_lixeira(self):
        servicos = [
            ("Impressoras", self.printer_service, ["Patrimônio", "Modelo", "Marca", "Serial", "Status", "Local", "Excluído em"],
             lambda r: [r.patrimonio or "-", r.modelo or "-", r.marca or "-", r.serial or "-", r.status or "-", r.local_atual or "-", formatar_data_hora(r.deleted_at)]),
            ("Peças", self.part_service, ["Nome", "Código", "Modelo Compatível", "Qtd Estoque", "Estoque Mín.", "Excluído em"],
             lambda r: [r.nome or "-", r.codigo or "-", r.modelo_compativel or "-", str(r.quantidade_estoque), str(r.estoque_minimo), formatar_data_hora(r.deleted_at)]),
            ("Clientes", self.company_service, ["Nome", "CNPJ", "Telefone", "Email", "Tipo", "Excluído em"],
             lambda r: [r.nome or "-", r.cnpj or "-", r.telefone or "-", r.email or "-", r.tipo or "-", formatar_data_hora(r.deleted_at)]),
            ("OS", self.activity_service, ["Tipo", "Impressora", "Data", "Status", "Recibo", "Excluído em"],
             lambda r: [r.kind or "-", r.printer.patrimonio if r.printer else "-", formatar_data_hora(r.event_at), r.status_atividade or "-", r.numero_recibo or "-", formatar_data_hora(r.deleted_at)]),
            ("Transferências", self.transfer_service, ["Nº OS", "Tipo", "Data Saída", "Responsável", "Excluído em"],
             lambda r: [r.numero_os or "-", r.tipo or "-", formatar_data_hora(r.data_saida) if r.data_saida else "-", r.responsavel_entrega or "-", formatar_data_hora(r.deleted_at)]),
            ("Técnicos", self.technician_service, ["Nome", "Exibição", "Telefone", "Email", "Excluído em"],
             lambda r: [r.nome_completo or "-", r.nome_exibicao or "-", r.telefone or "-", r.email or "-", formatar_data_hora(r.deleted_at)]),
            ("Alertas", self.alert_service, ["Título", "Tipo", "Descrição", "Data", "Excluído em"],
             lambda r: [r.titulo or "-", r.tipo or "-", (r.descricao or "")[:80] + ("..." if len(r.descricao or "") > 80 else ""), formatar_data_hora(r.data_alerta) if r.data_alerta else "-", formatar_data_hora(r.deleted_at)]),
        ]
        dialog = QDialog(self)
        dialog.setWindowTitle("🗑️ Lixeira — Registros Excluídos")
        dialog.setMinimumSize(850, 500)
        dialog.setStyleSheet(ESTILO_DIALOG)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        abas = QTabWidget()
        abas.setStyleSheet("""
            QTabWidget::pane { border: none; background: transparent; }
            QTabBar::tab { padding: 8px 18px; color: #94949f; font-weight: 600;
                background: transparent; border: none; border-bottom: 2px solid transparent; }
            QTabBar::tab:selected { color: #ef4444; border-bottom: 2px solid #ef4444; }
            QTabBar::tab:hover { color: #e8e8f0; }
        """)

        for nome_tab, svc, colunas, extrair in servicos:
            if not svc:
                continue
            registros = svc.listar_excluidos() if hasattr(svc, "listar_excluidos") else []
            tab = self._criar_tab_lixeira(registros, colunas, extrair, svc, dialog)
            abas.addTab(tab, f"{nome_tab} ({len(registros)})")

        layout.addWidget(abas)
        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_fechar.clicked.connect(dialog.accept)
        layout.addWidget(btn_fechar, alignment=Qt.AlignCenter)
        dialog.exec()

    def _criar_tab_lixeira(self, registros, colunas, extrair, svc, parent_dialog):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)
        if not registros:
            layout.addWidget(QLabel("Nenhum registro excluído."))
            return tab

        tabela = TabelaPadrao(colunas)
        tabela.setRowCount(len(registros))
        for i, r in enumerate(registros):
            valores = extrair(r)
            for j, val in enumerate(valores):
                tabela.setItem(i, j, QTableWidgetItem(val))
        tabela.redimensionar()
        layout.addWidget(tabela)

        btn_restaurar = QPushButton("♻️ Restaurar Selecionado")
        btn_restaurar.setStyleSheet(ESTILO_BOTAO_PRIMARIO)
        btn_restaurar.clicked.connect(lambda: self._restaurar_selecionado(tabela, registros, svc, parent_dialog))
        layout.addWidget(btn_restaurar, alignment=Qt.AlignCenter)
        return tab

    def _restaurar_selecionado(self, tabela, registros, svc, dialog):
        row = tabela.currentRow()
        if row < 0 or row >= len(registros):
            QMessageBox.warning(self, "Aviso", "Selecione um registro para restaurar.")
            return
        obj = registros[row]
        if ConfirmacaoDigitarDialog.confirmar(
            "Confirmar",
            f"Restaurar '{getattr(obj, 'nome', getattr(obj, 'patrimonio', obj.id))}'?\n\n"
            "O registro voltará a aparecer nas listagens normais.",
            self,
        ):
            with tratar_erro("restaurar registro"):
                svc.restaurar(obj)
                QMessageBox.information(self, "Restaurado", "Registro restaurado com sucesso.")
                dialog.accept()
                self._abrir_lixeira()

    def _criar_aba_auditoria(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(12)

        desc = QLabel("Histórico de alterações feitas no sistema.")
        desc.setStyleSheet("color: #94a3b8; font-size: 12px; background: transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        filtros = QHBoxLayout()
        filtros.setSpacing(8)

        lbl_tabela = QLabel("Tabela:")
        lbl_tabela.setStyleSheet("color: #c8c8d8; font-size: 12px; background: transparent;")
        filtros.addWidget(lbl_tabela)

        self._combo_filtro_tabela = QComboBox()
        self._combo_filtro_tabela.addItems(["Todas", "printers", "activities", "companies", "parts", "technicians", "users", "alerts", "transfers"])
        self._combo_filtro_tabela.setStyleSheet(ESTILO_COMBO)
        self._combo_filtro_tabela.currentIndexChanged.connect(self._recarregar_auditoria)
        filtros.addWidget(self._combo_filtro_tabela)

        filtros.addStretch()

        btn_recarregar = QPushButton("🔄 Recarregar")
        btn_recarregar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        btn_recarregar.clicked.connect(self._recarregar_auditoria)
        filtros.addWidget(btn_recarregar)

        layout.addLayout(filtros)

        self._tabela_auditoria = TabelaPadrao(["Data/Hora", "Usuário", "Ação", "Tabela", "Registro"])
        self._tabela_auditoria.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabela_auditoria.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabela_auditoria.setAlternatingRowColors(True)
        self._tabela_auditoria.verticalHeader().setVisible(False)
        layout.addWidget(self._tabela_auditoria, stretch=1)

        botoes = QHBoxLayout()
        botoes.setSpacing(10)

        btn_detalhes = QPushButton("🔍 Ver Detalhes")
        btn_detalhes.setStyleSheet(ESTILO_BOTAO_AVISO)
        btn_detalhes.clicked.connect(self._detalhes_auditoria)
        botoes.addWidget(btn_detalhes)

        botoes.addStretch()
        layout.addLayout(botoes)

        self._logs_auditoria: list = []
        self._recarregar_auditoria()
        return tab

    def _recarregar_auditoria(self):
        if not self.audit_service:
            return
        filtro_tabela = self._combo_filtro_tabela.currentText()
        if filtro_tabela == "Todas":
            self._logs_auditoria = self.audit_service.listar(limite=200)
        else:
            self._logs_auditoria = self.audit_service.listar_por_tabela(filtro_tabela, limite=200)

        self._tabela_auditoria.limpar()
        self._tabela_auditoria.setRowCount(len(self._logs_auditoria))
        for i, log in enumerate(self._logs_auditoria):
            self._tabela_auditoria.setItem(i, 0, QTableWidgetItem(formatar_data_hora(log.created_at)))
            nome_user = log.user.nome if log.user else "-"
            self._tabela_auditoria.setItem(i, 1, QTableWidgetItem(nome_user))
            self._tabela_auditoria.setItem(i, 2, QTableWidgetItem(log.acao))
            self._tabela_auditoria.setItem(i, 3, QTableWidgetItem(log.tabela_alvo))
            self._tabela_auditoria.setItem(i, 4, QTableWidgetItem(log.registro_id))
        self._tabela_auditoria.redimensionar()

    def _detalhes_auditoria(self):
        row = self._tabela_auditoria.currentRow()
        if row < 0 or row >= len(self._logs_auditoria):
            QMessageBox.warning(self, "Aviso", "Selecione um registro para ver detalhes.")
            return
        log = self._logs_auditoria[row]

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Detalhes — #{log.id}")
        dialog.setMinimumSize(600, 400)
        dialog.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        info = QLabel(
            f"<b style='color:#a78bfa'>#{log.id}</b> — "
            f"<b style='color:#e8e8f0'>{log.acao}</b> "
            f"em <b style='color:#60a5fa'>{log.tabela_alvo}</b> "
            f"(registro {log.registro_id})<br>"
            f"<span style='color:#94949f'>Por: {log.user.nome if log.user else '-'} • {formatar_data_hora(log.created_at)}</span>"
        )
        info.setWordWrap(True)
        info.setStyleSheet("background: transparent; padding: 8px 0;")
        layout.addWidget(info)

        abas = QTabWidget()
        abas.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #2a2a3e; background: #16162a; border-radius: 6px; }
            QTabBar::tab { padding: 8px 16px; color: #94949f; font-weight: 600;
                background: transparent; border: none; }
            QTabBar::tab:selected { color: #a78bfa; border-bottom: 2px solid #a78bfa; }
        """)

        for titulo_aba, dado, cor in [("📦 Antes", log.dados_antes, "#f87171"),
                                       ("📦 Depois", log.dados_depois, "#34d399")]:
            tab_aba = QWidget()
            lay = QVBoxLayout(tab_aba)
            lay.setContentsMargins(12, 12, 12, 12)

            txt = QLabel()
            txt.setWordWrap(True)
            txt.setTextInteractionFlags(Qt.TextSelectableByMouse)
            if dado:
                try:
                    parsed = json.loads(dado)
                    formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                    txt.setText(f"<pre style='color:{cor}; font-size:12px; font-family:Courier New;'>{formatted}</pre>")
                except json.JSONDecodeError:
                    txt.setText(f"<pre style='color:{cor};'>{dado}</pre>")
            else:
                txt.setText("<span style='color:#475569;'>Sem dados</span>")
            lay.addWidget(txt)
            abas.addTab(tab_aba, titulo_aba)

        layout.addWidget(abas)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_fechar.clicked.connect(dialog.accept)
        layout.addWidget(btn_fechar, alignment=Qt.AlignCenter)

        dialog.exec()

    def _fazer_backup(self):
        try:
            backup_dir = DB_PATH.parent / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"backup_{timestamp}.db"
            destino = backup_dir / nome_arquivo
            shutil.copy2(str(DB_PATH), str(destino))
            self.label_backup.setStyleSheet("color: #34d399; font-size: 12px; background: transparent; padding: 6px 0;")
            self.label_backup.setText(f"Backup criado: {nome_arquivo}")
        except Exception as e:
            self.label_backup.setStyleSheet("color: #f87171; font-size: 12px; background: transparent; padding: 6px 0;")
            self.label_backup.setText(f"Erro: {e}")


class _UserDialog(QDialog):
    def __init__(self, parent, user_service, modo="novo", usuario=None):
        super().__init__(parent)
        self.user_service = user_service
        self.modo = modo
        self.usuario = usuario
        self._setup_ui()

    def _setup_ui(self):
        titulo = "Novo Usuário" if self.modo == "novo" else "Editar Usuário"
        self.setWindowTitle(titulo)
        self.setMinimumWidth(420)
        self.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.input_nome = QLineEdit()
        self.input_nome.setStyleSheet(ESTILO_INPUT)
        self.input_nome.setMaxLength(120)
        self.input_nome.setPlaceholderText("Nome completo")
        if self.usuario:
            self.input_nome.setText(self.usuario.nome)
        form.addRow("Nome:", self.input_nome)

        self.input_username = QLineEdit()
        self.input_username.setStyleSheet(ESTILO_INPUT)
        self.input_username.setMaxLength(50)
        self.input_username.setPlaceholderText("Nome de usuário")
        if self.usuario:
            self.input_username.setText(self.usuario.username)
        if self.modo == "editar":
            self.input_username.setReadOnly(True)
            self.input_username.setStyleSheet(ESTILO_INPUT_READONLY)
        form.addRow("Usuário:", self.input_username)

        self.input_email = QLineEdit()
        self.input_email.setStyleSheet(ESTILO_INPUT)
        self.input_email.setMaxLength(120)
        self.input_email.setPlaceholderText("email@exemplo.com")
        if self.usuario:
            self.input_email.setText(self.usuario.email)
        form.addRow("Email:", self.input_email)

        self.input_senha = QLineEdit()
        self.input_senha.setStyleSheet(ESTILO_INPUT)
        self.input_senha.setPlaceholderText("Digite a senha" if self.modo == "novo" else "Deixe em branco para manter")
        self.input_senha.setEchoMode(QLineEdit.Password)
        form.addRow("Senha:", self.input_senha)

        self.combo_perfil = QComboBox()
        configurar_combo(self.combo_perfil)
        self.combo_perfil.addItems(["admin", "tecnico", "visualizador"])
        if self.usuario:
            idx = self.combo_perfil.findText(self.usuario.perfil)
            if idx >= 0:
                self.combo_perfil.setCurrentIndex(idx)
        form.addRow("Perfil:", self.combo_perfil)

        if self.modo == "editar":
            self.combo_ativo = QComboBox()
            configurar_combo(self.combo_ativo)
            self.combo_ativo.addItems(["Sim", "Não"])
            if self.usuario and not self.usuario.ativo:
                self.combo_ativo.setCurrentIndex(1)
            form.addRow("Ativo:", self.combo_ativo)

        layout.addLayout(form)

        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.accepted.connect(self._validar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def _validar(self):
        nome = self.input_nome.text().strip()
        username = self.input_username.text().strip()
        email = self.input_email.text().strip()
        senha = self.input_senha.text()
        perfil = self.combo_perfil.currentText()

        if not nome:
            QMessageBox.warning(self, "Validação", "O campo Nome é obrigatório.")
            return
        if not username:
            QMessageBox.warning(self, "Validação", "O campo Usuário é obrigatório.")
            return
        if not email:
            QMessageBox.warning(self, "Validação", "O campo Email é obrigatório.")
            return
        if self.modo == "novo" and not senha:
            QMessageBox.warning(self, "Validação", "O campo Senha é obrigatório.")
            return

        with tratar_erro("salvar usuário"):
            if self.modo == "novo":
                if self.user_service.verificar_existente(email, username):
                    QMessageBox.warning(self, "Validação", "Usuário já existe.")
                    return
                self.user_service.criar(nome, username, email, senha, perfil)
            else:
                kwargs = {"nome": nome, "email": email, "perfil": perfil}
                if senha:
                    kwargs["senha"] = senha
                if hasattr(self, "combo_ativo"):
                    kwargs["ativo"] = self.combo_ativo.currentText() == "Sim"
                self.user_service.atualizar(self.usuario, **kwargs)
            self.accept()
