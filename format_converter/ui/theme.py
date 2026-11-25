"""Paper / Ink 两套主题：奶油底 + 黑描边 + 橙色强调（与 MCU-Forge 工作台一致）。"""

from __future__ import annotations

FONT_UI = "Microsoft YaHei UI"
FONT_MONO = "Cascadia Mono"

THEMES: dict[str, dict[str, str]] = {
    "light": {  # Paper
        "bg": "#f6f4ef", "panel": "#ffffff", "panel_alt": "#fbfaf7",
        "ink": "#1c1c1c", "muted": "#555555", "dim": "#888888",
        "line_soft": "#d9d5ca", "accent": "#d9541e", "accent_soft": "#fff3ec",
        "on_accent": "#ffffff", "ok": "#1f8a4c", "ok_soft": "#eaf6ee",
        "err": "#c0341d", "err_soft": "#fdecea",
    },
    "dark": {  # Ink
        "bg": "#161616", "panel": "#1f1f1f", "panel_alt": "#252525",
        "ink": "#ece9e1", "muted": "#b8b4aa", "dim": "#8a867d",
        "line_soft": "#3a3833", "accent": "#ff7a3d", "accent_soft": "#33231a",
        "on_accent": "#161616", "ok": "#4cc17f", "ok_soft": "#16261d",
        "err": "#ff6b55", "err_soft": "#2d1814",
    },
}


def get_tokens(name: str) -> dict[str, str]:
    return THEMES["dark" if name == "dark" else "light"]


def build_stylesheet(name: str) -> str:
    t = get_tokens(name)
    return f"""
    * {{ font-family: '{FONT_UI}'; }}
    QMainWindow, QDialog, QScrollArea, QScrollArea > QWidget > QWidget {{ background: {t['bg']}; }}
    QWidget {{ color: {t['ink']}; font-size: 13px; }}
    QLabel {{ background: transparent; }}

    QLabel#mark {{
        background: {t['ink']}; color: {t['bg']}; border-radius: 4px;
        font-family: '{FONT_MONO}'; font-weight: 800; font-size: 14px; letter-spacing: 1px;
    }}
    QLabel#brand {{ font-size: 24px; font-weight: 800; }}
    QLabel#subtitle {{ color: {t['muted']}; font-size: 14px; }}
    QLabel#version {{
        font-family: '{FONT_MONO}'; font-size: 11px; font-weight: 700; letter-spacing: 1px;
        color: {t['accent']}; background: {t['accent_soft']};
        border: 1px solid {t['accent']}; border-radius: 3px; padding: 1px 6px;
    }}
    QLabel#section {{
        font-family: '{FONT_MONO}'; font-size: 11px; font-weight: 700; letter-spacing: 2px; color: {t['dim']};
    }}

    QFrame#card {{
        background: {t['panel']}; border: 2px solid {t['ink']}; border-radius: 6px;
    }}
    QFrame#card:hover, QFrame#card:focus {{
        background: {t['accent_soft']}; border: 2px solid {t['accent']};
    }}
    QFrame#card[disabled_card="true"] {{ border-color: {t['line_soft']}; }}
    QFrame#card[drop="true"] {{ background: {t['accent_soft']}; border: 2px dashed {t['accent']}; }}
    QLabel#tag {{
        font-family: '{FONT_MONO}'; font-size: 12px; font-weight: 800; letter-spacing: 1px;
        color: {t['on_accent']}; background: {t['ink']}; border-radius: 3px; padding: 3px 8px;
    }}
    QLabel#card_title {{ font-size: 18px; font-weight: 800; }}
    QLabel#card_desc {{ color: {t['muted']}; font-size: 13px; }}
    QLabel#card_hint {{
        font-family: '{FONT_MONO}'; font-size: 11px; color: {t['accent']}; font-weight: 700;
    }}

    QPushButton {{
        background: {t['panel']}; color: {t['ink']}; border: 1.5px solid {t['ink']};
        border-radius: 4px; padding: 6px 14px; font-weight: 700;
    }}
    QPushButton:hover:!disabled {{ background: {t['ink']}; color: {t['bg']}; }}
    QPushButton:disabled {{ color: {t['dim']}; border-color: {t['line_soft']}; }}
    QPushButton:checked {{ background: {t['ink']}; color: {t['bg']}; }}
    QPushButton#primary {{ background: {t['accent']}; color: {t['on_accent']}; border-color: {t['ink']}; }}
    QPushButton#primary:hover:!disabled {{ background: {t['ink']}; color: {t['bg']}; }}

    QFrame#status_bar {{
        background: {t['panel']}; border: 2px solid {t['ink']}; border-radius: 6px;
    }}
    QLabel#pip {{ background: {t['dim']}; min-width: 9px; max-width: 9px; min-height: 9px; max-height: 9px; }}
    QLabel#pip[state="busy"] {{ background: {t['accent']}; }}
    QLabel#pip[state="ok"] {{ background: {t['ok']}; }}
    QLabel#pip[state="err"] {{ background: {t['err']}; }}
    QLabel#status_text {{ font-weight: 700; }}
    QProgressBar {{ background: {t['panel_alt']}; border: 1px solid {t['line_soft']}; border-radius: 0; max-height: 6px; }}
    QProgressBar::chunk {{ background: {t['accent']}; }}

    QPlainTextEdit#log {{
        background: {t['panel']}; border: 2px solid {t['ink']}; border-radius: 6px;
        font-family: '{FONT_MONO}', Consolas; font-size: 12px; padding: 6px; color: {t['muted']};
    }}

    QCheckBox {{ spacing: 8px; }}
    QCheckBox::indicator {{ width: 14px; height: 14px; border: 1.5px solid {t['ink']}; background: {t['panel']}; }}
    QCheckBox::indicator:checked {{ background: {t['accent']}; }}

    QMessageBox {{ background: {t['bg']}; }}
    QScrollBar:vertical {{ background: transparent; width: 8px; }}
    QScrollBar::handle:vertical {{ background: {t['line_soft']}; border-radius: 4px; min-height: 24px; }}
    QScrollBar::handle:vertical:hover {{ background: {t['dim']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    """
