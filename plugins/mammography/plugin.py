"""Плагин маммографии"""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QButtonGroup, QGroupBox, QTextEdit
)
from PySide6.QtCore import Qt
import re
from core.plugin_base import ModalityPlugin


class MammographyPlugin(ModalityPlugin):
    """Плагин для работы с маммографией"""
    
    def __init__(self):
        self.density = "B"  
        self.conclusion = "норма"  
        
        # Тексты плотности для замены
        self.density_texts = {
            "A": "Тип плотности ACR-A( железистого компонента менее 25%), Структура представлена преимущественно элементами рассеянных участков фиброза и жировой ткани(жировая инволюция)",
            "B": "Тип плотности ACR-В( железистого компонента от 25% до 50% ), соответствует возрасту.  Структура представлена преимущественно фиброзно-жировой и отдельными включениями железистой ткани.",
            "C": "Тип плотности ACR-C( железистого компонента от 50% до 75%), соответствует возрасту. Структура представлена гетерогенно плотной тканью.",
            "D": "Тип плотности ACR-D( железистого компонента, больше 75%), соответствует возрасту. Структура представлена преимущественно элементами железистой ткани, в меньшей степени фиброзной и жировой."
        }
        
        # Тексты заключения для замены
        self.conclusion_texts = {
            "Норма": "ОЧАГОВОЙ ПАТОЛОГИИ МОЛОЧНЫХ ЖЕЛЕЗ НЕ ВЫЯВЛЕНО.",
            "ФЖИ": "ФИБРОЗНО-ЖИРОВАЯ ИНВОЛЮЦИЯ МОЛОЧНЫХ ЖЕЛЕЗ.",
            "ФКМ": "ФИБРОЗНО-КИСТОЗНАЯ МАСТОПАТИЯ."
        }
        
        # Инициализируем базовый текст
        self.base_text = """ПРАВАЯ МОЛОЧНАЯ ЖЕЛЕЗА В ДВУХ ПРОЕКЦИЯХ: Тип плотности ACR-В( железистого компонента от 25% до 50% ), соответствует возрасту.  Структура представлена преимущественно фиброзно-живой и отдельными включениями железистой ткани. Кожные покровы, сосок, ареола без особенностей.Кальцинаты доброкачественные - нет, злокачественные - нет. Участков ассиметрии - нет. Узловые образования не определяются. Нарушение архитектоники - нет. Лимфатические узлы не увеличены. Обызвествления сосудов нет. 

ЛЕВАЯ МОЛОЧНАЯ ЖЕЛЕЗА  В ДВУХ ПРОЕКЦИЯХ: Тип плотности ACR-В( железистого компонента от 25% до 50% ), соответствует возрасту.  Структура представлена преимущественно фиброзно-жировой и отдельными включениями железистой ткани. Кожные покровы, сосок, ареола без особенностей. Кальцинаты доброкачественные - нет, злокачественные - нет. Участков ассиметрии - нет. Узловые образования не определяются. Нарушение архитектоники - нет. Лимфатические узлы не увеличены. Обызвествления сосудов нет. 

ЗАКЛЮЧЕНИЕ: ОЧАГОВОЙ ПАТОЛОГИИ МОЛОЧНЫХ ЖЕЛЕЗ НЕ ВЫЯВЛЕНО. 
BIRADS 1 СПРАВА И СЛЕВА 

Динамический контроль через 1 год"""
    
    def get_name(self) -> str:
        return "Маммография"
    
    def get_description(self) -> str:
        return "Плагин для работы с маммографическими исследованиями"
    
    def create_widget(self) -> QWidget:
        """Создает виджет с кнопками для плотности и заключения"""
        widget = QWidget()
        main_layout = QHBoxLayout(widget)
        main_layout.setSpacing(10)
        
        # Левая колонка: текстовое поле и кнопка
        left_column = QVBoxLayout()
        
        text_group = QGroupBox("Текст заключения (редактируемый)")
        text_layout = QVBoxLayout()
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.base_text)
        self.text_edit.setMinimumHeight(400)
        text_layout.addWidget(self.text_edit)
        
        text_group.setLayout(text_layout)
        left_column.addWidget(text_group)
        
        # Кнопка "Сформировать отчет"
        generate_report_btn = QPushButton("Сформировать отчет")
        generate_report_btn.setMinimumHeight(40)
        generate_report_btn.clicked.connect(self._generate_description)
        left_column.addWidget(generate_report_btn)
        
        left_column.addStretch()
        
        # Правая колонка: поля ввода и кнопки
        right_column = QVBoxLayout()
        
        # Группа для выбора плотности
        density_group = QGroupBox("Плотность молочной железы (ACR)")
        density_layout = QHBoxLayout()
        
        self.density_buttons = QButtonGroup()
        density_btn_a = QPushButton("A")
        density_btn_b = QPushButton("B")
        density_btn_c = QPushButton("C")
        density_btn_d = QPushButton("D")
        
        # Делаем кнопки переключаемыми
        for btn in [density_btn_a, density_btn_b, density_btn_c, density_btn_d]:
            btn.setCheckable(True)
            btn.setMinimumHeight(40)
            density_layout.addWidget(btn)
            self.density_buttons.addButton(btn)
        
        # По умолчанию выбрана B
        density_btn_b.setChecked(True)
        self.density_buttons.buttonClicked.connect(self._on_density_changed)
        
        density_group.setLayout(density_layout)
        right_column.addWidget(density_group)
        
        # Группа для выбора заключения
        conclusion_group = QGroupBox("Заключение")
        conclusion_layout = QVBoxLayout()
        
        self.conclusion_buttons = QButtonGroup()
        conclusion_btn_normal = QPushButton("Норма")
        conclusion_btn_fzhi = QPushButton("ФЖИ")
        conclusion_btn_fkm = QPushButton("ФКМ")
        
        for btn in [conclusion_btn_normal, conclusion_btn_fzhi, conclusion_btn_fkm]:
            btn.setCheckable(True)
            btn.setMinimumHeight(35)
            conclusion_layout.addWidget(btn)
            self.conclusion_buttons.addButton(btn)
        
        # По умолчанию выбрана норма
        conclusion_btn_normal.setChecked(True)
        self.conclusion_buttons.buttonClicked.connect(self._on_conclusion_changed)
        
        conclusion_group.setLayout(conclusion_layout)
        right_column.addWidget(conclusion_group)
        
        right_column.addStretch()
        
        # Добавляем колонки в основной layout
        main_layout.addLayout(left_column, 2)  # Левая колонка занимает 2 части
        main_layout.addLayout(right_column, 1)  # Правая колонка занимает 1 часть
        
        return widget
    
    def _on_density_changed(self, button: QPushButton):
        """Обработчик изменения плотности"""
        self.density = button.text()
    
    def _on_conclusion_changed(self, button: QPushButton):
        """Обработчик изменения заключения"""
        self.conclusion = button.text()
    
    def _generate_description(self):
        """Формирует описание, применяя выбранную плотность и заключение"""
        # Получаем текущий текст из редактора
        current_text = self.text_edit.toPlainText()
        
        # Получаем тексты для замены
        new_density_text = self.density_texts.get(self.density, "")
        new_conclusion_text = self.conclusion_texts.get(self.conclusion, "")
        
        # Проверяем, что значения найдены
        if not new_density_text:
            print(f"Предупреждение: плотность '{self.density}' не найдена в словаре")
        if not new_conclusion_text:
            print(f"Предупреждение: заключение '{self.conclusion}' не найдено в словаре")
        
        # Если текущий текст пустой, используем базовый
        if not current_text.strip():
            current_text = self.base_text
        
        # Заменяем плотность в тексте (для обеих молочных желез)
        # Ищем паттерны плотности в тексте
        density_patterns = [
            r"Тип плотности ACR-[ABCD]\([^)]+\)[^.]*\.",  # Паттерн для текста плотности
        ]
        
        for pattern in density_patterns:
            matches = re.findall(pattern, current_text)
            if matches:
                # Заменяем все найденные вхождения
                for match in matches:
                    current_text = current_text.replace(match, new_density_text)
                break
        
        # Если паттерн не найден, добавляем текст плотности вручную
        if not any(pattern in current_text for pattern in density_patterns):
            # Это более простая замена для случая, когда структура текста отличается
            current_text = re.sub(
                r"(ПРАВАЯ МОЛОЧНАЯ ЖЕЛЕЗА[^:]+:).*?(Кожные покровы)",
                r"\1 " + new_density_text + " \2",
                current_text
            )
            current_text = re.sub(
                r"(ЛЕВАЯ МОЛОЧНАЯ ЖЕЛЕЗА[^:]+:).*?(Кожные покровы)",
                r"\1 " + new_density_text + " \2",
                current_text
            )
        
        # Заменяем заключение в тексте
        # Ищем заключение после "ЗАКЛЮЧЕНИЕ:"
        conclusion_match = re.search(r"ЗАКЛЮЧЕНИЕ:.*?(?=BIRADS|\n\n|$)", current_text, re.DOTALL)
        if conclusion_match:
            old_conclusion = conclusion_match.group(0)
            new_conclusion_line = f"ЗАКЛЮЧЕНИЕ: {new_conclusion_text}"
            current_text = current_text.replace(old_conclusion, new_conclusion_line)
        else:
            # Если не нашли стандартный формат, заменяем или добавляем вручную
            if "ЗАКЛЮЧЕНИЕ:" in current_text:
                current_text = re.sub(
                    r"ЗАКЛЮЧЕНИЕ:.*",
                    f"ЗАКЛЮЧЕНИЕ: {new_conclusion_text}",
                    current_text
                )
            else:
                # Добавляем заключение в конец
                current_text += f"\n\nЗАКЛЮЧЕНИЕ: {new_conclusion_text}"
        
        # Обновляем текст в редакторе
        self.text_edit.setPlainText(current_text)
    

    
    def get_generated_text(self) -> str:
        """Возвращает сформированный текст из редактора"""
        return self.text_edit.toPlainText() if hasattr(self, 'text_edit') else ""


# Обязательный класс Plugin для динамической загрузки
Plugin = MammographyPlugin