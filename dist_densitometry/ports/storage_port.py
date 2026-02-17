"""Порт для хранения данных"""

from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities import Modality, Report, Template


class StorageAdapter(ABC):
    """Интерфейс для адаптера хранения данных"""
    
    @abstractmethod
    def save_report(self, report: Report) -> None:
        """Сохранить заключение"""
        pass
    
    @abstractmethod
    def get_report(self, report_id: str) -> Optional[Report]:
        """Получить заключение по ID"""
        pass
    
    @abstractmethod
    def get_all_reports(self) -> List[Report]:
        """Получить все заключения"""
        pass
    
    @abstractmethod
    def save_template(self, template: Template) -> None:
        """Сохранить шаблон"""
        pass
    
    @abstractmethod
    def get_template(self, template_name: str) -> Optional[Template]:
        """Получить шаблон по имени"""
        pass
    
    @abstractmethod
    def get_all_templates(self) -> List[Template]:
        """Получить все шаблоны"""
        pass

    @abstractmethod
    def get_templates_by_modality(self, modality: Modality) -> List[Template]:
        """Получить шаблоны для конкретной модальности"""
        pass
