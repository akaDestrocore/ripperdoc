from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication
from qfluentwidgets import Theme, setTheme
from tools_gui.ui.main_window import MainWindow

def main() -> int:
    app = QApplication(sys.argv)
    setTheme(Theme.AUTO)
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())