"""Плагин денситометрии с улучшенной обработкой текста"""

import sys
from pathlib import Path
from enum import Enum
from typing import Optional

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QDoubleSpinBox, QGroupBox, QFormLayout, QTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QClipboard
from core.plugin_base import ModalityPlugin


class ClipboardState(Enum):
    """Состояния машины для отслеживания копирования в буфер обмена"""
    IDLE = "idle"
    WAITING_FIRST_PASTE = "waiting_first_paste"
    WAITING_SECOND_PASTE = "waiting_second_paste"


class DensitometryPlugin(ModalityPlugin):
    """Плагин для работы с денситометрией"""
    
    def __init__(self):
        # Состояние копирования в буфер обмена
        self.clipboard_state = ClipboardState.IDLE
        self.clipboard = None
        self.clipboard_description = ""  # Текст описания для первой вставки
        self.clipboard_conclusion = ""    # Текст заключения для второй вставки
        self.is_clipboard_change_ours = False  # Флаг для предотвращения рекурсии
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_clipboard)
        
    def get_name(self) -> str:
        return "Денситометрия"
    
    def get_description(self) -> str:
        return "Плагин для работы с денситометрическими исследованиями"
    
    def create_widget(self) -> QWidget:
        """Создает виджет с полями для T/Z-критериев и костной массы"""
        widget = QWidget()
        main_layout = QHBoxLayout(widget)
        main_layout.setSpacing(10)
        
        # Инициализируем буфер обмена
        from PySide6.QtWidgets import QApplication
        self.clipboard = QApplication.clipboard()
        
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
        
        # Текстовое поле для бедренной кости
        femur_text_group = QGroupBox("Текст заключения - Бедренная кость")
        femur_text_layout = QVBoxLayout()
        
        self.femur_text_edit = QTextEdit()
        self.femur_text_edit.setPlainText("")
        self.femur_text_edit.setMinimumHeight(200)
        femur_text_layout.addWidget(self.femur_text_edit)
        
        femur_text_group.setLayout(femur_text_layout)
        left_column.addWidget(femur_text_group)
        
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
        
        self.spine_t_score = QDoubleSpinBox()
        self.spine_t_score.setRange(-5.0, 5.0)
        self.spine_t_score.setSingleStep(0.1)
        self.spine_t_score.setValue(0.0)
        self.spine_t_score.setDecimals(2)  # 2 знака для UI
        
        self.spine_z_score = QDoubleSpinBox()
        self.spine_z_score.setRange(-5.0, 5.0)
        self.spine_z_score.setSingleStep(0.1)
        self.spine_z_score.setValue(0.0)
        self.spine_z_score.setDecimals(2)  # 2 знака для UI
        
        self.spine_bmd = QDoubleSpinBox()
        self.spine_bmd.setRange(0.0, 2.0)
        self.spine_bmd.setSingleStep(0.01)
        self.spine_bmd.setValue(0.0)
        self.spine_bmd.setDecimals(3)
        
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
        
        self.femur_t_score = QDoubleSpinBox()
        self.femur_t_score.setRange(-5.0, 5.0)
        self.femur_t_score.setSingleStep(0.1)
        self.femur_t_score.setValue(0.0)
        self.femur_t_score.setDecimals(2)  # 2 знака для UI
        
        self.femur_z_score = QDoubleSpinBox()
        self.femur_z_score.setRange(-5.0, 5.0)
        self.femur_z_score.setSingleStep(0.1)
        self.femur_z_score.setValue(0.0)
        self.femur_z_score.setDecimals(2)  # 2 знака для UI
        
        self.femur_bmd = QDoubleSpinBox()
        self.femur_bmd.setRange(0.0, 2.0)
        self.femur_bmd.setSingleStep(0.01)
        self.femur_bmd.setValue(0.0)
        self.femur_bmd.setDecimals(3)
        
        self.femur_frax = QDoubleSpinBox()
        self.femur_frax.setRange(0.0, 100.0)
        self.femur_frax.setSingleStep(0.1)
        self.femur_frax.setValue(0.0)
        self.femur_frax.setDecimals(1)
        
        femur_layout.addRow("T-критерий:", self.femur_t_score)
        femur_layout.addRow("Z-критерий:", self.femur_z_score)
        femur_layout.addRow("Костная масса (г/см²):", self.femur_bmd)
        femur_layout.addRow("FRAX (%):", self.femur_frax)
        
        femur_group.setLayout(femur_layout)
        right_column.addWidget(femur_group)
        
        # Группа для проксимального отдела бедра в целом (total hip)
        total_hip_group = QGroupBox("Проксимальный отдел бедра в целом (total hip)")
        total_hip_layout = QFormLayout()
        
        self.total_hip_t_score = QDoubleSpinBox()
        self.total_hip_t_score.setRange(-5.0, 5.0)
        self.total_hip_t_score.setSingleStep(0.1)
        self.total_hip_t_score.setValue(0.0)
        self.total_hip_t_score.setDecimals(2)  # 2 знака для UI
        
        self.total_hip_z_score = QDoubleSpinBox()
        self.total_hip_z_score.setRange(-5.0, 5.0)
        self.total_hip_z_score.setSingleStep(0.1)
        self.total_hip_z_score.setValue(0.0)
        self.total_hip_z_score.setDecimals(2)  # 2 знака для UI
        
        self.total_hip_bmd = QDoubleSpinBox()
        self.total_hip_bmd.setRange(0.0, 2.0)
        self.total_hip_bmd.setSingleStep(0.01)
        self.total_hip_bmd.setValue(0.0)
        self.total_hip_bmd.setDecimals(3)
        
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
    
    def _get_diagnosis(self, t_score: float) -> str:
        """Определяет диагноз по T-критерию согласно классификации ВОЗ"""
        if t_score <= -2.5:
            return "Остеопороз"
        elif -2.5 < t_score <= -2.0:
            return "Остеопения 3 ст."
        elif -2.0 < t_score <= -1.5:
            return "Остеопения 2 ст"
        elif -1.5 < t_score <= -1.1:
            return "Остеопения 1 ст"
        else:  # t_score > -1.1
            return "Норма"
    
    def _validate_spine(self) -> Optional[str]:
        """Валидация полей позвоночника"""
        spine_bmd = self.spine_bmd.value()
        spine_t = self.spine_t_score.value()
        spine_z = self.spine_z_score.value()
        
        if spine_bmd == 0.0 or (spine_t == 0.0 and spine_z == 0.0):
            return "Для позвоночника заполните костную массу и хотя бы один критерий (T или Z)"
        return None
    
    def _validate_femur(self) -> Optional[str]:
        """Валидация полей бедренной кости"""
        # Проверка шейки бедренной кости
        femur_bmd = self.femur_bmd.value()
        femur_t = self.femur_t_score.value()
        femur_z = self.femur_z_score.value()
        femur_frax = self.femur_frax.value()
        
        if femur_bmd == 0.0 or (femur_t == 0.0 and femur_z == 0.0) or femur_frax == 0.0:
            return "Для шейки бедренной кости заполните костную массу, хотя бы один критерий (T или Z) и FRAX"
        
        # Проверка total hip
        total_hip_bmd = self.total_hip_bmd.value()
        total_hip_t = self.total_hip_t_score.value()
        total_hip_z = self.total_hip_z_score.value()
        
        if total_hip_bmd == 0.0 or (total_hip_t == 0.0 and total_hip_z == 0.0):
            return "Для проксимального отдела бедра (total hip) заполните костную массу и хотя бы один критерий (T или Z)"
        
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
    
    def _copy_to_clipboard_with_tracking(self, description: str, conclusion: str):
        """Копирует текст в буфер обмена с отслеживанием вставок"""
        # Отменяем предыдущую операцию, если она активна
        if self.clipboard_state != ClipboardState.IDLE:
            self.check_timer.stop()
            self.clipboard_state = ClipboardState.IDLE
        
        # Сохраняем тексты
        self.clipboard_description = description
        self.clipboard_conclusion = conclusion
        
        # Копируем описание в буфер
        self.is_clipboard_change_ours = True
        self.clipboard.setText(description)
        self.is_clipboard_change_ours = False
        
        # Устанавливаем состояние ожидания первой вставки
        self.clipboard_state = ClipboardState.WAITING_FIRST_PASTE
        
        # Запускаем таймер для проверки
        self.check_timer.start(100)  # Проверяем каждые 100 мс
    
    def _check_clipboard(self):
        """Проверяет состояние буфера обмена и обновляет его по необходимости"""
        current_text = self.clipboard.text()
        
        if self.clipboard_state == ClipboardState.WAITING_FIRST_PASTE:
            # Проверяем, было ли описание вставлено
            # Если буфер пуст или текст не совпадает с описанием, предполагаем, что текст был вставлен
            if not current_text or current_text != self.clipboard_description:
                # Заменяем на заключение
                self.is_clipboard_change_ours = True
                self.clipboard.setText(self.clipboard_conclusion)
                self.is_clipboard_change_ours = False
                self.clipboard_state = ClipboardState.WAITING_SECOND_PASTE
        
        elif self.clipboard_state == ClipboardState.WAITING_SECOND_PASTE:
            # Проверяем, было ли заключение вставлено
            if not current_text or current_text != self.clipboard_conclusion:
                # Останавливаем таймер и сбрасываем состояние
                self.check_timer.stop()
                self.clipboard_state = ClipboardState.IDLE
    
    def _generate_spine_text(self):
        """Формирует текст для позвоночника с валидацией и копированием в буфер"""
        # Валидация
        error = self._validate_spine()
        if error:
            self._show_error_tooltip(self.spine_generate_btn, error)
            return
        
        # Очищаем tooltip при успешной валидации
        self._clear_error_tooltip(self.spine_generate_btn)
        
        # Получаем текущие значения
        spine_t = self.spine_t_score.value()
        spine_bmd = self.spine_bmd.value()
        spine_diagnosis = self._get_diagnosis(spine_t)
        
        # Формируем текст описания (для первой вставки)
        description = f"""Поясничный отдел позвоночника. Поясничные позвонки: L1–L4. Среднее значение МПК составило {spine_bmd:.3f} г/см². Т-критерий – {spine_t:.1f}"""
        
        # Формируем текст заключения (для второй вставки)
        conclusion = f"""Заключение. Позвоночник - {spine_diagnosis}"""
        
        # Полный текст для отображения в редакторе
        full_text = f"{description}\n\n{conclusion}"
        
        # Обновляем текстовое поле позвоночника
        self.spine_text_edit.setPlainText(full_text)
        
        # Копируем в буфер обмена с отслеживанием
        self._copy_to_clipboard_with_tracking(description, conclusion)
    
    def _generate_femur_text(self):
        """Формирует текст для бедренной кости с валидацией и копированием в буфер"""
        # Валидация
        error = self._validate_femur()
        if error:
            self._show_error_tooltip(self.femur_generate_btn, error)
            return
        
        # Очищаем tooltip при успешной валидации
        self._clear_error_tooltip(self.femur_generate_btn)
        
        # Получаем текущие значения для шейки бедренной кости
        femur_t = self.femur_t_score.value()
        femur_z = self.femur_z_score.value()
        femur_bmd = self.femur_bmd.value()
        femur_frax = self.femur_frax.value()
        femur_diagnosis = self._get_diagnosis(femur_t)
        
        # Получаем текущие значения для total hip
        total_hip_t = self.total_hip_t_score.value()
        total_hip_z = self.total_hip_z_score.value()
        total_hip_bmd = self.total_hip_bmd.value()
        total_hip_diagnosis = self._get_diagnosis(total_hip_t)
        
        # Формируем текст описания (для первой вставки)
        description = f"""Проксимальный отдел бедра. Бедренная кость: левая.
Шейка бедренной кости (femoral neck). Значение МПК составило {femur_bmd:.3f} г/см². Т-критерий – {femur_t:.1f}. Z-критерий – {femur_z:.1f}. FRAX – {femur_frax:.1f}%
Проксимальный отдел бедра в целом (total hip). Значение МПК составило {total_hip_bmd:.3f} г/см². Т-критерий – {total_hip_t:.1f}. Z-критерий – {total_hip_z:.1f}."""
        
        # Формируем текст заключения (для второй вставки)
        conclusion = f"""Заключение: Проксимальный отдел бедра в целом: {total_hip_diagnosis}. Шейка бедренной кости: {femur_diagnosis}."""
        
        # Полный текст для отображения в редакторе
        full_text = f"{description}\n\n{conclusion}"
        
        # Обновляем текстовое поле бедренной кости
        self.femur_text_edit.setPlainText(full_text)
        
        # Копируем в буфер обмена с отслеживанием
        self._copy_to_clipboard_with_tracking(description, conclusion)
    
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
        
        # Очищаем tooltip при успешной валидации
        self._clear_error_tooltip(self.generate_all_btn)
        
        # Генерируем оба текста
        self._generate_spine_text_internal()
        self._generate_femur_text_internal()
        
        # Формируем объединенный текст для копирования
        # Описание (позвоночник + бедро)
        spine_t = self.spine_t_score.value()
        spine_bmd = self.spine_bmd.value()
        spine_desc = f"""Поясничный отдел позвоночника. Поясничные позвонки: L1–L4. Среднее значение МПК составило {spine_bmd:.3f} г/см². Т-критерий – {spine_t:.1f}"""
        
        femur_t = self.femur_t_score.value()
        femur_z = self.femur_z_score.value()
        femur_bmd = self.femur_bmd.value()
        femur_frax = self.femur_frax.value()
        total_hip_t = self.total_hip_t_score.value()
        total_hip_z = self.total_hip_z_score.value()
        total_hip_bmd = self.total_hip_bmd.value()
        
        femur_desc = f"""Проксимальный отдел бедра. Бедренная кость: левая.
Шейка бедренной кости (femoral neck). Значение МПК составило {femur_bmd:.3f} г/см². Т-критерий – {femur_t:.1f}. Z-критерий – {femur_z:.1f}. FRAX – {femur_frax:.1f}%
Проксимальный отдел бедра в целом (total hip). Значение МПК составило {total_hip_bmd:.3f} г/см². Т-критерий – {total_hip_t:.1f}. Z-критерий – {total_hip_z:.1f}."""
        
        description = f"{spine_desc}\n\n{femur_desc}"
        
        # Заключение (позвоночник + бедро)
        spine_diagnosis = self._get_diagnosis(spine_t)
        femur_diagnosis = self._get_diagnosis(femur_t)
        total_hip_diagnosis = self._get_diagnosis(total_hip_t)
        
        spine_conc = f"Заключение. Позвоночник - {spine_diagnosis}"
        femur_conc = f"Заключение: Проксимальный отдел бедра в целом: {total_hip_diagnosis}. Шейка бедренной кости: {femur_diagnosis}."
        
        conclusion = f"{spine_conc}\n\n{femur_conc}"
        
        # Копируем в буфер обмена с отслеживанием
        self._copy_to_clipboard_with_tracking(description, conclusion)
    
    def _generate_spine_text_internal(self):
        """Внутренний метод генерации текста позвоночника без копирования в буфер"""
        spine_t = self.spine_t_score.value()
        spine_bmd = self.spine_bmd.value()
        spine_diagnosis = self._get_diagnosis(spine_t)
        
        description = f"""Поясничный отдел позвоночника. Поясничные позвонки: L1–L4. Среднее значение МПК составило {spine_bmd:.3f} г/см². Т-критерий – {spine_t:.1f}"""
        conclusion = f"""Заключение. Позвоночник - {spine_diagnosis}"""
        full_text = f"{description}\n\n{conclusion}"
        
        self.spine_text_edit.setPlainText(full_text)
    
    def _generate_femur_text_internal(self):
        """Внутренний метод генерации текста бедренной кости без копирования в буфер"""
        femur_t = self.femur_t_score.value()
        femur_z = self.femur_z_score.value()
        femur_bmd = self.femur_bmd.value()
        femur_frax = self.femur_frax.value()
        femur_diagnosis = self._get_diagnosis(femur_t)
        
        total_hip_t = self.total_hip_t_score.value()
        total_hip_z = self.total_hip_z_score.value()
        total_hip_bmd = self.total_hip_bmd.value()
        total_hip_diagnosis = self._get_diagnosis(total_hip_t)
        
        description = f"""Проксимальный отдел бедра. Бедренная кость: левая.
Шейка бедренной кости (femoral neck). Значение МПК составило {femur_bmd:.3f} г/см². Т-критерий – {femur_t:.1f}. Z-критерий – {femur_z:.1f}. FRAX – {femur_frax:.1f}%
Проксимальный отдел бедра в целом (total hip). Значение МПК составило {total_hip_bmd:.3f} г/см². Т-критерий – {total_hip_t:.1f}. Z-критерий – {total_hip_z:.1f}."""
        
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