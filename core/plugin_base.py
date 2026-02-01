"""Базовые классы для плагинов - БЕЗ зависимостей от UI"""

from abc import ABC, abstractmethod
from typing import Any


class BasePlugin(ABC):
    """Базовый класс для всех плагинов"""
    
    @abstractmethod
    def get_name(self) -> str:
        """Возвращает название плагина"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Возвращает описание плагина"""
        pass


class ModalityPlugin(BasePlugin):
    """Базовый класс для плагинов модальностей"""
    
    @abstractmethod
    def create_widget(self) -> Any:
        """
        Создает виджет для плагина.
        Возвращает QWidget (но тип Any, чтобы не импортировать PySide6 в core)
        """
        pass
