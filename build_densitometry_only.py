#!/usr/bin/env python3
"""
Скрипт сборки дистрибутива «только плагин Денситометрия».
Создаёт папку dist_densitometry/ с приложением и одним плагином — для установки на любой компьютер.
"""

import shutil
import sys
from pathlib import Path

# Корень проекта
PROJECT_ROOT = Path(__file__).resolve().parent

# Что копировать в дистрибутив (относительно корня проекта)
DIRS_TO_COPY = [
    "core",
    "ui",
    "adapters",
    "domain",
    "ports",
]
FILES_TO_COPY = ["main.py"]
# Только плагин денситометрия
PLUGIN_NAME = "densitometry"
PLUGINS_INIT = "plugins/__init__.py"

# Куда собирать
OUT_DIR = PROJECT_ROOT / "dist_densitometry"


def copy_tree(src: Path, dst: Path, exclude_dirs: set = None) -> None:
    """Копирует дерево каталогов, исключая __pycache__ и exclude_dirs."""
    exclude_dirs = exclude_dirs or set()
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name == "__pycache__" or item.name in exclude_dirs:
            continue
        dest_item = dst / item.name
        if item.is_dir():
            copy_tree(item, dest_item, exclude_dirs)
        else:
            shutil.copy2(item, dest_item)


def main() -> None:
    out = OUT_DIR
    if out.exists():
        print(f"Удаляю старую сборку: {out}")
        shutil.rmtree(out)

    out.mkdir(parents=True)
    plugins_out = out / "plugins"
    plugins_out.mkdir(parents=True)

    # Копируем основные модули
    for d in DIRS_TO_COPY:
        src = PROJECT_ROOT / d
        if src.is_dir():
            copy_tree(src, out / d)
            print(f"  + {d}/")

    for f in FILES_TO_COPY:
        src = PROJECT_ROOT / f
        if src.is_file():
            shutil.copy2(src, out / f)
            print(f"  + {f}")

    # plugins/__init__.py
    init_src = PROJECT_ROOT / PLUGINS_INIT
    if init_src.is_file():
        shutil.copy2(init_src, plugins_out / "__init__.py")
        print(f"  + {PLUGINS_INIT}")

    # Только плагин densitometry
    plugin_src = PROJECT_ROOT / "plugins" / PLUGIN_NAME
    if not plugin_src.is_dir():
        print(f"Ошибка: плагин не найден: {plugin_src}")
        sys.exit(1)
    copy_tree(plugin_src, plugins_out / PLUGIN_NAME)
    print(f"  + plugins/{PLUGIN_NAME}/")

    # requirements только для запуска (без pytest)
    req_src = PROJECT_ROOT / "requirements.txt"
    req_out = out / "requirements.txt"
    with open(req_src, encoding="utf-8") as f:
        lines = [line for line in f if line.strip() and "pytest" not in line.lower()]
    req_out.write_text("".join(lines), encoding="utf-8")
    print(f"  + requirements.txt")

    # Краткая инструкция в папке
    readme = out / "КАК_УСТАНОВИТЬ.txt"
    readme.write_text(
        "Установка «Конструктор заключений — Денситометрия»\n"
        "================================================\n\n"
        "1. Установите Python 3.10 или 3.11 с python.org\n\n"
        "2. Откройте терминал (командную строку) в этой папке.\n\n"
        "3. Выполните:\n"
        "   python -m venv venv\n"
        "   venv\\Scripts\\activate     (Windows)\n"
        "   или: source venv/bin/activate  (macOS/Linux)\n\n"
        "   pip install -r requirements.txt\n"
        "   python main.py\n\n"
        "Готово. Запускайте приложение командой: python main.py\n",
        encoding="utf-8",
    )
    print(f"  + КАК_УСТАНОВИТЬ.txt")

    print(f"\nГотово. Дистрибутив: {out}")
    print("Архивируйте папку dist_densitometry в ZIP и переносите на любой компьютер.")


if __name__ == "__main__":
    main()
