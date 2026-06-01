STATUS_CORES = {
    "Operacional": "#34d399",
    "Em uso": "#34d399",
    "Em manutenção": "#f97316",
    "Manutenção": "#f97316",
    "Aguardando peça": "#f59e0b",
    "Parada": "#ef4444",
    "Sucata": "#717182",
}

STATUS_MANUTENCAO = ["Em manutenção", "Manutenção", "Aguardando peça", "Parada"]
STATUS_OPERACIONAL = ["Operacional", "Em uso"]
STATUS_ATIVIDADE_OPCOES = ["Concluida", "Pendente", "Em Andamento"]
CORES_GRAFICO = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#3b82f6", "#06b6d4", "#f97316"]

# ── Paletas de cores (Figma shadcn/ui Dark) ─────────────
ESCURO = {
    "fundo": "#0a0a0f",
    "fundo_card": "#14141f",
    "fundo_input": "#1e1e2e",
    "tabela_bg": "#14141f",
    "borda": "#2a2a3e",
    "texto": "#e8e8f0",
    "texto_sec": "#c8c8d8",
    "roxo": "#6366f1",
    "roxo_escuro": "#4f46e5",
    "azul": "#3b82f6",
    "azul_escuro": "#2563eb",
    "hover": "#1e1e2e",
    "sucesso": "#10b981",
    "erro": "#ef4444",
    "aviso": "#f59e0b",
    "status_ok": "#34d399",
    "status_alerta": "#f59e0b",
    "status_ruim": "#ef4444",
    "sidebar": "#0f0f16",
    "topbar": "#0f0f16",
    "texto_muted": "#94949f",
    "texto_label": "#717182",
    "nav_text": "#717182",
    "nav_active_bg": "rgba(99, 102, 241, 0.12)",
    "nav_active_text": "#6366f1",
}

CLARO = {
    "fundo": "#f8fafc",
    "fundo_card": "#ffffff",
    "fundo_input": "#f3f3f5",
    "tabela_bg": "#ffffff",
    "borda": "#e2e8f0",
    "texto": "#0f172a",
    "texto_sec": "#475569",
    "roxo": "#6366f1",
    "roxo_escuro": "#4f46e5",
    "azul": "#3b82f6",
    "azul_escuro": "#2563eb",
    "hover": "#f1f5f9",
    "sucesso": "#10b981",
    "erro": "#ef4444",
    "aviso": "#f59e0b",
    "status_ok": "#34d399",
    "status_alerta": "#f59e0b",
    "status_ruim": "#ef4444",
    "sidebar": "#ffffff",
    "topbar": "#ffffff",
    "texto_muted": "#717182",
    "texto_label": "#94949f",
    "nav_text": "#64748b",
    "nav_active_bg": "#eef2ff",
    "nav_active_text": "#4f46e5",
}

_TEMA = "dark"
COR = dict(ESCURO)


def alternar():
    global _TEMA
    _TEMA = "light" if _TEMA == "dark" else "dark"
    paleta = CLARO if _TEMA == "light" else ESCURO
    COR.clear()
    COR.update(paleta)


def atual():
    return _TEMA


# ── ESTILOS (estáticos, tema escuro — Design System 2026) ──
# Inline stylesheets são LIMPOS no toggle via limpar_estilos().
# O QSS global cuida da aparência correta em cada tema.

ESTILO_BOTAO_PRIMARIO = """\
    QPushButton {
        background: #6366f1; color: #ffffff;
        border: none; border-radius: 8px;
        padding: 9px 18px; font-size: 11pt; font-weight: 600;
    }
    QPushButton:hover { background: #4f46e5; }
    QPushButton:pressed { background: #4338ca; }
"""

ESTILO_BOTAO_SUCESSO = """\
    QPushButton {
        background: #3b82f6; color: #ffffff;
        border: none; border-radius: 8px;
        padding: 9px 18px; font-size: 11pt; font-weight: 600;
    }
    QPushButton:hover { background: #2563eb; }
    QPushButton:pressed { background: #1d4ed8; }
"""

ESTILO_BOTAO_AVISO = """\
    QPushButton {
        background: #f97316; color: #ffffff;
        border: none; border-radius: 8px;
        padding: 9px 18px; font-size: 11pt; font-weight: 600;
    }
    QPushButton:hover { background: #ea580c; }
    QPushButton:pressed { background: #c2410c; }
"""

ESTILO_BOTAO_ERRO = """\
    QPushButton {
        background: #ef4444; color: #ffffff;
        border: none; border-radius: 8px;
        padding: 9px 18px; font-size: 11pt; font-weight: 600;
    }
    QPushButton:hover { background: #dc2626; }
    QPushButton:pressed { background: #b91c1c; }
"""

ESTILO_BOTAO_SECUNDARIO = """\
    QPushButton {
        background-color: transparent; color: #e8e8f0;
        border: 1px solid #2a2a3e; border-radius: 8px;
        padding: 9px 18px; font-size: 11pt; font-weight: 600;
    }
    QPushButton:hover { background-color: #1e1e2e; color: #e8e8f0; border-color: #6366f1; }
"""

