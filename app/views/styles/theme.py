COR = {
    "fundo": "#1a1a2e",
    "fundo_card": "#0f3460",
    "fundo_input": "#0f3460",
    "fundo_sidebar": "#0f3460",
    "borda": "#533483",
    "borda_foco": "#e94560",
    "texto_primario": "#e2e8f0",
    "texto_secundario": "#a0a0b0",
    "texto_label": "#c0c0d0",
    "texto_destaque": "#e94560",
    "texto_link": "#89b4fa",
    "sucesso": "#a6e3a1",
    "aviso": "#f9e2af",
    "erro": "#f38ba8",
    "roxo": "#7c3aed",
    "roxo_claro": "#cba6f7",
    "azul": "#89b4fa",
    "destaque": "#e94560",
    "hover_card": "#1a1a4e",
    "selecao": "#533483",
    "linha_tabela_alt": "#16213e",
    "status_ok": "#10b981",
    "status_alerta": "#f59e0b",
    "status_ruim": "#ef4444",
    "status_inativo": "#6b7280",
    "sidebar_bg": "#0f3460",
    "sidebar_hover": "#141428",
    "sidebar_selected": "#1e1040",
    "sidebar_text": "#4a4a6a",
    "sidebar_text_hover": "#8888aa",
    "sidebar_text_selected": "#a78bfa",
    "sidebar_border": "#533483",
    "fundo_tabela": "#0f3460",
    "header_tabela": "#16213e",
    "linha_grid": "#1a1a3e",
}

ESTILO_BOTAO_PRIMARIO = """
    QPushButton {
        background-color: #e94560; color: white;
        border: none; border-radius: 8px;
        padding: 9px 18px; font-size: 11pt; font-weight: 600;
    }
    QPushButton:hover { background-color: #d63850; }
    QPushButton:pressed { background-color: #c02d43; }
"""

ESTILO_BOTAO_SUCESSO = """
    QPushButton {
        background-color: #a6e3a1; color: #1a1a2e;
        border: none; border-radius: 8px;
        padding: 10px 20px; font-size: 13px; font-weight: bold;
    }
    QPushButton:hover { background-color: #94d89f; }
"""

ESTILO_BOTAO_AVISO = """
    QPushButton {
        background-color: #f9e2af; color: #1a1a2e;
        border: none; border-radius: 8px;
        padding: 10px 20px; font-size: 13px; font-weight: bold;
    }
    QPushButton:hover { background-color: #f5d78c; }
"""

ESTILO_BOTAO_ERRO = """
    QPushButton {
        background-color: #f38ba8; color: #1a1a2e;
        border: none; border-radius: 8px;
        padding: 10px 20px; font-size: 13px; font-weight: bold;
    }
    QPushButton:hover { background-color: #eb7a94; }
"""

ESTILO_BOTAO_SECUNDARIO = """
    QPushButton {
        background-color: #141422; color: #6b7280;
        border: 1px solid #1e1e30; border-radius: 8px;
        padding: 9px 18px; font-size: 11pt; font-weight: 600;
    }
    QPushButton:hover { background-color: #1a1a2e; color: #c4c4e0; }
"""

ESTILO_BOTAO_FECHAR = """
    QPushButton {
        background-color: #e94560; color: white;
        border: none; border-radius: 8px;
        padding: 10px 20px; font-size: 13px; font-weight: bold;
    }
    QPushButton:hover { background-color: #d63850; }
"""

ESTILO_INPUT = """
    QLineEdit, QTextEdit {
        background-color: #0f3460; color: white;
        border: 2px solid #533483; border-radius: 6px;
        padding: 8px; font-size: 13px;
    }
    QLineEdit:focus, QTextEdit:focus { border-color: #e94560; }
"""

ESTILO_INPUT_READONLY = """
    QLineEdit, QTextEdit {
        background-color: #16213e; color: #a0a0b0;
        border: 1px solid #313244; border-radius: 6px;
        padding: 8px; font-size: 13px;
    }
"""

ESTILO_COMBO = """
    QComboBox {
        background-color: #0f3460; color: white;
        border: 2px solid #533483; border-radius: 6px;
        padding: 8px; font-size: 13px;
    }
    QComboBox:hover { border-color: #89b4fa; }
    QComboBox:disabled { background-color: #16213e; color: #a0a0b0; }
    QComboBox QAbstractItemView {
        background-color: #0f3460; color: white;
        selection-background-color: #533483;
        border: 1px solid #533483;
    }
    QComboBox QAbstractItemView::item { padding: 6px 12px; }
    QComboBox QAbstractItemView::item:hover { background-color: #e94560; }
"""

ESTILO_TABELA = """
    QTableWidget {
        background-color: #0f3460; color: #e0e0e0;
        border: 1px solid #533483; border-radius: 10px;
        gridline-color: #1a1a3e; selection-background-color: #533483;
        font-size: 13px;
    }
    QTableWidget::item { padding: 8px; }
    QTableWidget::item:hover { background-color: #1a1a4e; }
    QTableWidget::item:selected { background-color: #533483; color: white; }
    QHeaderView::section {
        background-color: #16213e; color: #89b4fa;
        font-weight: bold; padding: 10px 8px;
        border: none; border-bottom: 2px solid #e94560;
        font-size: 12px;
    }
"""

ESTILO_TABELA_SIMPLES = """
    QTableWidget {
        background-color: #0f3460; color: #e0e0e0;
        border: 1px solid #533483; border-radius: 8px;
        gridline-color: #1a1a3e; font-size: 12px;
    }
    QTableWidget::item { padding: 8px; }
    QHeaderView::section {
        background-color: #16213e; color: #89b4fa;
        font-weight: bold; padding: 8px; border: none;
    }
"""

ESTILO_DIALOG = """
    QDialog { background-color: #1a1a2e; color: #e0e0e0; }
    QLabel { color: #c0c0d0; font-size: 12px; background: transparent; }
"""

ESTILO_TITULO_PAGINA = "color: #e94560; font-size: 20px; font-weight: bold; background: transparent;"
ESTILO_SUBTITULO = "color: #a0a0b0; font-size: 13px; background: transparent;"
ESTILO_LABEL_VALOR = "font-weight: bold; background: transparent;"
ESTILO_LABEL_CAMPO = "color: #89b4fa; font-weight: bold; font-size: 12px;"

STATUS_CORES = {
    "Operacional": "#10b981",
    "Em uso": "#10b981",
    "Em manutenção": "#f59e0b",
    "Manutenção": "#f59e0b",
    "Aguardando peça": "#f59e0b",
    "Parada": "#ef4444",
    "Sucata": "#6b7280",
}

STATUS_MANUTENCAO = ["Em manutenção", "Manutenção", "Aguardando peça", "Parada"]
STATUS_OPERACIONAL = ["Operacional", "Em uso"]

STATUS_ATIVIDADE_OPCOES = ["Concluida", "Pendente", "Em Andamento"]


def estilos_dialogo_tabs():
    return """
        QTabWidget::pane {
            border: 1px solid #533483;
            background-color: #1a1a2e;
            border-radius: 8px;
        }
        QTabBar::tab {
            background-color: #0f3460; color: #a0a0b0;
            padding: 10px 20px;
            border: 1px solid #533483; border-bottom: none;
            border-top-left-radius: 8px; border-top-right-radius: 8px;
            font-size: 13px;
        }
        QTabBar::tab:selected {
            background-color: #1a1a2e; color: #e94560; font-weight: bold;
        }
    """
