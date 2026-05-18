COR = {
    "fundo": "#1e1e2e",
    "fundo_card": "#313244",
    "fundo_input": "#313244",
    "fundo_sidebar": "#1e1e2e",
    "fundo_tabela": "#313244",
    "header_tabela": "#1e1e2e",
    "linha_grid": "#45475a",
    "linha_tabela_alt": "#313244",
    "borda": "#585b70",
    "borda_foco": "#cba6f7",
    "texto_primario": "#cdd6f4",
    "texto_secundario": "#a6adc8",
    "texto_label": "#cdd6f4",
    "texto_destaque": "#cba6f7",
    "texto_link": "#89b4fa",
    "sucesso": "#89b4fa",
    "aviso": "#f9e2af",
    "erro": "#f38ba8",
    "roxo": "#cba6f7",
    "roxo_claro": "#cba6f7",
    "azul": "#89b4fa",
    "destaque": "#cba6f7",
    "hover_card": "#45475a",
    "selecao": "rgba(137, 180, 250, 0.2)",
    "status_ok": "#a6e3a1",
    "status_alerta": "#f9e2af",
    "status_ruim": "#f38ba8",
    "status_inativo": "#6c7086",
    "sidebar_bg": "#1e1e2e",
    "sidebar_hover": "#313244",
    "sidebar_selected": "#45475a",
    "sidebar_text": "#6c7086",
    "sidebar_text_hover": "#a6adc8",
    "sidebar_text_selected": "#cba6f7",
    "sidebar_border": "#45475a",
    "gradient": "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #cba6f7,stop:1 #ff6b6b)",
}

ESTILO_BOTAO_PRIMARIO = """
    QPushButton {
        background-color: #cba6f7; color: #1e1e2e;
        border: none; border-radius: 8px;
        padding: 9px 18px; font-size: 11pt; font-weight: 600;
    }
    QPushButton:hover { background-color: #b4befe; }
    QPushButton:pressed { background-color: #a6adc8; }
"""

ESTILO_BOTAO_SUCESSO = """
    QPushButton {
        background-color: #89b4fa; color: #1e1e2e;
        border: none; border-radius: 8px;
        padding: 10px 20px; font-size: 13px; font-weight: 600;
    }
    QPushButton:hover { background-color: #74c7ec; }
"""

ESTILO_BOTAO_AVISO = """
    QPushButton {
        background-color: #fab387; color: #1e1e2e;
        border: none; border-radius: 8px;
        padding: 10px 20px; font-size: 13px; font-weight: 600;
    }
    QPushButton:hover { background-color: #f9e2af; }
"""

ESTILO_BOTAO_ERRO = """
    QPushButton {
        background-color: #f38ba8; color: #1e1e2e;
        border: none; border-radius: 8px;
        padding: 10px 20px; font-size: 13px; font-weight: 600;
    }
    QPushButton:hover { background-color: #eba0ac; }
"""

ESTILO_BOTAO_SECUNDARIO = """
    QPushButton {
        background-color: #45475a; color: #a6adc8;
        border: 1px solid #585b70; border-radius: 8px;
        padding: 9px 18px; font-size: 11pt; font-weight: 600;
    }
    QPushButton:hover { background-color: #585b70; color: #cdd6f4; border-color: #a6adc8; }
"""

ESTILO_BOTAO_FECHAR = """
    QPushButton {
        background-color: #45475a; color: #a6adc8;
        border: 1px solid #585b70; border-radius: 8px;
        padding: 10px 20px; font-size: 13px; font-weight: 600;
    }
    QPushButton:hover { background-color: #585b70; color: #cdd6f4; }
"""

ESTILO_INPUT = """
    QLineEdit, QTextEdit {
        background-color: #313244; color: #cdd6f4;
        border: 1px solid #585b70; border-radius: 8px;
        padding: 8px 12px; font-size: 13px;
    }
    QLineEdit:focus, QTextEdit:focus { border-color: #cba6f7; }
"""

ESTILO_INPUT_READONLY = """
    QLineEdit, QTextEdit {
        background-color: #1e1e2e; color: #6c7086;
        border: 1px solid #45475a; border-radius: 8px;
        padding: 8px 12px; font-size: 13px;
    }
"""

