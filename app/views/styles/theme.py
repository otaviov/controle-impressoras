from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from app.utils.constants import STATUS_MANUTENCAO, STATUS_OPERACIONAL, STATUS_ATIVIDADE_OPCOES

# ── Urgência / SLA ─────────────────────────────────────────────────────────────
URGENCIAS = ["Baixa", "Normal", "Alta", "Crítica"]
SLA_DIAS: dict[str, int] = {"Baixa": 30, "Normal": 15, "Alta": 3, "Crítica": 1}
URGENCIA_CORES: dict[str, str] = {
    "Baixa": "#a6e3a1",
    "Normal": "#f9e2af",
    "Alta": "#fab387",
    "Crítica": "#f38ba8",
}

STATUS_CORES: dict[str, str] = {
    "Operacional": "#34d399",
    "Em uso": "#34d399",
    "Em manutenção": "#f97316",
    "Manutenção": "#f97316",
    "Aguardando peça": "#f59e0b",
    "Parada": "#ef4444",
    "Sucata": "#717182",
}

ATIVIDADE_CORES: dict[str, str] = {
    "Aberta": "#94a3b8",
    "Aguardando Peça": "#f59e0b",
    "Técnico Designado": "#3b82f6",
    "Em Deslocamento": "#8b5cf6",
    "Em Manutenção": "#ef4444",
    "Em Atendimento": "#6366f1",
    "Aguardando Aprovação": "#f97316",
    "Concluido": "#10b981",
    "Verificada": "#34d399",
}

TIPO_ATIVIDADE_CORES: dict[str, str] = {
    "Todos": "#717182",
    "MANUTENCAO": "#f97316",
    "MOVIMENTACAO": "#3b82f6",
}

TIPO_CLIENTE_CORES: dict[str, str] = {
    "Cliente": "#6366f1",
    "Filial": "#34d399",
    "Parceiro": "#f59e0b",
}

PERFIL_CORES: dict[str, str] = {
    "admin": "#ef4444",
    "tecnico": "#3b82f6",
    "visualizador": "#717182",
}

SIM_NAO_CORES: dict[str, str] = {
    "Sim": "#10b981",
    "Não": "#ef4444",
}

CORES_GRAFICO: list[str] = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#3b82f6", "#06b6d4", "#f97316"]

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

_TEMA: str = "dark"
COR: dict[str, str] = dict(ESCURO)


def alternar() -> None:
    global _TEMA
    _TEMA = "light" if _TEMA == "dark" else "dark"
    paleta: dict[str, str] = CLARO if _TEMA == "light" else ESCURO
    COR.clear()
    COR.update(paleta)


