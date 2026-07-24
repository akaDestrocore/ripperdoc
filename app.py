#!/usr/bin/env python

"""
File: app.py

Brief:
    RIPPERDOC main application entry point.

Author:
    destrocore

Created: 2026-07-20
"""

from __future__ import annotations

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from qfluentwidgets import Theme, setTheme
from tools_gui.ui.main_window import MainWindow

def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative

def main() -> int:
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(resource_path("favicon.ico"))))
    setTheme(Theme.AUTO)
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())