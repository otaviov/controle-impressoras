"""
apply_theme.py
Roda na raiz do projeto: python apply_theme.py

O QUE FAZ:
1. Copia dark_premium.qss pra pasta themes/
2. Aplica a logo (1.png) na sidebar da main_window
3. Aplica a logo na tela de login
4. Atualiza o app.py pra carregar o novo tema por padrão
"""

import shutil
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent

def backup(path: Path):
    bk = path.with_suffix(path.suffix + f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(path, bk)
    print(f"  📦 Backup: {bk.name}")

def aplicar(path, descricao, old, new):
    content = path.read_text(encoding="utf-8")
    if old in content:
        path.write_text(content.replace(old, new), encoding="utf-8")
        print(f"  ✅ {descricao}")
        return True
    print(f"  ⚠️  Não encontrado: {descricao}")
    return False

# ─────────────────────────────────────────────────────────
# FIX 1 — Logo na sidebar (main_window.py)
# ─────────────────────────────────────────────────────────
def fix_sidebar_logo(path):
    old = (
        '        logo = QLabel("🖨️  CONTROLE DE\\n   IMPRESSORAS")\n'
        '        logo.setStyleSheet("color: #e94560; font-size: 14px; font-weight: bold; background: transparent; padding: 10px 5px;")\n'
        '        sidebar_layout.addWidget(logo)'
    )
    new = (
        '        # Logo Brasil Toner\n'
        '        import os\n'
        '        logo_frame = QFrame()\n'
        '        logo_frame.setStyleSheet("background: transparent; border: none;")\n'
        '        logo_frame_layout = QHBoxLayout(logo_frame)\n'
        '        logo_frame_layout.setContentsMargins(10, 10, 10, 14)\n'
        '        logo_frame_layout.setSpacing(10)\n'
        '        _logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "1.PNG")\n'
        '        if not os.path.exists(_logo_path):\n'
        '            _logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "1.png")\n'
        '        if os.path.exists(_logo_path):\n'
        '            from PySide6.QtGui import QPixmap\n'
        '            logo_img = QLabel()\n'
        '            pix = QPixmap(_logo_path).scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)\n'
        '            logo_img.setPixmap(pix)\n'
        '            logo_img.setStyleSheet("background: transparent; border: none;")\n'
        '            logo_frame_layout.addWidget(logo_img)\n'
        '        logo_text_widget = QLabel("CONTROLE DE\\nIMPRESSORA")\n'
        '        logo_text_widget.setStyleSheet(\n'
        '            "color: #e2e8f0; font-size: 11px; font-weight: 700;"\n'
        '            " background: transparent; letter-spacing: 0.3px; line-height: 1.4;"\n'
        '        )\n'
        '        logo_frame_layout.addWidget(logo_text_widget)\n'
        '        logo_frame_layout.addStretch()\n'
        '        sidebar_layout.addWidget(logo_frame)\n'
        '        sep_logo = QFrame()\n'
        '        sep_logo.setFrameShape(QFrame.HLine)\n'
        '        sep_logo.setStyleSheet("background-color: #1a1a2a; max-height: 1px;")\n'
        '        sidebar_layout.addWidget(sep_logo)'
    )
    return aplicar(path, "sidebar: logo 1.png + texto", old, new)


# ─────────────────────────────────────────────────────────
# FIX 2 — Botões do menu com objectName pra pegar estilo
# ─────────────────────────────────────────────────────────
def fix_menu_button_style(path):
    old = (
        '    def _criar_botao_menu(self, icone, texto):\n'
        '        btn = QPushButton(f"{icone}  {texto}")\n'
        '        btn.setCheckable(True)\n'
        '        btn.setCursor(Qt.PointingHandCursor)\n'
        '        btn.setMinimumHeight(40)\n'
        '        btn.setStyleSheet("QPushButton { background: transparent; color: #c0c0d0; border: none; text-align: left; font-size: 13px; padding: 10px 14px; border-radius: 8px; } QPushButton:hover { background-color: #1a1a3e; color: #ffffff; } QPushButton:checked { background-color: #e94560; color: white; font-weight: bold; }")\n'
        '        return btn'
    )
    new = (
        '    def _criar_botao_menu(self, icone, texto):\n'
        '        btn = QPushButton(f"{icone}  {texto}")\n'
        '        btn.setCheckable(True)\n'
        '        btn.setCursor(Qt.PointingHandCursor)\n'
        '        btn.setMinimumHeight(42)\n'
        '        btn.setObjectName("menuBtn")\n'
        '        btn.setStyleSheet(\n'
        '            "QPushButton#menuBtn { background: transparent; color: #4a4a6a; border: none;"\n'
        '            " text-align: left; font-size: 12pt; padding: 9px 14px; border-radius: 8px; font-weight: 500; }"\n'
        '            " QPushButton#menuBtn:hover { background-color: #141428; color: #8888aa; }"\n'
        '            " QPushButton#menuBtn:checked { background-color: #1e1040; color: #a78bfa; font-weight: 700; }"\n'
        '        )\n'
        '        return btn'
    )
    return aplicar(path, "menu buttons: novo estilo premium", old, new)


# ─────────────────────────────────────────────────────────
# FIX 3 — Separador da sidebar mais sutil
# ─────────────────────────────────────────────────────────
def fix_sidebar_sep(path):
    old = (
        '        sep = QFrame()\n'
        '        sep.setFrameShape(QFrame.HLine)\n'
        '        sep.setStyleSheet("background-color: #533483; max-height: 1px;")\n'
        '        sidebar_layout.addWidget(sep)\n'
        '        sidebar_layout.addSpacing(8)'
    )
    new = (
        '        sep = QFrame()\n'
        '        sep.setFrameShape(QFrame.HLine)\n'
        '        sep.setStyleSheet("background-color: #1a1a2a; max-height: 1px;")\n'
        '        sidebar_layout.addWidget(sep)\n'
        '        sidebar_layout.addSpacing(8)'
    )
    return aplicar(path, "sidebar separador: cor mais sutil", old, new)


# ─────────────────────────────────────────────────────────
# FIX 4 — user_info na sidebar
# ─────────────────────────────────────────────────────────
def fix_sidebar_user_info(path):
    old = (
        '        user_info = QLabel(f"👤 {self.user[\'nome\']}\\n🔒 {self.user[\'perfil\']}")\n'
        '        user_info.setStyleSheet("color: #a0a0b0; font-size: 11px; background: transparent; padding: 5px;")\n'
        '        sidebar_layout.addWidget(user_info)'
    )
    new = (
        '        # Card de usuário no rodapé da sidebar\n'
        '        user_frame = QFrame()\n'
        '        user_frame.setStyleSheet(\n'
        '            "QFrame { background-color: #141422; border: 1px solid #1e1e30;"\n'
        '            " border-radius: 8px; padding: 4px; }"\n'
        '        )\n'
        '        user_frame_layout = QHBoxLayout(user_frame)\n'
        '        user_frame_layout.setContentsMargins(8, 6, 8, 6)\n'
        '        user_frame_layout.setSpacing(8)\n'
        '        avatar = QLabel(self.user["nome"][:2].upper())\n'
        '        avatar.setFixedSize(28, 28)\n'
        '        avatar.setAlignment(Qt.AlignCenter)\n'
        '        avatar.setStyleSheet(\n'
        '            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #7c3aed,stop:1 #e94560);"\n'
        '            " color: white; border-radius: 14px; font-size: 10px; font-weight: 700;"\n'
        '        )\n'
        '        user_frame_layout.addWidget(avatar)\n'
        '        user_text = QLabel(f"{self.user[\'nome\']}\\n{self.user[\'perfil\'].capitalize()}")\n'
        '        user_text.setStyleSheet(\n'
        '            "color: #8888aa; font-size: 10px; background: transparent; border: none;"\n'
        '        )\n'
        '        user_frame_layout.addWidget(user_text)\n'
        '        user_frame_layout.addStretch()\n'
        '        sidebar_layout.addWidget(user_frame)'
    )
    return aplicar(path, "sidebar user card: avatar + nome + perfil", old, new)


# ─────────────────────────────────────────────────────────
# FIX 5 — Logo na tela de login (login_dialog.py)
# ─────────────────────────────────────────────────────────
def fix_login_logo(path):
    old = (
        '        # ÍCONE\n'
        '        icon = QLabel("🖨️")\n'
        '        icon.setAlignment(Qt.AlignCenter)\n'
        '        icon.setStyleSheet("font-size: 40px; background: transparent; border: none;")\n'
        '        card_layout.addWidget(icon)'
    )
    new = (
        '        # Logo Brasil Toner\n'
        '        import os\n'
        '        from PySide6.QtGui import QPixmap\n'
        '        _logo_path = Path(__file__).parent.parent.parent / "1.PNG"\n'
        '        if not _logo_path.exists():\n'
        '            _logo_path = Path(__file__).parent.parent.parent / "1.png"\n'
        '        if _logo_path.exists():\n'
        '            logo_lbl = QLabel()\n'
        '            pix = QPixmap(str(_logo_path)).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)\n'
        '            logo_lbl.setPixmap(pix)\n'
        '            logo_lbl.setAlignment(Qt.AlignCenter)\n'
        '            logo_lbl.setStyleSheet("background: transparent; border: none;")\n'
        '            card_layout.addWidget(logo_lbl)\n'
        '        else:\n'
        '            icon = QLabel("🖨️")\n'
        '            icon.setAlignment(Qt.AlignCenter)\n'
        '            icon.setStyleSheet("font-size: 40px; background: transparent; border: none;")\n'
        '            card_layout.addWidget(icon)'
    )
    return aplicar(path, "login: logo 1.png no lugar do emoji", old, new)


# ─────────────────────────────────────────────────────────
# FIX 6 — app.py: carrega dark_premium.qss por padrão
# ─────────────────────────────────────────────────────────
def fix_app_tema(path):
    old = (
        'def main():\n'
        '    app = QApplication(sys.argv)\n'
        '    app.setApplicationName("Controle de Impressoras Pro")'
    )
    new = (
        'def main():\n'
        '    app = QApplication(sys.argv)\n'
        '    app.setApplicationName("Controle de Impressoras Pro")\n'
        '\n'
        '    # Carrega tema premium\n'
        '    import os\n'
        '    _theme_path = os.path.join(os.path.dirname(__file__), "themes", "dark_premium.qss")\n'
        '    if os.path.exists(_theme_path):\n'
        '        with open(_theme_path, "r", encoding="utf-8") as _f:\n'
        '            app.setStyleSheet(_f.read())'
    )
    return aplicar(path, "app.py: carrega dark_premium.qss automaticamente", old, new)


# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  🎨 Aplicando novo tema premium...")
    print("=" * 55)

    main_window = BASE / "app" / "views" / "main_window.py"
    login_dialog = BASE / "app" / "views" / "login_dialog.py"
    app_py = BASE / "app.py"

    for p in [main_window, login_dialog, app_py]:
        if p.exists():
            backup(p)

    print("\n[1/6] Logo na sidebar")
    fix_sidebar_logo(main_window)

    print("\n[2/6] Estilo dos botões do menu")
    fix_menu_button_style(main_window)

    print("\n[3/6] Separador da sidebar")
    fix_sidebar_sep(main_window)

    print("\n[4/6] Card de usuário na sidebar")
    fix_sidebar_user_info(main_window)

    print("\n[5/6] Logo na tela de login")
    fix_login_logo(login_dialog)

    print("\n[6/6] app.py: tema automático")
    fix_app_tema(app_py)

    print("\n" + "=" * 55)
    print("  ✅ Pronto! Backups .bak_* gerados.")
    print()
    print("  📁 Certifique-se que o 1.PNG está na raiz do projeto")
    print("     (mesma pasta do app.py)")
    print()
    print("  ▶  python app.py")
    print("=" * 55)
