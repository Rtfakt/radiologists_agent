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
        """Горячие клавиши: Ctrl+Shift+S — вставить описание, Ctrl+Shift+D — вставить заключение."""
        self._shortcut_description = QShortcut(
            QKeySequence("Ctrl+Shift+S"), self, context=Qt.ApplicationShortcut
        )
        self._shortcut_description.activated.connect(self._on_paste_description)
        self._shortcut_conclusion = QShortcut(
            QKeySequence("Ctrl+Shift+D"), self, context=Qt.ApplicationShortcut
        )
        self._shortcut_conclusion.activated.connect(self._on_paste_conclusion)

    def _on_paste_description(self):
        """Копирует описание в буфер и симулирует вставку в активное окно."""
        if not self.current_plugin:
            return
        text = self.current_plugin.get_description_text()
        if not text:
            return
        QApplication.clipboard().setText(text)
        _simulate_paste()

    def _on_paste_conclusion(self):
        """Копирует заключение в буфер и симулирует вставку в активное окно."""
        if not self.current_plugin:
            return
        text = self.current_plugin.get_conclusion_text()
        if not text:
            return
        QApplication.clipboard().setText(text)
        _simulate_paste()
    
    def _create_modality_panel(self) -> QWidget:
        """Создает верхнюю панель с выбором модальностей горизонтально"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Модальности:")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Явное сопоставление кнопка -> плагин (исключает ошибки захвата в замыканиях)
        self._button_to_plugin: dict = {}
        self.plugin_buttons = []
        
        for plugin in self.plugins:
            btn = QPushButton(plugin.get_name())
            btn.setMinimumHeight(40)
            btn.setMinimumWidth(150)
            btn.setToolTip(plugin.get_description())
            self._button_to_plugin[id(btn)] = plugin
            btn.clicked.connect(self._on_modality_button_clicked)
            layout.addWidget(btn)
            self.plugin_buttons.append(btn)
        
        layout.addStretch()
        
        return panel

    def _on_modality_button_clicked(self):
        """Определяет плагин по нажатой кнопке и переключает модальность."""
        btn = self.sender()
        if btn is not None and isinstance(btn, QPushButton):
            plugin = self._button_to_plugin.get(id(btn))
            if plugin is not None:
                self._on_plugin_selected(plugin)
    
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
        
        # Удаляем предыдущий виджет
        if self.current_widget:
            self.current_widget.setParent(None)
            self.current_widget.deleteLater()
        
        # Создаем новый виджет плагина
        self.current_widget = plugin.create_widget()
        self.plugin_container_layout.addWidget(self.current_widget)
        
        # Выделяем выбранную кнопку
        for btn in self.plugin_buttons:
            btn.setStyleSheet("")
        for btn in self.plugin_buttons:
            if btn.text() == plugin.get_name():
                btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
                break