ESTILO_BOTAO_FECHAR = """\
    QPushButton {
        background-color: transparent; color: #717182;
        border: 1px solid #2a2a3e; border-radius: 8px;
        padding: 9px 18px; font-size: 11pt; font-weight: 500;
    }
    QPushButton:hover { background-color: #1e1e2e; color: #e8e8f0; border-color: #3a3a50; }
"""

ESTILO_INPUT = """\
    QLineEdit, QTextEdit {
        background-color: #1e1e2e; color: #e8e8f0;
        border: 1px solid #2a2a3e; border-radius: 8px;
        padding: 8px 12px; font-size: 13px;
        selection-background-color: rgba(99, 102, 241, 0.25);
    }
    QLineEdit:hover, QTextEdit:hover { border-color: #3a3a50; }
    QLineEdit:focus, QTextEdit:focus { border-color: #6366f1; }
"""

ESTILO_INPUT_READONLY = """\
    QLineEdit, QTextEdit {
        background-color: #14141f; color: #717182;
        border: 1px solid #2a2a3e; border-radius: 8px;
        padding: 8px 12px; font-size: 13px;
    }
"""

ESTILO_COMBO = """\
    QComboBox {
        background-color: #1e1e2e; color: #e8e8f0;
        border: 1px solid #2a2a3e; border-radius: 8px;
        padding: 8px 12px; font-size: 13px;
        min-height: 20px;
    }
    QComboBox:hover { border-color: #3a3a50; }
    QComboBox:focus { border-color: #6366f1; }
    QComboBox:on { background-color: #1e1e2e; border-color: #6366f1; }
    QComboBox:disabled { background-color: #14141f; color: #3a3a50; border-color: #2a2a3e; }
    QComboBox QLineEdit { background-color: #1e1e2e; color: #e8e8f0; border: none; }
    QComboBox::drop-down { border: none; width: 30px; background: transparent; }
    QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #717182; width: 0; height: 0; margin-right: 8px; }
    QComboBox:hover::down-arrow { border-top-color: #6366f1; }
    QComboBox QAbstractItemView {
        background-color: #1e1e2e; color: #e8e8f0;
        border: 1px solid #2a2a3e; border-top: none;
        border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;
        selection-background-color: rgba(99, 102, 241, 0.15);
        selection-color: #818cf8; padding: 4px; outline: none;
    }
    QComboBox QAbstractItemView::item {
        padding: 8px 12px; min-height: 28px; border-radius: 6px;
        background-color: #1e1e2e; color: #e8e8f0;
    }
    QComboBox QAbstractItemView::item:hover {
        background-color: rgba(99, 102, 241, 0.15); color: #818cf8;
    }
    QComboBox QAbstractItemView::item:selected {
        background-color: rgba(99, 102, 241, 0.25); color: #a5b4fc;
    }
    QComboBox QAbstractItemView::viewport { background-color: #1e1e2e; }
    QComboBox QScrollBar:vertical {
        background: #1e1e2e; width: 8px; margin: 0;
        border: none; border-radius: 4px;
    }
    QComboBox QScrollBar::handle:vertical {
        background: #3a3a50; min-height: 30px; border-radius: 4px;
    }
    QComboBox QScrollBar::handle:vertical:hover { background: #52527a; }
    QComboBox QScrollBar::add-line:vertical, QComboBox QScrollBar::sub-line:vertical {
        height: 0; background: none; border: none;
    }
    QComboBox QScrollBar::add-page:vertical, QComboBox QScrollBar::sub-page:vertical {
        background: none;
    }
"""

ESTILO_TABELA = """\
    QTableWidget {
        background-color: rgba(20, 20, 31, 0.5); color: #e8e8f0;
        alternate-background-color: transparent;
        border: 1px solid rgba(42, 42, 62, 0.5); border-radius: 12px;
        gridline-color: transparent; selection-background-color: rgba(99, 102, 241, 0.15);
        font-size: 13px;
    }
    QTableWidget::item { padding: 11px 16px; border-bottom: 1px solid rgba(42, 42, 62, 0.3); }
    QTableWidget::item:hover { background-color: rgba(30, 30, 46, 0.5); color: #e8e8f0; }
    QTableWidget::item:selected { background-color: rgba(99, 102, 241, 0.15); color: #818cf8; font-weight: 600; }
    QHeaderView::section {
        background-color: transparent; color: #717182;
        font-weight: 700; padding: 10px 16px;
        border: none; border-bottom: 1px solid rgba(42, 42, 62, 0.5);
        font-size: 10px; letter-spacing: 0.8px; text-transform: uppercase;
    }
    QHeaderView::section:first { border-top-left-radius: 11px; }
    QHeaderView::section:last { border-top-right-radius: 11px; }
    QHeaderView::section:hover { background-color: rgba(30, 30, 46, 0.5); color: #94949f; }
    QTableWidget QTableCornerButton::section { background-color: transparent; border: none; }
"""

