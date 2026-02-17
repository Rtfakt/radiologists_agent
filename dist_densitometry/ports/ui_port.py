"""Порт для пользовательского интерфейса"""

from abc import ABC, abstractmethod
from typing import Callable, Optional
from domain.entities import Modality, Report, Template


class UIAdapter(ABC):
    """Интерфейс для UI адаптера"""
    
    @abstractmethod
    def show_report(self, report: Report):
        """Показать заключение"""
        pass
    
    @abstractmethod
    def get_original_text(self) -> str:
        """Получить исходный текст от пользователя"""
        pass
    
    @abstractmethod
    def set_process_callback(self, callback: Callable[[], None]):
        """Установить callback для обработки текста"""
        pass
    
    @abstractmethod
    def set_template_callback(self, callback: Callable[[str], None]):
        """Установить callback для выбора шаблона"""
        pass

    @abstractmethod
    def set_modality_callback(self, callback: Callable[[Modality], None]):
        """Установить callback для выбора модальности"""
        pass
    
    @abstractmethod
    def run(self):
        """Запустить UI"""
        pass
