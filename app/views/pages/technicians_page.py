from __future__ import annotations

from typing import Any

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
    QScrollArea,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.views.styles.theme import (
    ESTILO_BOTAO_AVISO,
    ESTILO_BOTAO_ERRO,
    ESTILO_BOTAO_FECHAR,
    ESTILO_BOTAO_SUCESSO,
    ESTILO_DIALOG,
    ESTILO_INPUT,
    ESTILO_TITULO_PAGINA,
    group_box,
    input_label,
    campo_rotulo,
    campo_readonly,
)
from app.utils.validacao import ValidadorCampo, obrigatorio, email
from app.views.widgets import ToastManager
from app.views.widgets.confirm_dialog import ConfirmacaoDigitarDialog
from app.views.widgets.pagination import PaginacaoWidget
from app.views.widgets.table_widget import TabelaPadrao


class _TechnicianDialog(QDialog):
    input_nome: QLineEdit
    input_exibicao: QLineEdit
    input_telefone: QLineEdit
    input_email: QLineEdit
    btn_salvar: QPushButton
    btn_excluir: QPushButton
    _excluir_confirmado: bool

    def __init__(self, parent: QWidget | None = None, dados: dict[str, Any] | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Editar Técnico" if dados else "Novo Técnico")
        self.setMinimumWidth(400)
        self.setStyleSheet(ESTILO_DIALOG)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Identificação ──
        id_box, id_layout = group_box("Identificação")
        id_form = QFormLayout()
        id_form.setLabelAlignment(Qt.AlignRight)

        self.input_nome = QLineEdit()
        self.input_nome.setStyleSheet(ESTILO_INPUT)
        self.input_nome.setPlaceholderText("Nome completo do técnico")
        self.input_nome.setMaxLength(150)

        self.input_exibicao = QLineEdit()
        self.input_exibicao.setStyleSheet(ESTILO_INPUT)
        self.input_exibicao.setPlaceholderText("Nome de exibição (apelido)")
        self.input_exibicao.setMaxLength(80)

        id_form.addRow("Nome Completo:", self.input_nome)

        erro_nome = QLabel()
        erro_nome.setStyleSheet("color: #ef4444; font-size: 10px; background: transparent;")
        erro_nome.hide()
        id_form.addRow("", erro_nome)

        id_form.addRow("Nome Exibição:", self.input_exibicao)
        id_layout.addLayout(id_form)
        layout.addWidget(id_box)

        # ── Contato ──
        ct_box, ct_layout = group_box("Contato")
        ct_form = QFormLayout()
        ct_form.setLabelAlignment(Qt.AlignRight)

        self.input_telefone = QLineEdit()
        self.input_telefone.setStyleSheet(ESTILO_INPUT)
        self.input_telefone.setPlaceholderText("(81) 99999-9999")
        self.input_telefone.setMaxLength(20)

        self.input_email = QLineEdit()
        self.input_email.setStyleSheet(ESTILO_INPUT)
        self.input_email.setPlaceholderText("email@exemplo.com")
        self.input_email.setMaxLength(120)

        ct_form.addRow("Telefone:", self.input_telefone)
        ct_form.addRow("Email:", self.input_email)

        erro_email = QLabel()
        erro_email.setStyleSheet("color: #ef4444; font-size: 10px; background: transparent;")
        erro_email.hide()
        ct_form.addRow("", erro_email)

        ct_layout.addLayout(ct_form)
        layout.addWidget(ct_box)

        ValidadorCampo(self.input_nome, obrigatorio, erro_nome)
        ValidadorCampo(self.input_email, email, erro_email)

        layout.addStretch()

        if dados:
            self.input_nome.setText(dados.get("nome_completo", ""))
            self.input_exibicao.setText(dados.get("nome_exibicao", ""))
            self.input_telefone.setText(dados.get("telefone", ""))
            self.input_email.setText(dados.get("email", ""))

            botoes = QHBoxLayout()
            self.btn_salvar = QPushButton("💾 Salvar")
            self.btn_salvar.setToolTip("Salvar dados do técnico")
            self.btn_salvar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
            self.btn_salvar.clicked.connect(self.accept)

            self.btn_excluir = QPushButton("🗑️ Excluir")
            self.btn_excluir.setToolTip("Excluir este técnico (pode ser desfeito pela Lixeira)")
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
            botoes.button(QDialogButtonBox.Ok).setToolTip("Salvar novo técnico")
            botoes.button(QDialogButtonBox.Cancel).setText("Cancelar")
            botoes.button(QDialogButtonBox.Cancel).setToolTip("Cancelar")
            botoes.button(QDialogButtonBox.Ok).setStyleSheet(ESTILO_BOTAO_SUCESSO)
            botoes.button(QDialogButtonBox.Cancel).setStyleSheet(ESTILO_BOTAO_AVISO)
            layout.addWidget(botoes)

        self._excluir_confirmado = False

    def dados(self) -> dict[str, str]:
        return {
            "nome_completo": self.input_nome.text().strip(),
            "nome_exibicao": self.input_exibicao.text().strip(),
            "telefone": self.input_telefone.text().strip(),
            "email": self.input_email.text().strip(),
        }

    def _confirmar_exclusao(self) -> None:
        if ConfirmacaoDigitarDialog.confirmar(
            "Confirmar Exclusão",
            "Tem certeza que deseja excluir este técnico?",
            self,
        ):
            self._excluir_confirmado = True
            self.accept()

    def excluir_confirmado(self) -> bool:
        return self._excluir_confirmado


class TechniciansPage(QWidget):
    COLUNAS: list[str] = ["Nome Completo", "Exibição", "Telefone", "Email", "Ativo"]

    _session: Any
    _technician_service: Any
    _tecnicos_visiveis: list[Any]
    btn_novo: QPushButton
    tabela: TabelaPadrao
    _paginacao: PaginacaoWidget

    def __init__(self, session: Any, technician_service: Any, parent: QWidget | None = None) -> None:
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
        self.btn_novo.setToolTip("Cadastrar novo técnico")
        self.btn_novo.setStyleSheet(ESTILO_BOTAO_SUCESSO)
        self.btn_novo.clicked.connect(self._novo)
        header.addWidget(self.btn_novo)

        layout.addLayout(header)

        self._tecnicos_visiveis = []
        self.tabela = TabelaPadrao(self.COLUNAS)
        self.tabela.cellDoubleClicked.connect(self._detalhes)
        layout.addWidget(self.tabela, 1)

        self._paginacao = PaginacaoWidget()
        self._paginacao.pagina_alterada.connect(lambda p: self._carregar())
        layout.addWidget(self._paginacao)

        self._carregar()

    def recarregar(self) -> None:
        self._carregar()

    def _carregar(self) -> None:
        tecnicos = self._technician_service.listar_todos(
            limite=self._paginacao.limit, offset=self._paginacao.offset
        )
        total = self._technician_service.contar_todos()
        self._paginacao.configurar(total, pagina_atual=self._paginacao.pagina,
                                   itens_por_pagina=self._paginacao.limit)
        self._tecnicos_visiveis = tecnicos
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

    def _novo(self) -> None:
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

    def _detalhes(self, row: int) -> None:
        if row < 0 or row >= len(self._tecnicos_visiveis):
            return
        tecnico = self._tecnicos_visiveis[row]

        dialog = QDialog(self)
        dialog.setWindowTitle(tecnico.nome_exibicao or "Técnico")
        dialog.setMinimumSize(500, 400)
        dialog.setStyleSheet(ESTILO_DIALOG)

        root = QVBoxLayout(dialog)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        # ── Identificação ──
        id_box, id_layout = group_box("Identificação")
        id_form = QFormLayout()
        id_form.setLabelAlignment(Qt.AlignRight)
        id_form.addRow(campo_rotulo("Nome Completo"), campo_readonly(tecnico.nome_completo))
        id_form.addRow(campo_rotulo("Nome Exibição"), campo_readonly(tecnico.nome_exibicao))
        id_layout.addLayout(id_form)
        layout.addWidget(id_box)

        # ── Contato ──
        ct_box, ct_layout = group_box("Contato")
        ct_form = QFormLayout()
        ct_form.setLabelAlignment(Qt.AlignRight)
        ct_form.addRow(campo_rotulo("Telefone"), campo_readonly(tecnico.telefone or "—"))
        ct_form.addRow(campo_rotulo("Email"), campo_readonly(tecnico.email or "—"))
        ct_layout.addLayout(ct_form)
        layout.addWidget(ct_box)

        layout.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll, 1)

        # ── Botões ──
        botoes = QHBoxLayout()
        botoes.setSpacing(10)
        botoes.setContentsMargins(24, 12, 24, 12)

        btn_editar = QPushButton("✏️  Editar")
        btn_editar.setStyleSheet(ESTILO_BOTAO_AVISO)
        btn_editar.clicked.connect(lambda: (dialog.accept(), self._editar(row)))

        btn_excluir = QPushButton("🗑️ Excluir")
        btn_excluir.setStyleSheet(ESTILO_BOTAO_ERRO)
        btn_excluir.clicked.connect(lambda: self._excluir_do_detalhes(tecnico, dialog))

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet(ESTILO_BOTAO_FECHAR)
        btn_fechar.clicked.connect(dialog.accept)

        botoes.addWidget(btn_editar)
        botoes.addWidget(btn_excluir)
        botoes.addStretch()
        botoes.addWidget(btn_fechar)
        root.addLayout(botoes)

        dialog.exec()

    def _excluir_do_detalhes(self, tecnico: Any, dialog: QDialog) -> None:
        from app.views.widgets.confirm_dialog import ConfirmacaoDigitarDialog
        if ConfirmacaoDigitarDialog.confirmar(
            "Confirmar Exclusão",
            "Tem certeza que deseja excluir este técnico?",
            dialog,
        ):
            try:
                self._technician_service.excluir(tecnico)
                ToastManager.mostrar(
                    f"Técnico '{tecnico.nome_exibicao or tecnico.nome_completo}' excluído.",
                    "aviso", duracao=8000,
                    acao=("Desfazer", lambda o=tecnico, svc=self._technician_service, pag=self: (svc.restaurar(o), pag.recarregar())),
                )
                dialog.accept()
                self.recarregar()
            except Exception as e:
                QMessageBox.critical(dialog, "Erro", f"Erro ao excluir técnico:\n{e}")

    def _editar(self, row: int) -> None:
        if row < 0 or row >= len(self._tecnicos_visiveis):
            return
        tecnico = self._tecnicos_visiveis[row]
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
                    self._technician_service.excluir(tecnico)
                    ToastManager.mostrar(
                        f"Técnico '{tecnico.nome_exibicao or tecnico.nome_completo}' excluído.",
                        "aviso", duracao=8000,
                        acao=("Desfazer", lambda o=tecnico, svc=self._technician_service, pag=self: (svc.restaurar(o), pag.recarregar())),
                    )
                    self.recarregar()
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Erro ao excluir técnico:\n{e}")
            else:
                novos_dados = dialogo.dados()
                if not novos_dados["nome_completo"]:
                    QMessageBox.warning(self, "Aviso", "O campo Nome Completo é obrigatório.")
                    return
                try:
                    self._technician_service.atualizar(tecnico, **novos_dados)
                    self.recarregar()
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Erro ao atualizar técnico:\n{e}")
