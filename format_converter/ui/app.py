"""桌面应用入口。"""

from __future__ import annotations

import sys


def run_gui() -> int:
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication

    from .main_window import MainWindow
    from .theme import FONT_UI

    app = QApplication.instance() or QApplication(sys.argv)
    app.setFont(QFont(FONT_UI, 9))
    window = MainWindow()
    window.show()
    return app.exec()
