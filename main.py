"""Точка входа в десктопное приложение (Qt)."""

import sys

from PySide6.QtWidgets import QApplication

from core.plugin_loader import load_plugins
from ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    plugins = load_plugins()
    if not plugins:
        print("Не найдено ни одного плагина!")
        return

    window = MainWindow(plugins)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

