"""Доменные сущности"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class Modality(str, Enum):
    XRAY = "xray"
    MAMMOGRAPHY = "mammography"
    DENSITOMETRY = "densitometry"


@dataclass
class Report:
    """Сущность рентгеновского заключения"""
    id: str
    modality: Modality
    original_text: str
    processed_text: Optional[str] = None
    template_name: Optional[str] = None


@dataclass
class Template:
    """Шаблон для замены текста"""
    name: str
    modality: Modality
    replacements: Dict[str, str]  # Словарь замен: исходный текст -> целевой текст
