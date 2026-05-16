from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox, QMessageBox, QGroupBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from pathlib import Path
import shutil
from datetime import datetime
from app.views.styles.theme import (COR, ESTILO_TITULO_PAGINA, ESTILO_SUBTITULO, ESTILO_BOTAO_SUCESSO, ESTILO_BOTAO_AVISO, ESTILO_BOTAO_ERRO, ESTILO_BOTAO_FECHAR, ESTILO_INPUT, ESTILO_COMBO, ESTILO_TABELA, ESTILO_DIALOG)
from app.views.widgets.table_widget import TabelaPadrao
from config import DB_PATH


class ConfigPage(QWidget):
    def __init__(self, session, user_service, user, parent=None):
        super().__init__(parent)
        self.session = session
        self.user_service = user_service
        self.user = user
        self._setup_ui()
        self.recarregar()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        titulo = QLabel("\u2699\ufe0f Configurações do Sistema")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        layout.addWidget(titulo)

        subtitulo = QLabel("Gerenciamento de usuários (apenas administradores)")
        subtitulo.setStyleSheet(ESTILO_SUBTITULO)
        layout.addWidget(subtitulo)

        grupo_usuarios = QGroupBox("\U0001f465 Usuários do Sistema")
        grupo_usuarios.setStyleSheet("QGroupBox { color: #89b4fa; font-size: 14px; font-weight: bold; border: 1px solid #533483; border-radius: 10px; margin-top: 20px; padding: 20px 15px 15px 15px; } QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; }")
        layout_grupo = QVBoxLayout(grupo_usuarios)
        layout_grupo.setSpacing(12)

        self.tabela = TabelaPadrao(["Nome", "Usuário", "Email", "Perfil", "Ativo"])
        self.tabela.setAlternatingRowColors(True)
        layout_grupo.addWidget(self.tabela)

        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(10)

        self.btn_novo = QPushButton("➕ Novo Usuário")
        self.btn_novo.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        self.btn_novo.clicked.connect(self._novo_usuario)
        botoes_layout.addWidget(self.btn_novo)

        self.btn_editar = QPushButton("✏️ Editar Usuário")
        self.btn_editar.setStyleSheet(ESTILO_BOTAO_AVISO)
        self.btn_editar.clicked.connect(self._editar_usuario)
        botoes_layout.addWidget(self.btn_editar)

        botoes_layout.addStretch()
        layout_grupo.addLayout(botoes_layout)

        layout.addWidget(grupo_usuarios)

        grupo_backup = QGroupBox("\U0001f4be Backup do Banco de Dados")
        grupo_backup.setStyleSheet("QGroupBox { color: #89b4fa; font-size: 14px; font-weight: bold; border: 1px solid #533483; border-radius: 10px; margin-top: 20px; padding: 20px 15px 15px 15px; } QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; }")
        layout_backup = QVBoxLayout(grupo_backup)
        layout_backup.setSpacing(12)

        self.btn_backup = QPushButton("\U0001f4e6 Fazer Backup Agora")
        self.btn_backup.setStyleSheet(f"""
            QPushButton {{
                background-color: #89b4fa; color: #1a1a2e;
                border: none; border-radius: 8px;
                padding: 10px 20px; font-size: 13px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #7aa8f0; }}
        """)
        self.btn_backup.clicked.connect(self._fazer_backup)
        layout_backup.addWidget(self.btn_backup)

        self.label_backup = QLabel("")
        self.label_backup.setStyleSheet("color: #a0a0b0; font-size: 12px; background: transparent;")
        layout_backup.addWidget(self.label_backup)

        layout.addWidget(grupo_backup)
        layout.addStretch()

    def recarregar(self):
        usuarios = self.user_service.listar_todos()
        self.tabela.limpar()
        self.tabela.setRowCount(len(usuarios))
        for i, u in enumerate(usuarios):
            self.tabela.setItem(i, 0, QTableWidgetItem(u.nome))
            self.tabela.setItem(i, 1, QTableWidgetItem(u.username))
            self.tabela.setItem(i, 2, QTableWidgetItem(u.email))

            perfil_texto = u.perfil.capitalize()
            cor_perfil = COR.get("destaque", "#e94560") if u.perfil == "admin" else COR.get("azul", "#89b4fa")
            perfil_item = self.tabela.item_colorido(perfil_texto, cor_perfil)
            self.tabela.setItem(i, 3, perfil_item)

            ativo_texto = "Sim" if u.ativo else "Não"
            cor_ativo = COR.get("sucesso", "#a6e3a1") if u.ativo else COR.get("status_inativo", "#6b7280")
            ativo_item = self.tabela.item_colorido(ativo_texto, cor_ativo)
            self.tabela.setItem(i, 4, ativo_item)

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

    def _fazer_backup(self):
        try:
            backup_dir = DB_PATH.parent / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"backup_{timestamp}.db"
            destino = backup_dir / nome_arquivo
            shutil.copy2(str(DB_PATH), str(destino))
            self.label_backup.setStyleSheet("color: #a6e3a1; font-size: 12px; background: transparent;")
            self.label_backup.setText(f"Backup criado: {nome_arquivo}")
        except Exception as e:
            self.label_backup.setStyleSheet("color: #f38ba8; font-size: 12px; background: transparent;")
            self.label_backup.setText(f"Erro ao criar backup: {e}")


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
        self.input_nome.setPlaceholderText("Nome completo")
        if self.usuario:
            self.input_nome.setText(self.usuario.nome)
        form.addRow("Nome:", self.input_nome)

        self.input_username = QLineEdit()
        self.input_username.setStyleSheet(ESTILO_INPUT)
        self.input_username.setPlaceholderText("Nome de usuário")
        if self.usuario:
            self.input_username.setText(self.usuario.username)
        if self.modo == "editar":
            self.input_username.setReadOnly(True)
            self.input_username.setStyleSheet("""
                QLineEdit {
                    background-color: #16213e; color: #a0a0b0;
                    border: 1px solid #313244; border-radius: 6px;
                    padding: 8px; font-size: 13px;
                }
            """)
        form.addRow("Usuário:", self.input_username)

        self.input_email = QLineEdit()
        self.input_email.setStyleSheet(ESTILO_INPUT)
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
        self.combo_perfil.setStyleSheet(ESTILO_COMBO)
        self.combo_perfil.addItems(["admin", "tecnico", "visualizador"])
        if self.usuario:
            idx = self.combo_perfil.findText(self.usuario.perfil)
            if idx >= 0:
                self.combo_perfil.setCurrentIndex(idx)
        form.addRow("Perfil:", self.combo_perfil)

        if self.modo == "editar":
            self.combo_ativo = QComboBox()
            self.combo_ativo.setStyleSheet(ESTILO_COMBO)
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
            self.input_nome.setFocus()
            return
        if not username:
            QMessageBox.warning(self, "Validação", "O campo Usuário é obrigatório.")
            self.input_username.setFocus()
            return
        if not email:
            QMessageBox.warning(self, "Validação", "O campo Email é obrigatório.")
            self.input_email.setFocus()
            return

        if self.modo == "novo" and not senha:
            QMessageBox.warning(self, "Validação", "O campo Senha é obrigatório.")
            self.input_senha.setFocus()
            return

        if self.modo == "novo":
            existente = self.user_service.verificar_existente(email, username)
            if existente:
                QMessageBox.warning(self, "Validação", "Já existe um usuário com este email ou nome de usuário.")
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