def atual() -> str:
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
    QLineEdit, QTextEdit, QDateEdit, QTimeEdit, QDateTimeEdit, QComboBox {
        background-color: #1e1e2f; color: #e2e8f0;
        border: 2px solid #3b4261; border-radius: 8px;
        padding: 4px 10px; font-size: 13px;
    }
    QLineEdit, QDateEdit, QTimeEdit, QDateTimeEdit, QComboBox { min-height: 26px; }
    QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus, QComboBox:focus {
        border: 2px solid #3b82f6; background-color: #1a1b26; color: #ffffff;
    }
    QLineEdit:disabled, QTextEdit:disabled, QDateEdit:disabled, QTimeEdit:disabled, QDateTimeEdit:disabled, QComboBox:disabled {
        background-color: #14141f; color: #555568; border: 2px solid #1e1e2e;
    }
    QDateEdit::drop-down, QTimeEdit::drop-down, QDateTimeEdit::drop-down {
        border: none; width: 30px; background: transparent;
    }
    QDateEdit::down-arrow, QTimeEdit::down-arrow, QDateTimeEdit::down-arrow {
        image: none; border-left: 5px solid transparent; border-right: 5px solid transparent;
        border-top: 6px solid #717182; width: 0; height: 0; margin-right: 8px;
    }
    QDateEdit:hover::down-arrow, QTimeEdit:hover::down-arrow, QDateTimeEdit:hover::down-arrow {
        border-top-color: #6366f1;
    }
    QCalendarWidget {
        background-color: #1e1e2e; color: #e8e8f0;
        border: 1px solid #2a2a3e; border-radius: 8px;
    }
    QCalendarWidget QToolButton {
        color: #e8e8f0; background: transparent;
        padding: 6px 12px; border-radius: 6px; font-weight: 600;
    }
    QCalendarWidget QToolButton:hover { background: rgba(99, 102, 241, 0.15); }
    QCalendarWidget QMenu { background-color: #1e1e2e; color: #e8e8f0; border: 1px solid #2a2a3e; }
    QCalendarWidget QSpinBox { background-color: #1e1e2e; color: #e8e8f0; border: 1px solid #2a2a3e; border-radius: 6px; padding: 4px; }
    QCalendarWidget QTableView { border: none; background-color: #16162a; selection-background-color: rgba(99, 102, 241, 0.3); }
    QCalendarWidget QTableView::item:hover { background-color: rgba(99, 102, 241, 0.15); }
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


def _cor_rgba(hex_color: str, alpha: float = 1.0) -> str:
    h: str = hex_color.lstrip("#")
    r: int
    g: int
    b: int
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

def estilo_botao_outline(cor: str, cor_hover: str | None = None, bg_hover: str | None = None) -> str:
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


def configurar_combo(combo: QComboBox) -> None:
    """Garante fundo escuro e habilita digitação em qualquer QComboBox.
    editable + read-only (contorna bug do Fusion que ignora
    background-color via stylesheet em combos não-editáveis)."""
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.NoInsert)
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

    orig: Callable[[], Any] = combo.showPopup
    def _popup() -> None:
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


def input_label(texto: str) -> QLabel:
    """Label para campos de formulário (cinza, uppercase)."""
    lbl = QLabel(texto)
    lbl.setStyleSheet(
        "color: #94949f; font-size: 10px; font-weight: 600;"
        " background: transparent; letter-spacing: 0.5px;"
        " text-transform: uppercase;"
    )
    return lbl


def group_box(titulo: str) -> tuple[QWidget, QVBoxLayout]:
    """Retorna um widget agrupado com título azul (#6366f1) e layout interno."""
    box = QWidget()
    box.setStyleSheet("background: transparent;")
    outer = QVBoxLayout(box)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(6)
    title_lbl = QLabel(titulo.upper())
    title_lbl.setStyleSheet(
        "color: #6366f1; font-size: 9px; font-weight: 700;"
        " letter-spacing: 1.2px; background: transparent;"
    )
    outer.addWidget(title_lbl)
    return box, outer


def configurar_combo_colorido(combo: QComboBox, mapa_cores: dict[str, str]) -> None:
    """Conecta currentTextChanged do combo para atualizar borda e cor do texto."""
    def _atualizar(texto: str):
        cor = mapa_cores.get(texto, "#e8e8f0")
        combo.setStyleSheet(
            "QComboBox { background-color: #1e1e2e; color: #e8e8f0;"
            f" border: 2px solid {cor}; border-radius: 8px;"
            " padding: 0px 12px; font-size: 13px; min-height: 36px; }"
            "QComboBox:hover { border-color: #3a3a50; }"
            f"QComboBox:focus {{ border-color: {cor}; }}"
            f"QComboBox:on {{ background-color: #1e1e2e; border-color: {cor}; }}"
            "QComboBox::drop-down { border: none; width: 30px; background: transparent; }"
            "QComboBox::down-arrow { image: none; border-left: 5px solid transparent;"
            " border-right: 5px solid transparent; border-top: 6px solid #717182;"
            " width: 0; height: 0; }"
            "QComboBox:hover::down-arrow { border-top-color: #6366f1; }"
            "QComboBox QAbstractItemView { background-color: #1e1e2e; color: #e8e8f0;"
            " border: 1px solid #2a2a3e; border-top: none;"
            " selection-background-color: rgba(99, 102, 241, 0.15);"
            " selection-color: #818cf8; outline: none; }"
        )
        le = combo.lineEdit()
        if le:
            le.setStyleSheet(f"background-color: #1e1e2e; color: {cor}; border: none; padding: 0; min-height: 28px;")
    combo.currentTextChanged.connect(_atualizar)
    _atualizar(combo.currentText())


def campo_rotulo(texto: str) -> QLabel:
    """Rótulo em negrito para exibição de campo em detalhes."""
    lbl = QLabel(texto)
    lbl.setStyleSheet(
        "color: #717182; font-size: 9px; font-weight: 700;"
        " letter-spacing: 0.8px; background: transparent;"
    )
    return lbl


def campo_readonly(texto: str) -> QLabel:
    """Valor readonly para exibição de campo em detalhes."""
    lbl = QLabel(texto)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        "color: #c8c8e0; font-size: 12px; font-weight: 500;"
        " background: transparent; padding: 0; margin: 0;"
    )
    return lbl
