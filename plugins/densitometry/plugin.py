"""Плагин денситометрии с улучшенной обработкой текста"""

import sys
import re
from pathlib import Path
from typing import Optional

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QApplication,
    QPushButton, QGroupBox, QFormLayout, QTextEdit
)
from PySide6.QtCore import Qt
from core.plugin_base import ModalityPlugin
from plugins.densitometry.validators import (
    TZCriteriaLineEdit,
    DensityLineEdit,
    FRAXLineEdit,
)


class DensitometryPlugin(ModalityPlugin):
    """Плагин для работы с денситометрией"""
    
    def __init__(self):
        pass
        
    def get_name(self) -> str:
        return "Денситометрия"
    
    def get_description(self) -> str:
        return "Плагин для работы с денситометрическими исследованиями"
    
    def create_widget(self, on_report_generated=None) -> QWidget:
        """Создает виджет с полями для T/Z-критериев и костной массы"""
        self._on_report_generated = on_report_generated
        widget = QWidget()
        main_layout = QHBoxLayout(widget)
        main_layout.setSpacing(10)
        
        # Левая колонка: два текстовых поля и кнопки
        left_column = QVBoxLayout()
        
        # Текстовое поле для позвоночника
        spine_text_group = QGroupBox("Текст заключения - Позвоночник")
        spine_text_layout = QVBoxLayout()
        
        self.spine_text_edit = QTextEdit()
        self.spine_text_edit.setPlainText("")
        self.spine_text_edit.setMinimumHeight(200)
        spine_text_layout.addWidget(self.spine_text_edit)
        
        spine_text_group.setLayout(spine_text_layout)
        left_column.addWidget(spine_text_group)
        
        # Кнопки копирования для позвоночника
        spine_copy_btns = QHBoxLayout()
        self.spine_copy_desc_btn = QPushButton("Копировать описание позвоночника")
        self.spine_copy_desc_btn.setMinimumHeight(36)
        self.spine_copy_desc_btn.clicked.connect(self._copy_spine_description)
        self.spine_copy_conc_btn = QPushButton("Копировать заключение позвоночника")
        self.spine_copy_conc_btn.setMinimumHeight(36)
        self.spine_copy_conc_btn.clicked.connect(self._copy_spine_conclusion)
        spine_copy_btns.addWidget(self.spine_copy_desc_btn)
        spine_copy_btns.addWidget(self.spine_copy_conc_btn)
        left_column.addLayout(spine_copy_btns)
        
        # Текстовое поле для бедренной кости
        femur_text_group = QGroupBox("Текст заключения - Бедренная кость")
        femur_text_layout = QVBoxLayout()
        
        self.femur_text_edit = QTextEdit()
        self.femur_text_edit.setPlainText("")
        self.femur_text_edit.setMinimumHeight(200)
        femur_text_layout.addWidget(self.femur_text_edit)
        
        femur_text_group.setLayout(femur_text_layout)
        left_column.addWidget(femur_text_group)
        
        # Кнопки копирования для бедра
        femur_copy_btns = QHBoxLayout()
        self.femur_copy_desc_btn = QPushButton("Копировать описание бедра")
        self.femur_copy_desc_btn.setMinimumHeight(36)
        self.femur_copy_desc_btn.clicked.connect(self._copy_femur_description)
        self.femur_copy_conc_btn = QPushButton("Копировать заключение бедра")
        self.femur_copy_conc_btn.setMinimumHeight(36)
        self.femur_copy_conc_btn.clicked.connect(self._copy_femur_conclusion)
        femur_copy_btns.addWidget(self.femur_copy_desc_btn)
        femur_copy_btns.addWidget(self.femur_copy_conc_btn)
        left_column.addLayout(femur_copy_btns)
        
        # Кнопка для формирования всего отчета целиком
        self.generate_all_btn = QPushButton("Сформировать целиком")
        self.generate_all_btn.setMinimumHeight(35)
        self.generate_all_btn.clicked.connect(self._generate_all_text)
        left_column.addWidget(self.generate_all_btn)
        
        left_column.addStretch()
        
        # Правая колонка: поля ввода и кнопки
        right_column = QVBoxLayout()
        
        # Группа для позвоночника
        spine_group = QGroupBox("Позвоночник (L1-L4)")
        spine_layout = QFormLayout()
        
        self.spine_t_score = TZCriteriaLineEdit()
        self.spine_z_score = TZCriteriaLineEdit()
        self.spine_bmd = DensityLineEdit()
        
        spine_layout.addRow("T-критерий:", self.spine_t_score)
        spine_layout.addRow("Z-критерий:", self.spine_z_score)
        spine_layout.addRow("Костная масса (г/см²):", self.spine_bmd)
        
        spine_group.setLayout(spine_layout)
        right_column.addWidget(spine_group)
        
        # Кнопка для формирования текста позвоночника
        self.spine_generate_btn = QPushButton("Сформировать")
        self.spine_generate_btn.setMinimumHeight(35)
        self.spine_generate_btn.clicked.connect(self._generate_spine_text)
        right_column.addWidget(self.spine_generate_btn)
        
        # Группа для шейки бедренной кости
        femur_group = QGroupBox("Шейка бедренной кости (femoral neck)")
        femur_layout = QFormLayout()
        
        self.femur_t_score = TZCriteriaLineEdit()
        self.femur_z_score = TZCriteriaLineEdit()
        self.femur_bmd = DensityLineEdit()
        self.femur_frax = FRAXLineEdit()
        
        femur_layout.addRow("T-критерий:", self.femur_t_score)
        femur_layout.addRow("Z-критерий:", self.femur_z_score)
        femur_layout.addRow("Костная масса (г/см²):", self.femur_bmd)
        femur_layout.addRow("FRAX (%):", self.femur_frax)
        
        femur_group.setLayout(femur_layout)
        right_column.addWidget(femur_group)
        
        # Группа для проксимального отдела бедра в целом (total hip)
        total_hip_group = QGroupBox("Проксимальный отдел бедра в целом (total hip)")
        total_hip_layout = QFormLayout()
        
        self.total_hip_t_score = TZCriteriaLineEdit()
        self.total_hip_z_score = TZCriteriaLineEdit()
        self.total_hip_bmd = DensityLineEdit()
        
        total_hip_layout.addRow("T-критерий:", self.total_hip_t_score)
        total_hip_layout.addRow("Z-критерий:", self.total_hip_z_score)
        total_hip_layout.addRow("Костная масса (г/см²):", self.total_hip_bmd)
        
        total_hip_group.setLayout(total_hip_layout)
        right_column.addWidget(total_hip_group)
        
        # Кнопка для формирования текста бедренной кости
        self.femur_generate_btn = QPushButton("Сформировать")
        self.femur_generate_btn.setMinimumHeight(35)
        self.femur_generate_btn.clicked.connect(self._generate_femur_text)
        right_column.addWidget(self.femur_generate_btn)
        
        right_column.addStretch()
        
        # Добавляем колонки в основной layout
        main_layout.addLayout(left_column, 2)  # Левая колонка занимает 2 части
        main_layout.addLayout(right_column, 1)  # Правая колонка занимает 1 часть
        
        return widget
    
    def _get_criterion_display_and_value(self, t_val: Optional[float], z_val: Optional[float]) -> tuple[Optional[str], Optional[float]]:
        """
        Определяет, какой критерий использовать для отображения и диагноза.
        Возвращает (строка для отображения, значение для диагноза).
        Если оба критерия не равны 0, возвращает (None, None) — нужно показать ошибку.
        Точное равенство 0.0 считается заполненным значением.
        """
        if t_val is None and z_val is None:
            return (None, None)
        if t_val is not None and z_val is not None:
            return (None, None)
        if t_val is not None:
            return (f"Т-критерий – {t_val:.1f}", t_val)
        if z_val is not None:
            return (f"Z-критерий – {z_val:.1f}", z_val)
        return (None, None)

    def _get_criterion_type(self, t_val: Optional[float], z_val: Optional[float]) -> Optional[str]:
        """Возвращает тип критерия (T или Z) по введённым значениям или None."""
        if t_val is not None and z_val is not None:
            return None
        if t_val is not None:
            return "T"
        if z_val is not None:
            return "Z"
        return None

    def _get_diagnosis(self, score: float, criterion_type: str = "T") -> str:
        """Определяет диагноз по значению критерия (T или Z)."""
        if criterion_type == "Z":
            return "Остеопороз" if score <= -2.0 else "Норма"
        if score <= -2.5:
            return "Остеопороз"
        elif -2.5 < score <= -2.0:
            return "Остеопения 3 ст."
        elif -2.0 < score <= -1.5:
            return "Остеопения 2 ст"
        elif -1.5 < score <= -1.1:
            return "Остеопения 1 ст"
        else:  # score > -1.1
            return "Норма"
    
    def _validate_spine(self) -> Optional[str]:
        """Валидация полей позвоночника"""
        spine_bmd = self.spine_bmd.value()
        spine_t = self.spine_t_score.value()
        spine_z = self.spine_z_score.value()
        
        if spine_bmd is None or (spine_t is None and spine_z is None):
            return "Для позвоночника заполните костную массу и хотя бы один критерий (T или Z)"
        if spine_t is not None and spine_z is not None:
            return "Введите либо T, либо Z критерий (не оба сразу)"
        return None
    
    def _validate_femur(self) -> Optional[str]:
        """Валидация полей бедренной кости"""
        # Проверка шейки бедренной кости
        femur_bmd = self.femur_bmd.value()
        femur_t = self.femur_t_score.value()
        femur_z = self.femur_z_score.value()
        femur_frax = self.femur_frax.value()
        
        if femur_bmd is None or (femur_t is None and femur_z is None) or femur_frax is None:
            return "Для шейки бедренной кости заполните костную массу, хотя бы один критерий (T или Z) и FRAX"
        if femur_t is not None and femur_z is not None:
            return "Для шейки бедренной кости введите либо T, либо Z критерий (не оба сразу)"
        
        # Проверка total hip
        total_hip_bmd = self.total_hip_bmd.value()
        total_hip_t = self.total_hip_t_score.value()
        total_hip_z = self.total_hip_z_score.value()
        
        if total_hip_bmd is None or (total_hip_t is None and total_hip_z is None):
            return "Для проксимального отдела бедра (total hip) заполните костную массу и хотя бы один критерий (T или Z)"
        if total_hip_t is not None and total_hip_z is not None:
            return "Для проксимального отдела бедра (total hip) введите либо T, либо Z критерий (не оба сразу)"
        
        femur_type = self._get_criterion_type(femur_t, femur_z)
        total_hip_type = self._get_criterion_type(total_hip_t, total_hip_z)
        if femur_type and total_hip_type and femur_type != total_hip_type:
            return "Для бедренной кости используйте один тип критерия (либо T для обоих участков, либо Z)"
        
        return None
    
    def _show_error_tooltip(self, button: QPushButton, error_message: str):
        """Показывает ошибку в tooltip кнопки"""
        button.setToolTip(error_message)
        # Показываем tooltip программно
        from PySide6.QtCore import QPoint
        from PySide6.QtWidgets import QToolTip
        QToolTip.showText(button.mapToGlobal(QPoint(0, button.height())), error_message, button)
    
    def _clear_error_tooltip(self, button: QPushButton):
        """Очищает tooltip кнопки"""
        button.setToolTip("")
    
    def _clear_spine_input_fields(self):
        """Очищает поля ввода позвоночника (T, Z, костная масса)."""
        self.spine_t_score.setText("")
        self.spine_z_score.setText("")
        self.spine_bmd.setText("")
    
    def _clear_femur_input_fields(self):
        """Очищает поля ввода тазобедренного сустава (шейка + total hip + FRAX)."""
        self.femur_t_score.setText("")
        self.femur_z_score.setText("")
        self.femur_bmd.setText("")
        self.femur_frax.setText("")
        self.total_hip_t_score.setText("")
        self.total_hip_z_score.setText("")
        self.total_hip_bmd.setText("")
    
    def _clear_all_input_fields(self):
        """Очищает все поля ввода (позвоночник и тазобедренный сустав)."""
        self._clear_spine_input_fields()
        self._clear_femur_input_fields()
    
    def _split_description_conclusion(self, text: str) -> tuple[str, str]:
        """Разбивает текст блока на описание и заключение по маркеру «Заключение.» / «Заключение:»."""
        if not text or not text.strip():
            return "", ""
        match = re.search(r"\n\n\s*Заключение[.:]", text, re.IGNORECASE)
        if match:
            return text[: match.start()].strip(), text[match.start() :].strip()
        return text.strip(), ""
    
    def _get_combined_description(self) -> str:
        """Возвращает объединённое описание из обоих редакторов (без заключений)."""
        parts = []
        spine_text = self.spine_text_edit.toPlainText().strip()
        if spine_text:
            desc, _ = self._split_description_conclusion(spine_text)
            if desc:
                parts.append(desc)
        femur_text = self.femur_text_edit.toPlainText().strip()
        if femur_text:
            desc, _ = self._split_description_conclusion(femur_text)
            if desc:
                parts.append(desc)
        return "\n\n".join(parts)
    
    def _get_combined_conclusion(self) -> str:
        """Возвращает объединённое заключение из обоих редакторов."""
        parts = []
        spine_text = self.spine_text_edit.toPlainText().strip()
        if spine_text:
            _, conc = self._split_description_conclusion(spine_text)
            if conc:
                parts.append(conc)
        femur_text = self.femur_text_edit.toPlainText().strip()
        if femur_text:
            _, conc = self._split_description_conclusion(femur_text)
            if conc:
                parts.append(conc)
        return "\n\n".join(parts)
    
    def _copy_spine_description(self):
        """Копирует в буфер только описание позвоночника."""
        text = self.spine_text_edit.toPlainText().strip()
        if not text:
            self._show_error_tooltip(self.spine_copy_desc_btn, "Текстовое поле позвоночника пустое")
            return
        self._clear_error_tooltip(self.spine_copy_desc_btn)
        description, _ = self._split_description_conclusion(text)
        QApplication.clipboard().setText(description)

    def _copy_spine_conclusion(self):
        """Копирует в буфер только заключение позвоночника."""
        text = self.spine_text_edit.toPlainText().strip()
        if not text:
            self._show_error_tooltip(self.spine_copy_conc_btn, "Текстовое поле позвоночника пустое")
            return
        self._clear_error_tooltip(self.spine_copy_conc_btn)
        _, conclusion = self._split_description_conclusion(text)
        QApplication.clipboard().setText(conclusion)

    def _copy_femur_description(self):
        """Копирует в буфер только описание бедренной кости."""
        text = self.femur_text_edit.toPlainText().strip()
        if not text:
            self._show_error_tooltip(self.femur_copy_desc_btn, "Текстовое поле бедра пустое")
            return
        self._clear_error_tooltip(self.femur_copy_desc_btn)
        description, _ = self._split_description_conclusion(text)
        QApplication.clipboard().setText(description)

    def _copy_femur_conclusion(self):
        """Копирует в буфер только заключение бедренной кости."""
        text = self.femur_text_edit.toPlainText().strip()
        if not text:
            self._show_error_tooltip(self.femur_copy_conc_btn, "Текстовое поле бедра пустое")
            return
        self._clear_error_tooltip(self.femur_copy_conc_btn)
        _, conclusion = self._split_description_conclusion(text)
        QApplication.clipboard().setText(conclusion)

    def _copy_description(self):
        """Копирует в буфер только описание."""
        QApplication.clipboard().setText(self._get_combined_description())
    
    def _copy_conclusion(self):
        """Копирует в буфер только заключение."""
        QApplication.clipboard().setText(self._get_combined_conclusion())

    def get_description_text(self) -> str:
        """Текст описания для горячих клавиш."""
        return self._get_combined_description()

    def get_conclusion_text(self) -> str:
        """Текст заключения для горячих клавиш."""
        return self._get_combined_conclusion()
    
    def _generate_spine_text(self):
        """Формирует текст для позвоночника с валидацией и копированием в буфер"""
        # Валидация
        error = self._validate_spine()
        if error:
            self._show_error_tooltip(self.spine_generate_btn, error)
            return
        
        # Очищаем tooltip при успешной валидации
        self._clear_error_tooltip(self.spine_generate_btn)
        
        spine_t = self.spine_t_score.value()
        spine_z = self.spine_z_score.value()
        spine_bmd = self.spine_bmd.value()
        criterion_str, value_for_diagnosis = self._get_criterion_display_and_value(spine_t, spine_z)
        if criterion_str is None:
            self._show_error_tooltip(self.spine_generate_btn, "Введите либо T, либо Z критерий (не оба сразу)")
            return
        spine_criterion_type = "T" if spine_t is not None else "Z"
        spine_diagnosis = self._get_diagnosis(value_for_diagnosis, spine_criterion_type)
        
        bmd_text = f"{spine_bmd:.3f}" if spine_bmd is not None else None
        if bmd_text is not None:
            description = f"""Поясничный отдел позвоночника. Поясничные позвонки: L1–L4. Среднее значение МПК составило {bmd_text} г/см². {criterion_str}"""
        else:
            description = f"""Поясничный отдел позвоночника. Поясничные позвонки: L1–L4. {criterion_str}"""
        conclusion = f"""Заключение. Позвоночник - {spine_diagnosis}"""
        full_text = f"{description}\n\n{conclusion}"
        
        self.spine_text_edit.setPlainText(full_text)
        self._clear_spine_input_fields()
        if self.femur_text_edit.toPlainText().strip():
            self.femur_text_edit.clear()
        QApplication.clipboard().setText(description)
        if getattr(self, "_on_report_generated", None):
            self._on_report_generated(description, conclusion)
    
    def _generate_femur_text(self):
        """Формирует текст для бедренной кости с валидацией и копированием в буфер"""
        error = self._validate_femur()
        if error:
            self._show_error_tooltip(self.femur_generate_btn, error)
            return
        
        self._clear_error_tooltip(self.femur_generate_btn)
        
        femur_t = self.femur_t_score.value()
        femur_z = self.femur_z_score.value()
        femur_bmd = self.femur_bmd.value()
        femur_frax = self.femur_frax.value()
        femur_criterion_str, femur_value = self._get_criterion_display_and_value(femur_t, femur_z)
        if femur_criterion_str is None:
            self._show_error_tooltip(self.femur_generate_btn, "Для шейки бедренной кости введите либо T, либо Z критерий (не оба сразу)")
            return
        femur_criterion_type = self._get_criterion_type(femur_t, femur_z)
        femur_diagnosis = self._get_diagnosis(femur_value, femur_criterion_type)
        
        total_hip_t = self.total_hip_t_score.value()
        total_hip_z = self.total_hip_z_score.value()
        total_hip_bmd = self.total_hip_bmd.value()
        total_hip_criterion_str, total_hip_value = self._get_criterion_display_and_value(total_hip_t, total_hip_z)
        if total_hip_criterion_str is None:
            self._show_error_tooltip(self.femur_generate_btn, "Для проксимального отдела бедра (total hip) введите либо T, либо Z критерий (не оба сразу)")
            return
        total_hip_criterion_type = self._get_criterion_type(total_hip_t, total_hip_z)
        total_hip_diagnosis = self._get_diagnosis(total_hip_value, total_hip_criterion_type)
        
        femur_bmd_text = f"{femur_bmd:.3f}" if femur_bmd is not None else None
        total_hip_bmd_text = f"{total_hip_bmd:.3f}" if total_hip_bmd is not None else None
        frax_text = f"{femur_frax:.1f}%" if femur_frax is not None else None
        if femur_bmd_text is not None:
            femur_line = f"Шейка бедренной кости (femoral neck). Значение МПК составило {femur_bmd_text} г/см². {femur_criterion_str}."
        else:
            femur_line = f"Шейка бедренной кости (femoral neck). {femur_criterion_str}."
        if frax_text is not None:
            femur_line = f"{femur_line} FRAX – {frax_text}"
        if total_hip_bmd_text is not None:
            total_hip_line = f"Проксимальный отдел бедра в целом (total hip). Значение МПК составило {total_hip_bmd_text} г/см². {total_hip_criterion_str}."
        else:
            total_hip_line = f"Проксимальный отдел бедра в целом (total hip). {total_hip_criterion_str}."
        description = f"""Проксимальный отдел бедра. Бедренная кость: левая.
{femur_line}
{total_hip_line}"""
        conclusion = f"""Заключение: Проксимальный отдел бедра в целом: {total_hip_diagnosis}. Шейка бедренной кости: {femur_diagnosis}."""
        full_text = f"{description}\n\n{conclusion}"
        
        self.femur_text_edit.setPlainText(full_text)
        self._clear_femur_input_fields()
        if self.spine_text_edit.toPlainText().strip():
            self.spine_text_edit.clear()
        QApplication.clipboard().setText(description)
        if getattr(self, "_on_report_generated", None):
            self._on_report_generated(description, conclusion)
    
    def _generate_all_text(self):
        """Формирует весь отчет целиком (позвоночник и бедренная кость) с валидацией"""
        # Валидация позвоночника
        spine_error = self._validate_spine()
        if spine_error:
            self._show_error_tooltip(self.generate_all_btn, spine_error)
            return
        
        # Валидация бедренной кости
        femur_error = self._validate_femur()
        if femur_error:
            self._show_error_tooltip(self.generate_all_btn, femur_error)
            return
        
        spine_t = self.spine_t_score.value()
        spine_z = self.spine_z_score.value()
        spine_type = self._get_criterion_type(spine_t, spine_z)
        femur_t = self.femur_t_score.value()
        femur_z = self.femur_z_score.value()
        femur_type = self._get_criterion_type(femur_t, femur_z)
        total_hip_t = self.total_hip_t_score.value()
        total_hip_z = self.total_hip_z_score.value()
        total_hip_type = self._get_criterion_type(total_hip_t, total_hip_z)
        if spine_type and femur_type and total_hip_type:
            if spine_type != femur_type or spine_type != total_hip_type:
                self._show_error_tooltip(
                    self.generate_all_btn,
                    "Для общего отчета используйте один тип критерия: либо T, либо Z",
                )
                return

        # Очищаем tooltip при успешной валидации
        self._clear_error_tooltip(self.generate_all_btn)
        
        # Генерируем оба текста (редакторы уже заполнены с правильными описаниями и заключениями)
        self._generate_spine_text_internal()
        self._generate_femur_text_internal()
        
        # Формируем объединённое описание и заключение для копирования (та же логика T/Z)
        spine_t = self.spine_t_score.value()
        spine_z = self.spine_z_score.value()
        spine_bmd = self.spine_bmd.value()
        spine_criterion_str, spine_value = self._get_criterion_display_and_value(spine_t, spine_z)
        spine_criterion_type = self._get_criterion_type(spine_t, spine_z)
        spine_bmd_text = f"{spine_bmd:.3f}" if spine_bmd is not None else None
        if spine_criterion_str:
            if spine_bmd_text is not None:
                spine_desc = f"""Поясничный отдел позвоночника. Поясничные позвонки: L1–L4. Среднее значение МПК составило {spine_bmd_text} г/см². {spine_criterion_str}"""
            else:
                spine_desc = f"""Поясничный отдел позвоночника. Поясничные позвонки: L1–L4. {spine_criterion_str}"""
        else:
            spine_desc = ""
        
        femur_t = self.femur_t_score.value()
        femur_z = self.femur_z_score.value()
        femur_bmd = self.femur_bmd.value()
        femur_frax = self.femur_frax.value()
        femur_criterion_str, femur_value = self._get_criterion_display_and_value(femur_t, femur_z)
        femur_criterion_type = self._get_criterion_type(femur_t, femur_z)
        total_hip_t = self.total_hip_t_score.value()
        total_hip_z = self.total_hip_z_score.value()
        total_hip_bmd = self.total_hip_bmd.value()
        total_hip_criterion_str, total_hip_value = self._get_criterion_display_and_value(total_hip_t, total_hip_z)
        total_hip_criterion_type = self._get_criterion_type(total_hip_t, total_hip_z)
        
        femur_bmd_text = f"{femur_bmd:.3f}" if femur_bmd is not None else None
        total_hip_bmd_text = f"{total_hip_bmd:.3f}" if total_hip_bmd is not None else None
        frax_text = f"{femur_frax:.1f}%" if femur_frax is not None else None
        if femur_bmd_text is not None:
            femur_line = f"Шейка бедренной кости (femoral neck). Значение МПК составило {femur_bmd_text} г/см². {femur_criterion_str}."
        else:
            femur_line = f"Шейка бедренной кости (femoral neck). {femur_criterion_str}."
        if frax_text is not None:
            femur_line = f"{femur_line} FRAX – {frax_text}"
        if total_hip_bmd_text is not None:
            total_hip_line = f"Проксимальный отдел бедра в целом (total hip). Значение МПК составило {total_hip_bmd_text} г/см². {total_hip_criterion_str}."
        else:
            total_hip_line = f"Проксимальный отдел бедра в целом (total hip). {total_hip_criterion_str}."
        femur_desc = f"""Проксимальный отдел бедра. Бедренная кость: левая.
{femur_line}
{total_hip_line}"""
        
        description = f"{spine_desc}\n\n{femur_desc}" if spine_desc else femur_desc
        
        spine_diagnosis = self._get_diagnosis(spine_value, spine_criterion_type) if spine_criterion_str else ""
        femur_diagnosis = self._get_diagnosis(femur_value, femur_criterion_type) if femur_criterion_str else ""
        total_hip_diagnosis = self._get_diagnosis(total_hip_value, total_hip_criterion_type) if total_hip_criterion_str else ""
        
        spine_conc = f"Заключение. Позвоночник - {spine_diagnosis}" if spine_criterion_str else ""
        femur_conc = f"Заключение: Проксимальный отдел бедра в целом: {total_hip_diagnosis}. Шейка бедренной кости: {femur_diagnosis}."
        conclusion = f"{spine_conc}\n\n{femur_conc}" if spine_conc else femur_conc
        
        self._clear_all_input_fields()
        QApplication.clipboard().setText(description)
        if getattr(self, "_on_report_generated", None):
            self._on_report_generated(description, conclusion)
    
    def _generate_spine_text_internal(self):
        """Внутренний метод генерации текста позвоночника без копирования в буфер"""
        spine_t = self.spine_t_score.value()
        spine_z = self.spine_z_score.value()
        spine_bmd = self.spine_bmd.value()
        criterion_str, value_for_diagnosis = self._get_criterion_display_and_value(spine_t, spine_z)
        if criterion_str is None:
            return
        spine_criterion_type = "T" if spine_t is not None else "Z"
        spine_diagnosis = self._get_diagnosis(value_for_diagnosis, spine_criterion_type)
        
        bmd_text = f"{spine_bmd:.3f}" if spine_bmd is not None else None
        if bmd_text is not None:
            description = f"""Поясничный отдел позвоночника. Поясничные позвонки: L1–L4. Среднее значение МПК составило {bmd_text} г/см². {criterion_str}"""
        else:
            description = f"""Поясничный отдел позвоночника. Поясничные позвонки: L1–L4. {criterion_str}"""
        conclusion = f"""Заключение. Позвоночник - {spine_diagnosis}"""
        full_text = f"{description}\n\n{conclusion}"
        
        self.spine_text_edit.setPlainText(full_text)
    
    def _generate_femur_text_internal(self):
        """Внутренний метод генерации текста бедренной кости без копирования в буфер"""
        femur_t = self.femur_t_score.value()
        femur_z = self.femur_z_score.value()
        femur_bmd = self.femur_bmd.value()
        femur_frax = self.femur_frax.value()
        femur_criterion_str, femur_value = self._get_criterion_display_and_value(femur_t, femur_z)
        if femur_criterion_str is None:
            return
        femur_criterion_type = self._get_criterion_type(femur_t, femur_z)
        femur_diagnosis = self._get_diagnosis(femur_value, femur_criterion_type)
        
        total_hip_t = self.total_hip_t_score.value()
        total_hip_z = self.total_hip_z_score.value()
        total_hip_bmd = self.total_hip_bmd.value()
        total_hip_criterion_str, total_hip_value = self._get_criterion_display_and_value(total_hip_t, total_hip_z)
        if total_hip_criterion_str is None:
            return
        total_hip_criterion_type = self._get_criterion_type(total_hip_t, total_hip_z)
        total_hip_diagnosis = self._get_diagnosis(total_hip_value, total_hip_criterion_type)
        
        femur_bmd_text = f"{femur_bmd:.3f}" if femur_bmd is not None else None
        total_hip_bmd_text = f"{total_hip_bmd:.3f}" if total_hip_bmd is not None else None
        frax_text = f"{femur_frax:.1f}%" if femur_frax is not None else None
        if femur_bmd_text is not None:
            femur_line = f"Шейка бедренной кости (femoral neck). Значение МПК составило {femur_bmd_text} г/см². {femur_criterion_str}."
        else:
            femur_line = f"Шейка бедренной кости (femoral neck). {femur_criterion_str}."
        if frax_text is not None:
            femur_line = f"{femur_line} FRAX – {frax_text}"
        if total_hip_bmd_text is not None:
            total_hip_line = f"Проксимальный отдел бедра в целом (total hip). Значение МПК составило {total_hip_bmd_text} г/см². {total_hip_criterion_str}."
        else:
            total_hip_line = f"Проксимальный отдел бедра в целом (total hip). {total_hip_criterion_str}."
        description = f"""Проксимальный отдел бедра. Бедренная кость: левая.
{femur_line}
{total_hip_line}"""
        conclusion = f"""Заключение: Проксимальный отдел бедра в целом: {total_hip_diagnosis}. Шейка бедренной кости: {femur_diagnosis}."""
        full_text = f"{description}\n\n{conclusion}"
        
        self.femur_text_edit.setPlainText(full_text)
    
    def get_generated_text(self) -> str:
        """Возвращает сформированный текст из редакторов"""
        spine_text = self.spine_text_edit.toPlainText() if hasattr(self, 'spine_text_edit') else ""
        femur_text = self.femur_text_edit.toPlainText() if hasattr(self, 'femur_text_edit') else ""
        
        if spine_text and femur_text:
            return f"{spine_text}\n\n{femur_text}"
        elif spine_text:
            return spine_text
        elif femur_text:
            return femur_text
        else:
            return ""


# Обязательный класс Plugin для динамической загрузки
Plugin = DensitometryPlugin