ESTILO_TABELA_SIMPLES = """\
    QTableWidget {
        background-color: #14141f; color: #e8e8f0;
        border: 1px solid #2a2a3e; border-radius: 10px;
        gridline-color: transparent; font-size: 12px;
    }
    QTableWidget::item { padding: 8px; }
    QHeaderView::section {
        background-color: #14141f; color: #717182;
        font-weight: 700; padding: 8px; border: none;
        border-bottom: 1px solid #2a2a3e;
    }
"""

ESTILO_DIALOG = """\
    QDialog { background-color: #14141f; }
    QLabel { color: #e8e8f0; font-size: 12px; background: transparent; }
    QLineEdit, QTextEdit {
        background-color: #1e1e2e; color: #e8e8f0;
        border: 1px solid #2a2a3e; border-radius: 8px;
        padding: 8px 12px; font-size: 13px;
    }
    QLineEdit:hover, QTextEdit:hover { border-color: #3a3a50; }
    QLineEdit:focus, QTextEdit:focus { border-color: #6366f1; }
"""

ESTILO_TITULO_PAGINA = "color: #e8e8f0; font-size: 22px; font-weight: 700; background: transparent; letter-spacing: -0.3px;"
ESTILO_SUBTITULO = "color: #94949f; font-size: 13px; background: transparent;"

ESTILO_VIDRO = "background-color: rgba(20, 20, 31, 0.5); border: 1px solid rgba(42, 42, 62, 0.5); border-radius: 12px;"

ESTILO_LABEL_VALOR = "font-weight: 600; background: transparent;"
ESTILO_LABEL_CAMPO = "color: #3b82f6; font-weight: 600; font-size: 12px;"


def _cor_rgba(hex_color, alpha=1.0):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

def estilo_botao_outline(cor, cor_hover=None, bg_hover=None):
    if cor_hover is None:
        cor_hover = cor
    if bg_hover is None:
        bg_hover = cor
    return f"""
    QPushButton {{
        background-color: {_cor_rgba(cor, 0.10)}; color: {cor};
        border: 1px solid {_cor_rgba(cor, 0.30)}; border-radius: 8px;
        padding: 9px 18px; font-size: 11pt; font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {bg_hover}; color: #ffffff;
        border: 1px solid {cor_hover};
    }}
    """


def estilos_dialogo_tabs():
    return f"""
    QTabWidget::pane {{ border: none; background: transparent; }}
    QTabBar::tab {{ background: transparent; color: #717182; padding: 10px 16px; border: none; border-bottom: 2px solid transparent; font-size: 13px; }}
    QTabBar::tab:selected {{ color: #e8e8f0; border-bottom-color: #6366f1; }}
    QTabBar::tab:hover {{ color: #94949f; }}
"""


def configurar_combo(combo):
    """Garante fundo escuro e habilita digitação em qualquer QComboBox.
    editable + read-only (contorna bug do Fusion que ignora
    background-color via stylesheet em combos não-editáveis)."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QComboBox as _QComboBox

    combo.setEditable(True)
    combo.setInsertPolicy(_QComboBox.NoInsert)
    combo.setMinimumHeight(38)

    le = combo.lineEdit()
    if le:
        le.setAlignment(Qt.AlignmentFlag.AlignLeft)
        le.setStyleSheet(
            "background-color: #1e1e2e; color: #e8e8f0;"
            " border: none;"
        )

    combo.setStyleSheet(
        "QComboBox { background-color: #1e1e2e; color: #e8e8f0;"
        " border: 1px solid #2a2a3e; border-radius: 8px;"
        " padding: 0px 12px; font-size: 13px;"
        " min-height: 36px; }"
        "QComboBox:hover { border-color: #3a3a50; }"
        "QComboBox:focus { border-color: #6366f1; }"
        "QComboBox:on { background-color: #1e1e2e; border-color: #6366f1; }"
        "QComboBox QLineEdit { background-color: #1e1e2e; color: #e8e8f0;"
        " border: none; }"
        "QComboBox::drop-down { border: none; width: 30px;"
        " background: transparent; }"
        "QComboBox::down-arrow {"
        " image: none; border-left: 5px solid transparent;"
        " border-right: 5px solid transparent;"
        " border-top: 6px solid #717182; width: 0; height: 0;"
        " margin-right: 8px; }"
        "QComboBox:disabled { background-color: #14141f;"
        " color: #3a3a50; }"
    )

    orig = combo.showPopup
    def _popup():
        orig()
        v = combo.view()
        if v:
            from PySide6.QtWidgets import QStyleFactory
            v.setStyle(QStyleFactory.create("Fusion"))
            v.setStyleSheet(
                "QListView { background-color: #1e1e2e; color: #e8e8f0; }"
                "QListView::item { background-color: #1e1e2e; color: #e8e8f0;"
                " padding: 8px 12px; }"
                "QListView::item:hover {"
                " background-color: rgba(99, 102, 241, 0.15);"
                " color: #818cf8; }"
                "QListView::item:selected {"
                " background-color: rgba(99, 102, 241, 0.25);"
                " color: #a5b4fc; }"
            )
    combo.showPopup = _popup
