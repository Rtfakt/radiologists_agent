"""Плагин маммографии"""

import json
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QApplication,
    QPushButton, QButtonGroup, QGroupBox, QTextEdit
)
from PySide6.QtGui import QShortcut, QKeySequence
import re
from core.plugin_base import ModalityPlugin

PLUGIN_DIR = Path(__file__).parent


def _load_json(name: str) -> dict:
    """Загружает JSON из папки плагина."""
    path = PLUGIN_DIR / name
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class MammographyPlugin(ModalityPlugin):
    """Плагин для работы с маммографией"""

    def __init__(self):
        self.density = "B"
        self.pathology_key = "норма"
        self.side = "правая"

        self.densities = _load_json("densities.json")
        self.pathologies = _load_json("pathologies.json")

        if not self.densities:
            self.densities = {}
        if not self.pathologies:
            self.pathologies = {}

    def get_name(self) -> str:
        return "Маммография"

    def get_description(self) -> str:
        return "Плагин для работы с маммографическими исследованиями"

    def _get_density_description(self) -> str:
        """Возвращает текст описания плотности для выбранной буквы."""
        d = self.densities.get(self.density, {})
        return d.get("description", "")

    def _get_base_description_for_side(self, side: str) -> str:
        """Базовое описание для стороны из патологии «норма» с подстановкой плотности."""
        norm = self.pathologies.get("норма", {})
        desc = norm.get("description", {})
        template = desc.get(side, "")
        density_text = self._get_density_description()
        return template.replace("{density}", density_text)

    def _get_description_for_side(self, side: str) -> str:
        """Формирует описание для одной стороны (правая/левая)."""
        pathology = self.pathologies.get(self.pathology_key, {})
        density_text = self._get_density_description()

        if "description_replacements" in pathology:
            base = self._get_base_description_for_side(side)
            # Замену применяем только на поражённой стороне
            if side == self.side:
                repl = pathology["description_replacements"].get(side, {})
                search_s = repl.get("search", "")
                replace_s = repl.get("replace", "")
                if search_s and replace_s:
                    base = base.replace(search_s, replace_s)
            return base

        desc = pathology.get("description", {})
        template = desc.get(side, "")
        return template.replace("{density}", density_text)

    def _build_full_report(self) -> str:
        """Собирает полный отчёт: описание правой и левой, заключение, BIRADS, рекомендации."""
        pathology = self.pathologies.get(self.pathology_key, {})
        if not pathology:
            return ""

        desc_right = self._get_description_for_side("правая")
        desc_left = self._get_description_for_side("левая")

        if pathology.get("requires_side"):
            side_display = "справа" if self.side == "правая" else "слева"
            conclusion = pathology.get("conclusion", "").format(side=side_display)
            birads_right = pathology["birads"]["правая"]
            birads_left = pathology["birads"]["левая"]
            if self.side == "левая":
                birads_right, birads_left = birads_left, birads_right
            birads_line = f"BIRADS {birads_right} справа, BIRADS {birads_left} слева"
        else:
            conclusion = pathology.get("conclusion", "")
            birads = pathology.get("birads", {}).get("правая", "1")
            birads_line = f"BIRADS {birads} СПРАВА И СЛЕВА"

        followup = pathology.get("followup", "")

        parts = [
            desc_right,
            "",
            desc_left,
            "",
            f"ЗАКЛЮЧЕНИЕ: {conclusion}",
            birads_line,
            "",
            followup,
        ]
        return "\n".join(parts)

    def create_widget(self, on_report_generated=None) -> QWidget:
        """Создаёт виджет с выбором плотности, патологии и стороны."""
        self._on_report_generated = on_report_generated
        widget = QWidget()
        main_layout = QHBoxLayout(widget)
        main_layout.setSpacing(10)

        # Левая колонка
        left_column = QVBoxLayout()

        text_group = QGroupBox("Текст заключения (редактируемый)")
        text_layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self._build_full_report())
        self.text_edit.setMinimumHeight(400)
        text_layout.addWidget(self.text_edit)
        text_group.setLayout(text_layout)
        left_column.addWidget(text_group)

        generate_report_btn = QPushButton("Сформировать отчет")
        generate_report_btn.setMinimumHeight(40)
        generate_report_btn.clicked.connect(self._generate_report)
        left_column.addWidget(generate_report_btn)

        copy_btns = QHBoxLayout()
        btn_copy_desc = QPushButton("Скопировать описание")
        btn_copy_desc.setMinimumHeight(36)
        btn_copy_desc.clicked.connect(self._copy_description)
        btn_copy_conc = QPushButton("Скопировать заключение")
        btn_copy_conc.setMinimumHeight(36)
        btn_copy_conc.clicked.connect(self._copy_conclusion)
        copy_btns.addWidget(btn_copy_desc)
        copy_btns.addWidget(btn_copy_conc)
        left_column.addLayout(copy_btns)
        left_column.addStretch()

        # Правая колонка
        right_column = QVBoxLayout()

        density_group = QGroupBox("Плотность молочной железы (ACR)")
        density_layout = QHBoxLayout()
        self.density_buttons = QButtonGroup()
        for letter in ("A", "B", "C", "D"):
            btn = QPushButton(letter)
            btn.setCheckable(True)
            btn.setMinimumHeight(40)
            density_layout.addWidget(btn)
            self.density_buttons.addButton(btn)
        self.density_buttons.buttonClicked.connect(self._on_density_changed)
        for btn in self.density_buttons.buttons():
            if btn.text() == "B":
                btn.setChecked(True)
                break
        density_group.setLayout(density_layout)
        right_column.addWidget(density_group)

        pathology_group = QGroupBox("Патология / Заключение")
        pathology_layout = QVBoxLayout()
        self.pathology_buttons = QButtonGroup()
        for key, data in self.pathologies.items():
            name = data.get("name", key)
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setMinimumHeight(35)
            btn.setProperty("pathology_key", key)
            pathology_layout.addWidget(btn)
            self.pathology_buttons.addButton(btn)
        self.pathology_buttons.buttonClicked.connect(self._on_pathology_changed)
        for btn in self.pathology_buttons.buttons():
            if btn.property("pathology_key") == "норма":
                btn.setChecked(True)
                break
        pathology_group.setLayout(pathology_layout)
        right_column.addWidget(pathology_group)

        self.side_group = QGroupBox("Сторона")
        side_layout = QHBoxLayout()
        self.side_buttons = QButtonGroup()
        btn_right = QPushButton("Правая")
        btn_right.setCheckable(True)
        btn_right.setChecked(True)
        btn_right.setMinimumHeight(35)
        btn_left = QPushButton("Левая")
        btn_left.setCheckable(True)
        btn_left.setMinimumHeight(35)
        side_layout.addWidget(btn_right)
        side_layout.addWidget(btn_left)
        self.side_buttons.addButton(btn_right)
        self.side_buttons.addButton(btn_left)
        self.side_buttons.buttonClicked.connect(self._on_side_changed)
        self.side_group.setLayout(side_layout)
        right_column.addWidget(self.side_group)
        self._update_side_group_visibility()

        right_column.addStretch()

        main_layout.addLayout(left_column, 2)
        main_layout.addLayout(right_column, 1)

        # Горячие клавиши: Ctrl+Alt+S — скопировать описание, Ctrl+Alt+D — скопировать заключение
        self._shortcut_copy_desc = QShortcut(QKeySequence("Ctrl+Alt+S"), widget)
        self._shortcut_copy_desc.activated.connect(self._copy_description)
        self._shortcut_copy_conc = QShortcut(QKeySequence("Ctrl+Alt+D"), widget)
        self._shortcut_copy_conc.activated.connect(self._copy_conclusion)

        return widget

    def _update_side_group_visibility(self):
        """Показывает группу «Сторона» только для патологий с requires_side."""
        pathology = self.pathologies.get(self.pathology_key, {})
        self.side_group.setVisible(bool(pathology.get("requires_side")))

    def _on_density_changed(self, button: QPushButton):
        self.density = button.text()

    def _on_pathology_changed(self, button: QPushButton):
        key = button.property("pathology_key")
        if key is not None:
            self.pathology_key = key
        self._update_side_group_visibility()

    def _on_side_changed(self, button: QPushButton):
        self.side = "правая" if button.text() == "Правая" else "левая"

    def _generate_report(self):
        """Формирует отчёт и подставляет его в редактор, копирует описание в буфер."""
        full = self._build_full_report()
        self.text_edit.setPlainText(full)
        desc = self._get_description_from_text(full)
        conc = self._get_conclusion_from_text(full)
        if desc:
            QApplication.clipboard().setText(desc)
        if getattr(self, "_on_report_generated", None):
            self._on_report_generated(desc or "", conc or "")

    def _get_description_from_text(self, text: str) -> str:
        """Текст до «ЗАКЛЮЧЕНИЕ:» — только описание."""
        if not text or not text.strip():
            return ""
        match = re.search(r"ЗАКЛЮЧЕНИЕ\s*:", text, re.IGNORECASE)
        if match:
            return text[: match.start()].strip()
        return text.strip()

    def _get_conclusion_from_text(self, text: str) -> str:
        """Текст с «ЗАКЛЮЧЕНИЕ:» до конца — заключение, BIRADS и рекомендации."""
        if not text or not text.strip():
            return ""
        match = re.search(r"ЗАКЛЮЧЕНИЕ\s*:.*", text, re.DOTALL | re.IGNORECASE)
        if match:
            return text[match.start() :].strip()
        return ""

    def _copy_description(self):
        text = self.text_edit.toPlainText()
        QApplication.clipboard().setText(self._get_description_from_text(text))

    def _copy_conclusion(self):
        text = self.text_edit.toPlainText()
        QApplication.clipboard().setText(self._get_conclusion_from_text(text))

    def get_description_text(self) -> str:
        if not hasattr(self, "text_edit"):
            return ""
        return self._get_description_from_text(self.text_edit.toPlainText())

    def get_conclusion_text(self) -> str:
        if not hasattr(self, "text_edit"):
            return ""
        return self._get_conclusion_from_text(self.text_edit.toPlainText())

    def get_generated_text(self) -> str:
        return self.text_edit.toPlainText() if hasattr(self, "text_edit") else ""


Plugin = MammographyPlugin
