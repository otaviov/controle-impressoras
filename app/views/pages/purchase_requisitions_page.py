from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.utils.helpers import formatar_data_hora
from app.utils.ui_helpers import tratar_erro
from app.views.styles.theme import (
    ESTILO_BOTAO_AVISO,
    ESTILO_BOTAO_ERRO,
    ESTILO_BOTAO_SECUNDARIO,
    ESTILO_BOTAO_SUCESSO,
    ESTILO_TABELA_SIMPLES,
    ESTILO_TITULO_PAGINA,
    configurar_combo,
)
from app.views.widgets import ToastManager
from app.views.widgets.table_widget import tornar_interativa


class PurchaseRequisitionsPage(QWidget):
    session: Any
    part_service: Any
    _filtro_status: str | None
    _requisicoes: list[Any]
    combo_filtro: QComboBox
    tabela: QTableWidget
    btn_recarregar: QPushButton

    def __init__(self, session: Any, part_service: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        self.part_service = part_service
        self._filtro_status = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(10)

        titulo = QLabel("\U0001f6d2 Requisições de Compra")
        titulo.setStyleSheet(ESTILO_TITULO_PAGINA)
        header.addWidget(titulo)
        header.addStretch()

        self.combo_filtro = QComboBox()
        configurar_combo(self.combo_filtro)
        self.combo_filtro.addItems(["Todas", "pendente", "aprovada", "recebida", "cancelada"])
        self.combo_filtro.currentIndexChanged.connect(lambda: self._filtrar())
        header.addWidget(self.combo_filtro)

        self.btn_recarregar = QPushButton("\U0001f504 Recarregar")
        self.btn_recarregar.setStyleSheet(ESTILO_BOTAO_SECUNDARIO)
        self.btn_recarregar.setToolTip("Recarregar lista de requisições")
        self.btn_recarregar.clicked.connect(self._carregar)
        header.addWidget(self.btn_recarregar)

        layout.addLayout(header)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(7)
        self.tabela.setHorizontalHeaderLabels(["#", "Peça", "Qtd Sugerida", "Status", "Observação", "Criada em", "Ações"])
        self.tabela.setStyleSheet(ESTILO_TABELA_SIMPLES)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.verticalHeader().setDefaultSectionSize(36)
        layout.addWidget(self.tabela)

        self._requisicoes = []
        self._carregar()

    def recarregar(self) -> None:
        self._carregar()

    def _filtrar(self) -> None:
        texto = self.combo_filtro.currentText()
        self._filtro_status = texto if texto != "Todas" else None
        self._carregar()

    def _carregar(self) -> None:
        requisicoes = self.part_service.listar_requisicoes(status=self._filtro_status, limite=500)
        self._requisicoes = requisicoes
        self.tabela.setRowCount(len(requisicoes))

        status_cores = {
            "pendente": "#f59e0b",
            "aprovada": "#3b82f6",
            "recebida": "#10b981",
            "cancelada": "#717182",
        }

        for i, r in enumerate(requisicoes):
            items = [
                (str(r.id), None),
                (r.part.nome if r.part else "-", None),
                (str(r.quantidade_sugerida), None),
                (r.status, None),
                (r.observacao or "", None),
                (formatar_data_hora(r.created_at), None),
            ]
            for j, (texto, _) in enumerate(items):
                item = QTableWidgetItem(texto)
                item.setTextAlignment(Qt.AlignCenter if j in (2,) else Qt.AlignLeft)
                self.tabela.setItem(i, j, item)

            cor = status_cores.get(r.status, "#e8e8f0")
            self.tabela.item(i, 3).setForeground(QColor(cor))

            container = QWidget()
            row_layout = QHBoxLayout(container)
            row_layout.setContentsMargins(4, 2, 4, 2)
            row_layout.setSpacing(4)

            def make_handler(req_id: int, acao: str) -> Any:
                def handler() -> None:
                    if acao == "aprovar":
                        self._aprovar(req_id)
                    elif acao == "receber":
                        self._receber(req_id)
                    elif acao == "cancelar":
                        self._cancelar(req_id)
                return handler

            if r.status == "pendente":
                btn_aprovar = QPushButton("Aprovar")
                btn_aprovar.setStyleSheet(ESTILO_BOTAO_SUCESSO)
                btn_aprovar.setFixedHeight(28)
                btn_aprovar.clicked.connect(make_handler(r.id, "aprovar"))
                row_layout.addWidget(btn_aprovar)

                btn_receber = QPushButton("Receber")
                btn_receber.setStyleSheet(ESTILO_BOTAO_AVISO)
                btn_receber.setFixedHeight(28)
                btn_receber.clicked.connect(make_handler(r.id, "receber"))
                row_layout.addWidget(btn_receber)

                btn_cancelar = QPushButton("Cancelar")
                btn_cancelar.setStyleSheet(ESTILO_BOTAO_ERRO)
                btn_cancelar.setFixedHeight(28)
                btn_cancelar.clicked.connect(make_handler(r.id, "cancelar"))
                row_layout.addWidget(btn_cancelar)

            elif r.status == "aprovada":
                btn_receber = QPushButton("Receber")
                btn_receber.setStyleSheet(ESTILO_BOTAO_AVISO)
                btn_receber.setFixedHeight(28)
                btn_receber.clicked.connect(make_handler(r.id, "receber"))
                row_layout.addWidget(btn_receber)

                btn_cancelar = QPushButton("Cancelar")
                btn_cancelar.setStyleSheet(ESTILO_BOTAO_ERRO)
                btn_cancelar.setFixedHeight(28)
                btn_cancelar.clicked.connect(make_handler(r.id, "cancelar"))
                row_layout.addWidget(btn_cancelar)

            elif r.status == "recebida":
                pass

            elif r.status == "cancelada":
                pass

            self.tabela.setCellWidget(i, 6, container)

        tornar_interativa(self.tabela)
        self.tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabela.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabela.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tabela.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)

    def _executar_acao(self, req_id: int, acao: str) -> None:
        rotulos = {"aprovar": "aprovada", "receber": "recebida", "cancelar": "cancelada"}
        metodos = {
            "aprovar": self.part_service.aprovar_requisicao,
            "receber": self.part_service.receber_requisicao,
            "cancelar": self.part_service.cancelar_requisicao,
        }
        with tratar_erro(f"{acao} requisição"):
            metodos[acao](req_id)
            ToastManager.mostrar(f"Requisição #{req_id} {rotulos[acao]}.", "sucesso")
            self._carregar()

    def _aprovar(self, req_id: int) -> None:
        self._executar_acao(req_id, "aprovar")

    def _receber(self, req_id: int) -> None:
        self._executar_acao(req_id, "receber")

    def _cancelar(self, req_id: int) -> None:
        self._executar_acao(req_id, "cancelar")
