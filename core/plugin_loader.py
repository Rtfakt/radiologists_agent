from __future__ import annotations

"""Единая точка загрузки плагинов (UI‑агностичная)."""

import importlib.util
from pathlib import Path
from typing import List, Dict

from core.plugin_base import ModalityPlugin


def discover_plugin_paths() -> Dict[str, Path]:
    """
    Возвращает словарь {plugin_id: путь_к_plugin.py}.
    plugin_id соответствует имени поддиректории в `plugins/`.
    """
    root = Path(__file__).resolve().parent.parent
    plugins_dir = root / "plugins"

    result: Dict[str, Path] = {}
    if not plugins_dir.exists():
        return result

    subdirs = sorted(
        plugins_dir.iterdir(),
        key=lambda d: (0 if d.name == "xray_constructor" else 1, d.name),
    )

    for plugin_dir in subdirs:
        if (
            not plugin_dir.is_dir()
            or plugin_dir.name.startswith(".")
            or plugin_dir.name == "__pycache__"
        ):
            continue

        plugin_file = plugin_dir / "plugin.py"
        if not plugin_file.exists():
            continue

        result[plugin_dir.name] = plugin_file

    return result


def load_plugins() -> List[ModalityPlugin]:
    """Динамически загружает все плагины из папки `plugins/`."""
    plugins: List[ModalityPlugin] = []
    plugin_paths = discover_plugin_paths()

    for plugin_id, plugin_file in plugin_paths.items():
        try:
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_id}",
                plugin_file,
            )
            if spec is None or spec.loader is None:
                print(f"Не удалось загрузить спецификацию для {plugin_id}")
                continue

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[call-arg]

            if not hasattr(module, "Plugin"):
                print(f"Плагин {plugin_id} не содержит класс Plugin")
                continue

            plugin_instance = module.Plugin()

            if not isinstance(plugin_instance, ModalityPlugin):
                print(f"Плагин {plugin_id} не наследуется от ModalityPlugin")
                continue

            # Присваиваем идентификатор плагину для использования в веб‑части.
            setattr(plugin_instance, "plugin_id", plugin_id)

            plugins.append(plugin_instance)
            print(f"Загружен плагин: {plugin_instance.get_name()} ({plugin_id})")
        except Exception as e:  # pragma: no cover - защитный код
            print(f"Ошибка при загрузке плагина {plugin_id}: {e}")
            if plugin_id == "xray_constructor":
                import traceback

                traceback.print_exc()
            continue

    return plugins


__all__ = ["load_plugins", "discover_plugin_paths"]