ESTILO_COMBO = """
    QComboBox {
        background-color: #313244; color: #cdd6f4;
        border: 1px solid #585b70; border-radius: 8px;
        padding: 8px 12px; font-size: 13px;
    }
    QComboBox:hover { border-color: #89b4fa; }
    QComboBox:disabled { background-color: #1e1e2e; color: #6c7086; border-color: #45475a; }
    QComboBox::drop-down { border: none; width: 30px; }
    QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #6c7086; }
    QComboBox:hover::down-arrow { border-top-color: #cba6f7; }
    QComboBox QAbstractItemView {
        background-color: #313244; color: #cdd6f4;
        selection-background-color: rgba(137, 180, 250, 0.2);
        font-size: 13px;
    }
    QComboBox QAbstractItemView::item { padding: 8px 12px; min-height: 28px; }
    QComboBox QAbstractItemView::item:hover { background-color: rgba(137, 180, 250, 0.13); color: #89b4fa; }
"""

ESTILO_TABELA = """
    QTableWidget {
        background-color: #313244; color: #cdd6f4;
        alternate-background-color: #313244;
        border: 1px solid #585b70; border-radius: 12px;
        gridline-color: #45475a; selection-background-color: rgba(137, 180, 250, 0.2);
        font-size: 13px;
    }
    QTableWidget::item { padding: 10px 12px; border: none; }
    QTableWidget::item:hover { background-color: #45475a; color: #cdd6f4; }
    QTableWidget::item:selected { background-color: rgba(137, 180, 250, 0.2); color: #89b4fa; font-weight: 600; }
    QHeaderView::section {
        background-color: #1e1e2e; color: #6c7086;
        font-weight: 700; padding: 10px 12px;
        border: none; border-bottom: 1px solid #45475a;
        font-size: 11px; letter-spacing: 0.5px;
    }
    QHeaderView::section:first { border-top-left-radius: 11px; }
    QHeaderView::section:last { border-top-right-radius: 11px; }
"""

ESTILO_TABELA_SIMPLES = """
    QTableWidget {
        background-color: #313244; color: #cdd6f4;
        border: 1px solid #585b70; border-radius: 10px;
        gridline-color: #45475a; font-size: 12px;
    }
    QTableWidget::item { padding: 8px; }
    QHeaderView::section {
        background-color: #1e1e2e; color: #6c7086;
        font-weight: 700; padding: 8px; border: none;
        border-bottom: 1px solid #45475a;
    }
"""

ESTILO_DIALOG = """
    QDialog { background-color: #1e1e2e; }
    QLabel { color: #cdd6f4; font-size: 12px; background: transparent; }
    QLineEdit, QTextEdit {
        background-color: #313244; color: #cdd6f4;
        border: 1px solid #585b70; border-radius: 8px;
        padding: 8px 12px; font-size: 13px;
    }
    QLineEdit:focus, QTextEdit:focus { border-color: #cba6f7; }
    QComboBox {
        background-color: #313244; color: #cdd6f4;
        border: 1px solid #585b70; border-radius: 8px;
        padding: 8px 12px; font-size: 13px;
    }
"""

ESTILO_TITULO_PAGINA = "color: #cba6f7; font-size: 22px; font-weight: 700; background: transparent; letter-spacing: -0.3px;"
ESTILO_SUBTITULO = "color: #6c7086; font-size: 13px; background: transparent;"
ESTILO_LABEL_VALOR = "font-weight: 600; background: transparent;"
ESTILO_LABEL_CAMPO = "color: #89b4fa; font-weight: 600; font-size: 12px;"

STATUS_CORES = {
    "Operacional": "#89b4fa",
    "Em uso": "#89b4fa",
    "Em manutenção": "#fab387",
    "Manutenção": "#fab387",
    "Aguardando peça": "#f9e2af",
    "Parada": "#f38ba8",
    "Sucata": "#6c7086",
}

STATUS_MANUTENCAO = ["Em manutenção", "Manutenção", "Aguardando peça", "Parada"]
STATUS_OPERACIONAL = ["Operacional", "Em uso"]

STATUS_ATIVIDADE_OPCOES = ["Concluida", "Pendente", "Em Andamento"]

CORES_GRAFICO = ["#cba6f7", "#89b4fa", "#fab387", "#f9e2af", "#a6e3a1", "#f38ba8", "#89dceb", "#f5c2e7"]


def estilos_dialogo_tabs():
    return """
        QTabWidget::pane {
            border: 1px solid #585b70;
            background-color: transparent;
            border-radius: 0 0 8px 8px;
        }
        QTabWidget { background: transparent; }
        QTabBar { background: transparent; }
        QTabBar::tab {
            background: transparent; color: #6c7086;
            border: none; border-bottom: 2px solid transparent;
            padding: 10px 20px; margin-right: 4px;
            font-size: 13px; font-weight: 500;
        }
        QTabBar::tab:hover { color: #a6adc8; border-bottom-color: #585b70; }
        QTabBar::tab:selected { color: #cba6f7; border-bottom-color: #cba6f7; font-weight: 700; }
        QTabBar::tab:focus { outline: none; }
    """
