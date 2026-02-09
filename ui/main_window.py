"""Главное окно приложения"""

import sys
from pathlib import Path
from typing import List, Optional

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication,
    QPushButton, QScrollArea, QLabel, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence
from core.plugin_base import ModalityPlugin


def _simulate_paste():
    """Симулирует вставку из буфера (Cmd+V на macOS, Ctrl+V на Windows/Linux)."""
    try:
        from pynput.keyboard import Key, Controller
        ctrl = Controller()
        mod = Key.cmd if sys.platform == "darwin" else Key.ctrl
        ctrl.press(mod)
        ctrl.press("v")
        ctrl.release("v")
        ctrl.release(mod)
    except Exception:
        pass


class MainWindow(QMainWindow):
    """Главное окно с двумя панелями: список плагинов слева, виджет плагина справа"""
    
    def __init__(self, plugins: List[ModalityPlugin]):
        super().__init__()
        self.plugins = plugins
        self.current_plugin: Optional[ModalityPlugin] = None
        self.current_widget: Optional[QWidget] = None
        # Последний сформированный отчёт (обновляется при нажатии «Сформировать»/«Сформировать отчёт»)
        self._last_description = ""
        self._last_conclusion = ""

        self.setWindowTitle("Конструктор рентгеновских заключений")
        self.setGeometry(100, 100, 1200, 800)
        
        self._setup_ui()
        self._setup_hotkeys()
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Верхняя панель: выбор модальностей горизонтально
        modality_panel = self._create_modality_panel()
        main_layout.addWidget(modality_panel)
        
        # Основная панель: виджет текущего плагина
        plugin_panel = self._create_plugin_widget_panel()
        main_layout.addWidget(plugin_panel)

    def _setup_hotkeys(self):
        """Горячая клавиша: Ctrl+Shift+V — вставить сформированное заключение."""
        self._shortcut_paste_conclusion = QShortcut(
            QKeySequence("Ctrl+Shift+V"), self, context=Qt.ApplicationShortcut
        )
        self._shortcut_paste_conclusion.activated.connect(self._on_paste_conclusion)

    def _store_report(self, description: str, conclusion: str):
        """Вызывается плагином при нажатии «Сформировать»/«Сформировать отчёт» — для Ctrl+Shift+V."""
        self._last_description = description or ""
        self._last_conclusion = conclusion or ""

    def _on_paste_conclusion(self):
        """Вставляет сформированное заключение по Ctrl+Shift+V."""
        if not self._last_conclusion:
            return
        QApplication.clipboard().setText(self._last_conclusion)
        _simulate_paste()
    
    def _create_modality_panel(self) -> QWidget:
        """Создает верхнюю панель с выбором модальностей горизонтально"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Модальности:")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Кнопки в том же порядке, что и self.plugins — плагин по индексу: self.plugins[i]
        self.plugin_buttons = []
        for plugin in self.plugins:
            btn = QPushButton(plugin.get_name())
            btn.setMinimumHeight(40)
            btn.setMinimumWidth(150)
            btn.setToolTip(plugin.get_description())
            btn.clicked.connect(self._on_modality_button_clicked)
            layout.addWidget(btn)
            self.plugin_buttons.append(btn)
        
        layout.addStretch()
        
        return panel

    def _on_modality_button_clicked(self):
        """Определяет плагин по индексу нажатой кнопки и переключает модальность."""
        btn = self.sender()
        if btn is None:
            return
        try:
            idx = self.plugin_buttons.index(btn)
        except (ValueError, AttributeError):
            return
        if 0 <= idx < len(self.plugins):
            self._on_plugin_selected(self.plugins[idx])
    
    def _create_plugin_widget_panel(self) -> QWidget:
        """Создает панель для отображения виджета плагина"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.plugin_title = QLabel("Выберите модальность")
        self.plugin_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(self.plugin_title)
        
        # Скроллируемая область для виджета плагина
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignTop)
        
        self.plugin_container = QWidget()
        self.plugin_container_layout = QVBoxLayout(self.plugin_container)
        self.plugin_container_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(self.plugin_container)
        layout.addWidget(scroll_area)
        
        return panel
    
    def _on_plugin_selected(self, plugin: ModalityPlugin):
        """Обработчик выбора плагина"""
        self.current_plugin = plugin
        self.plugin_title.setText(plugin.get_name())
        # При смене модальности сбрасываем сохранённый отчёт — горячие клавиши будут вставлять только отчёт, сформированный в текущей модальности
        self._last_description = ""
        self._last_conclusion = ""

        # Удаляем предыдущий виджет
        if self.current_widget:
            self.current_widget.setParent(None)
            self.current_widget.deleteLater()
        
        # Создаем виджет; плагин при «Сформировать» вызывает _store_report — горячие клавиши вставляют этот текст
        self.current_widget = plugin.create_widget(on_report_generated=self._store_report)
        self.plugin_container_layout.addWidget(self.current_widget)
        
        # Выделяем выбранную кнопку
        for btn in self.plugin_buttons:
            btn.setStyleSheet("")
        for btn in self.plugin_buttons:
            if btn.text() == plugin.get_name():
                btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
                break
