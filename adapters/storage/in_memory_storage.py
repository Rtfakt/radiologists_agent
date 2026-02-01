"""In-memory реализация хранилища"""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from typing import List, Optional, Dict
from ports.storage_port import StorageAdapter
from domain.entities import Modality, Report, Template


class InMemoryStorage(StorageAdapter):
    """In-memory реализация хранилища данных"""
    
    def __init__(self):
        self._reports: Dict[str, Report] = {}
        self._templates: Dict[str, Template] = {}
        self._init_default_templates()
    
    def _init_default_templates(self):
        """Инициализация шаблонов по умолчанию"""
        # XRAY
        default_template = Template(
            name="Стандартный",
            modality=Modality.XRAY,
            replacements={
                "без патологических изменений": "без патологических изменений в легких",
                "легкие без особенностей": "легкие без патологических изменений",
                "сердце в норме": "сердце без патологических изменений",
                "без изменений": "без патологических изменений"
            }
        )
        self.save_template(default_template)
        
        formal_template = Template(
            name="Формализованный",
            modality=Modality.XRAY,
            replacements={
                "норма": "патологических изменений не выявлено",
                "все ок": "патологических изменений не обнаружено",
                "здоров": "признаков патологии не определяется"
            }
        )
        self.save_template(formal_template)

        # MAMMOGRAPHY
        mammo_standard = Template(
            name="Mammo: стандарт",
            modality=Modality.MAMMOGRAPHY,
            replacements={
                "без очаговых образований": "очаговых и инфильтративных изменений не выявлено",
                "микрокальцинаты не выявлены": "патологических микрокальцинатов не определяется",
            },
        )
        self.save_template(mammo_standard)

        # DENSITOMETRY
        densito_standard = Template(
            name="DXA: стандарт",
            modality=Modality.DENSITOMETRY,
            replacements={
                "остеопороз": "денситометрические признаки остеопороза",
                "остеопения": "денситометрические признаки остеопении",
            },
        )
        self.save_template(densito_standard)
    
    def save_report(self, report: Report) -> None:
        """Сохранить заключение"""
        self._reports[report.id] = report
    
    def get_report(self, report_id: str) -> Optional[Report]:
        """Получить заключение по ID"""
        return self._reports.get(report_id)
    
    def get_all_reports(self) -> List[Report]:
        """Получить все заключения"""
        return list(self._reports.values())
    
    def save_template(self, template: Template) -> None:
        """Сохранить шаблон"""
        # Ключ делаем составным: modality:name (чтобы имена могли повторяться между модальностями)
        key = f"{template.modality.value}:{template.name}"
        self._templates[key] = template
    
    def get_template(self, template_name: str) -> Optional[Template]:
        """Получить шаблон по имени"""
        # Для совместимости: сначала пробуем точное попадание по ключу, затем по "концу" (name)
        if template_name in self._templates:
            return self._templates.get(template_name)
        for t in self._templates.values():
            if t.name == template_name:
                return t
        return None
    
    def get_all_templates(self) -> List[Template]:
        """Получить все шаблоны"""
        return list(self._templates.values())

    def get_templates_by_modality(self, modality: Modality) -> List[Template]:
        """Получить шаблоны для конкретной модальности"""
        return [t for t in self._templates.values() if t.modality == modality]
