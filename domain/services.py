"""Сервисы доменного слоя - бизнес-логика"""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from typing import Optional
from domain.entities import Modality, Report, Template


class ReportService:
    """Сервис для работы с рентгеновскими заключениями"""
    
    def __init__(self, template: Optional[Template] = None):
        self.template = template
    
    def set_template(self, template: Template):
        """Установить шаблон для замены"""
        self.template = template
    
    def process_report(self, report: Report) -> Report:
        """Обработать заключение по шаблону"""
        if not self.template:
            report.processed_text = report.original_text
            return report
        
        processed_text = report.original_text
        for original, replacement in self.template.replacements.items():
            processed_text = processed_text.replace(original, replacement)
        
        report.processed_text = processed_text
        report.template_name = self.template.name
        return report
    
    def create_report(self, report_id: str, modality: Modality, original_text: str) -> Report:
        """Создать новое заключение"""
        return Report(id=report_id, modality=modality, original_text=original_text)
