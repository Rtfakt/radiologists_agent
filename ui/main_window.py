"""Главное окно приложения"""

import sys
from pathlib import Path
from typing import List, Optional

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QScrollArea, QLabel, QSplitter
)
from PySide6.QtCore import Qt
from core.plugin_base import ModalityPlugin


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
    
    def _create_modality_panel(self) -> QWidget:
        """Создает верхнюю панель с выбором модальностей горизонтально"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Модальности:")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Кнопка «Рентген» (плагин конструктора рентгеновских исследований)
        self._xray_plugin = next(
            (p for p in self.plugins if p.get_name() == "Рентген"),
            None,
        )
        if self._xray_plugin is not None:
            btn_rentgen = QPushButton("Рентген")
            btn_rentgen.setMinimumHeight(40)
            btn_rentgen.setMinimumWidth(150)
            btn_rentgen.setToolTip(self._xray_plugin.get_description())
            btn_rentgen.clicked.connect(
                lambda checked: self._on_plugin_selected(self._xray_plugin)
            )
            layout.addWidget(btn_rentgen)
            self.plugin_buttons = [btn_rentgen]
        else:
            self.plugin_buttons = []
        
        # Остальные плагины (без дублирования рентгена)
        for plugin in self.plugins:
            if plugin.get_name() == "Рентген":
                continue
            btn = QPushButton(plugin.get_name())
            btn.setMinimumHeight(40)
            btn.setMinimumWidth(150)
            btn.setToolTip(plugin.get_description())
            btn.clicked.connect(lambda checked, p=plugin: self._on_plugin_selected(p))
            layout.addWidget(btn)
            self.plugin_buttons.append(btn)
        
        layout.addStretch()
        
        return panel
    
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
