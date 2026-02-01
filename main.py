"""Точка входа в приложение"""

import sys
import importlib.util
from pathlib import Path
from typing import List

from PySide6.QtWidgets import QApplication
from core.plugin_base import ModalityPlugin
from ui.main_window import MainWindow


def load_plugins() -> List[ModalityPlugin]:
    """Динамически загружает все плагины из папки plugins/"""
    plugins = []
    plugins_dir = Path(__file__).parent / "plugins"
    
    if not plugins_dir.exists():
        print(f"Папка {plugins_dir} не найдена!")
        return plugins
    
    # Сканируем поддиректории в plugins/
    for plugin_dir in plugins_dir.iterdir():
        if not plugin_dir.is_dir():
            continue
        
        plugin_file = plugin_dir / "plugin.py"
        if not plugin_file.exists():
            continue
        
        try:
            # Динамический импорт плагина 
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_dir.name}", 
                plugin_file
            )
            if spec is None or spec.loader is None:
                print(f"Не удалось загрузить спецификацию для {plugin_dir.name}")
                continue
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Проверяем наличие класса Plugin
            if not hasattr(module, "Plugin"):
                print(f"Плагин {plugin_dir.name} не содержит класс Plugin")
                continue
            
            plugin_instance = module.Plugin()
            
            # Проверяем, что это ModalityPlugin
            if not isinstance(plugin_instance, ModalityPlugin):
                print(f"Плагин {plugin_dir.name} не наследуется от ModalityPlugin")
                continue
            
            plugins.append(plugin_instance)
            print(f"Загружен плагин: {plugin_instance.get_name()}")
            
        except Exception as e:
            print(f"Ошибка при загрузке плагина {plugin_dir.name}: {e}")
            continue
    
    return plugins


def main():
    """Главная функция"""
    app = QApplication(sys.argv)
    
    # Загружаем плагины
    plugins = load_plugins()
    
    if not plugins:
        print("Не найдено ни одного плагина!")
        return
    
    # Создаем и показываем главное окно
    window = MainWindow(plugins)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
