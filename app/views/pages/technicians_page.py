from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.views.styles.theme import (
    ESTILO_BOTAO_AVISO,
    ESTILO_BOTAO_ERRO,
    ESTILO_BOTAO_SUCESSO,
    ESTILO_DIALOG,
    ESTILO_INPUT,
    ESTILO_TITULO_PAGINA,
)
from app.views.widgets.table_widget import TabelaPadrao


class _TechnicianDialog(QDialog):
    def __init__(self, parent=None, dados=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Técnico" if dados else "Novo Técnico")
        self.setMinimumWidth(400)
        self.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.input_nome = QLineEdit()
        self.input_nome.setStyleSheet(ESTILO_INPUT)
        self.input_nome.setPlaceholderText("Nome completo do técnico")
        self.input_nome.setMaxLength(100)

        self.input_exibicao = QLineEdit()
        self.input_exibicao.setStyleSheet(ESTILO_INPUT)
        self.input_exibicao.setPlaceholderText("Nome de exibição (apelido)")
        self.input_exibicao.setMaxLength(60)

        self.input_telefone = QLineEdit()
        self.input_telefone.setStyleSheet(ESTILO_INPUT)
        self.input_telefone.setPlaceholderText("(11) 99999-9999")
        self.input_telefone.setMaxLength(20)

        self.input_email = QLineEdit()
        self.input_email.setStyleSheet(ESTILO_INPUT)
        self.input_email.setPlaceholderText("email@exemplo.com")
        self.input_email.setMaxLength(100)

        form.addRow("Nome Completo:", self.input_nome)
        form.addRow("Nome Exibição:", self.input_exibicao)
        form.addRow("Telefone:", self.input_telefone)
        form.addRow("Email:", self.input_email)
        layout.addLayout(form)

        if dados:
            self.input_nome.setText(dados.get("nome_completo", ""))
            self.input_exibicao.setText(dados.get("nome_exibicao", ""))
            self.input_telefone.setText(dados.get("telefone", ""))
            self.input_email.setText(dados.get("email", ""))

            botoes = QHBoxLayout()
            self.btn_salvar = QPushButton("💾 Salvar")
            self.btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
            self.btn_salvar.clicked.connect(self.accept)

            self.btn_excluir = QPushButton("🗑️ Excluir")
            self.btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
            self.btn_excluir.clicked.connect(self._confirmar_exclusao)

            botoes.addWidget(self.btn_salvar)
            botoes.addWidget(self.btn_excluir)
            layout.addLayout(botoes)
        else:
            botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            botoes.accepted.connect(self.accept)
            botoes.rejected.connect(self.reject)
            botoes.button(QDialogButtonBox.Ok).setText("💾 Salvar")
            botoes.button(QDialogButtonBox.Cancel).setText("Cancelar")
            botoes.button(QDialogButtonBox.Ok).setStyleSheet(ESTILO_BOTAO_SUCESSO)
            botoes.button(QDialogButtonBox.Cancel).setStyleSheet(ESTILO_BOTAO_AVISO)
            layout.addWidget(botoes)

        self._excluir_confirmado = False

    def dados(self):
        return {
            "nome_completo": self.input_nome.text().strip(),
            "nome_exibicao": self.input_exibicao.text().strip(),
            "telefone": self.input_telefone.text().strip(),
            "email": self.input_email.text().strip(),
        }

    def _confirmar_exclusao(self):
        resposta = QMessageBox.question(
            self, "Confirmar Exclusão",
            "Tem certeza que deseja excluir este técnico?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resposta == QMessageBox.Yes:
            self._excluir_confirmado = True
            self.accept()

    def excluir_confirmado(self):
        return self._excluir_confirmado


class TechniciansPage(QWidget):
    COLUNAS = ["Nome Completo", "Exibição", "Telefone", "Email", "Ativo"]

    def __init__(self, session, technician_service, parent=None):
        super().__init__(parent)
        self._session = session
        self._technician_service = technician_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        titulo = QLabel("👨‍🔧 Técnicos")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        header.addWidget(titulo)
        header.addStretch()

        self.btn_novo = QPushButton("➕ Novo Técnico")
        self.btn_novo.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        self.btn_novo.clicked.connect(self._novo)
        header.addWidget(self.btn_novo)

        layout.addLayout(header)

        self.tabela = TabelaPadrao(self.COLUNAS)
        self.tabela.cellDoubleClicked.connect(self._editar)
        layout.addWidget(self.tabela, 1)

    def recarregar(self):
        tecnicos = self._technician_service.listar_todos()
        self.tabela.limpar()
        self.tabela.setRowCount(len(tecnicos))
        for i, t in enumerate(tecnicos):
            self.tabela.setItem(i, 0, QTableWidgetItem(t.nome_completo))
            self.tabela.setItem(i, 1, QTableWidgetItem(t.nome_exibicao))
            self.tabela.setItem(i, 2, QTableWidgetItem(t.telefone or ""))
            self.tabela.setItem(i, 3, QTableWidgetItem(t.email or ""))
            ativo = "✅" if t.ativo else "❌"
            item_ativo = QTableWidgetItem(ativo)
            item_ativo.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 4, item_ativo)
        self.tabela.redimensionar()

    def _novo(self):
        dialogo = _TechnicianDialog(self)
        if dialogo.exec() == QDialog.Accepted:
            dados = dialogo.dados()
            if not dados["nome_completo"]:
                QMessageBox.warning(self, "Aviso", "O campo Nome Completo é obrigatório.")
                return
            try:
                self._technician_service.criar(**dados)
                self.recarregar()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao criar técnico:\n{e}")

    def _editar(self, row):
        tecnicos = self._technician_service.listar_todos()
        if row < 0 or row >= len(tecnicos):
            return
        tecnico = tecnicos[row]
        dados = {
            "nome_completo": tecnico.nome_completo,
            "nome_exibicao": tecnico.nome_exibicao,
            "telefone": tecnico.telefone or "",
            "email": tecnico.email or "",
        }
        dialogo = _TechnicianDialog(self, dados)
        if dialogo.exec() == QDialog.Accepted:
            if dialogo.excluir_confirmado():
                try:
                    self._technician_service.excluir(tecnico.id)
                    self.recarregar()
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Erro ao excluir técnico:\n{e}")
            else:
                novos_dados = dialogo.dados()
                if not novos_dados["nome_completo"]:
                    QMessageBox.warning(self, "Aviso", "O campo Nome Completo é obrigatório.")
                    return
                try:
                    self._technician_service.atualizar(tecnico.id, **novos_dados)
                    self.recarregar()
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Erro ao atualizar técnico:\n{e}")
