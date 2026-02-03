"""Плагин «Конструктор рентгеновских исследований»"""

import sys
import json
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup,
    QGroupBox, QTextEdit, QComboBox, QRadioButton, QScrollArea, QFileDialog,
    QMessageBox, QInputDialog, QFrame, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard

try:
    from PySide6.QtSvg import QSvgWidget
except ImportError:
    QSvgWidget = None

from core.plugin_base import ModalityPlugin


PLUGIN_DIR = Path(__file__).parent
DEFAULT_CONFIG_PATH = PLUGIN_DIR / "config.json"
DEFAULT_PRESETS_PATH = PLUGIN_DIR / "presets.json"


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path: Path, data: Any) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


class PathologyCard(QFrame):
    """Карточка одной патологии: название, радиокнопки стороны, кнопка удаления."""

    def __init__(self, pathology: dict, initial_side_id: str, on_delete, on_side_changed):
        super().__init__()
        self.pathology = pathology
        self.on_delete = on_delete
        self.on_side_changed = on_side_changed
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(pathology["название"]))
        self.side_group = QButtonGroup(self)
        sides_layout = QHBoxLayout()
        for side in pathology.get("стороны", []):
            rb = QRadioButton(side["название"])
            rb.setProperty("side_id", side["id"])
            rb.toggled.connect(self._on_toggled)
            if side["id"] == initial_side_id:
                rb.setChecked(True)
            self.side_group.addButton(rb)
            sides_layout.addWidget(rb)
        layout.addLayout(sides_layout)
        row = QHBoxLayout()
        row.addStretch()
        btn_del = QPushButton("✕ УДАЛИТЬ")
        btn_del.setMaximumWidth(120)
        btn_del.clicked.connect(self._do_delete)
        row.addWidget(btn_del)
        layout.addLayout(row)

    def _on_toggled(self, checked: bool):
        if checked:
            btn = self.side_group.checkedButton()
            if btn:
                self.on_side_changed(btn.property("side_id"))

    def _do_delete(self):
        self.on_delete()

    def get_side_id(self) -> str:
        btn = self.side_group.checkedButton()
        return btn.property("side_id") if btn else ""


class XrayConstructorPlugin(ModalityPlugin):
    """Плагин для генерации описаний и заключений по рентгеновским исследованиям."""

    def __init__(self):
        self._config_path = DEFAULT_CONFIG_PATH
        self._presets_path = DEFAULT_PRESETS_PATH
        self._config = _load_json(self._config_path, {"исследования": []})
        self._presets = _load_json(self._presets_path, [])
        self._current_study_id: str | None = None
        self._pathology_cards: list[tuple[str, str]] = []  # [(pathology_id, side_id), ...]
        self._card_widgets: list[tuple[PathologyCard, str, str]] = []  # [(widget, pathology_id, side_id)]
        self._copy_step = 0  # 0=idle, 1=description copied, 2=done

    def get_name(self) -> str:
        return "Рентген"

    def get_description(self) -> str:
        return "Генерация структурированных описаний и заключений по рентгеновским снимкам"

    def _get_study(self):
        studies = self._config.get("исследования", [])
        for s in studies:
            if s.get("id") == self._current_study_id:
                return s
        return studies[0] if studies else None

    def _build_header(self) -> str:
        study = self._get_study()
        if not study:
            return ""
        tpl = study.get("шаблон_заголовка", "")
        return tpl.replace("{сокращение}", study.get("сокращение", ""))

    def _is_bilateral_template(self, text: str) -> bool:
        return text.strip().startswith("Справа и слева:")

    def _get_template_prefix(self, text: str) -> str | None:
        t = text.strip()
        if t.startswith("Слева:"):
            return "слева"
        if t.startswith("Справа:"):
            return "справа"
        if t.startswith("Справа и слева:"):
            return "bilateral"
        return None

    def _build_description(self) -> str:
        study = self._get_study()
        if not study:
            return ""
        structure = study.get("структура_описания", ["слева", "справа"])
        default_texts_raw = study.get("текст_по_умолчанию_описание")
        default_texts = default_texts_raw if isinstance(default_texts_raw, dict) else {}
        default_text_single = default_texts_raw if isinstance(default_texts_raw, str) else None
        pathology_by_id = {p["id"]: p for p in study.get("патологии", [])}

        left_parts: list[str] = []
        right_parts: list[str] = []
        bilateral_parts: list[str] = []

        for pathology_id, side_id in self._pathology_cards:
            pat = pathology_by_id.get(pathology_id)
            if not pat:
                continue
            templates = pat.get("шаблоны", {}).get("описание", {})
            text = templates.get(side_id, "")
            if not text:
                continue
            prefix = self._get_template_prefix(text)
            if prefix == "слева":
                left_parts.append(text)
            elif prefix == "справа":
                right_parts.append(text)
            elif prefix == "bilateral":
                bilateral_parts.append(text)

        # Один текст по умолчанию для «лёгкие норма» (без патологий)
        if default_text_single and not left_parts and not right_parts and not bilateral_parts:
            return default_text_single

        paragraphs: list[str] = []
        # При наличии двусторонних патологий не подставляем текст по умолчанию для «слева»/«справа»
        use_default_sides = not bilateral_parts
        for key in structure:
            if key == "слева":
                if left_parts:
                    paragraphs.append(" ".join(left_parts))
                elif use_default_sides:
                    paragraphs.append(default_texts.get("слева", "Слева: Без видимых очагово-инфильтративных теней. Корни структурны. Легочный рисунок не изменен. Синусы свободны. Сердце и диафрагма без особенностей."))
            elif key == "справа":
                if right_parts:
                    paragraphs.append(" ".join(right_parts))
                elif use_default_sides:
                    paragraphs.append(default_texts.get("справа", "Справа: Без видимых очагово-инфильтративных теней. Корни структурны. Легочный рисунок не изменен. Синусы свободны. Сердце и диафрагма без особенностей."))
        if bilateral_parts:
            paragraphs.append(" ".join(bilateral_parts))

        return "\n\n".join(paragraphs)

    def _build_conclusion(self) -> str:
        study = self._get_study()
        if not study:
            return ""
        pathology_by_id = {p["id"]: p for p in study.get("патологии", [])}
        parts = []
        for pathology_id, side_id in self._pathology_cards:
            pat = pathology_by_id.get(pathology_id)
            if not pat:
                continue
            templates = pat.get("шаблоны", {}).get("заключение", {})
            text = templates.get(side_id, "")
            if text:
                parts.append(text)
        if parts:
            return ". ".join(parts)
        default_conclusion = study.get("текст_по_умолчанию_заключение", "")
        return default_conclusion

    def _refresh_texts(self):
        if not hasattr(self, "_te_description") or not self._te_description:
            return
        header = self._build_header()
        desc = self._build_description()
        conc = self._build_conclusion()
        self._te_description.setPlainText(f"{header}\n\n{desc}" if header else desc)
        self._te_conclusion.setPlainText(conc)

    def _on_study_changed(self, index: int):
        studies = self._config.get("исследования", [])
        if 0 <= index < len(studies):
            self._current_study_id = studies[index]["id"]
            self._pathology_cards.clear()
            self._rebuild_cards()
        self._refresh_add_pathology_combo()
        self._refresh_texts()

    def _on_scheme_clicked(self):
        studies = self._config.get("исследования", [])
        if not studies:
            return
        idx = 0
        for i, s in enumerate(studies):
            if s.get("id") == self._current_study_id:
                idx = i
                break
        if hasattr(self, "_combo_study"):
            self._combo_study.setCurrentIndex(idx)

    def _add_pathology(self, pathology_id: str, side_id: str):
        study = self._get_study()
        if not study:
            return
        pathology_by_id = {p["id"]: p for p in study.get("патологии", [])}
        pat = pathology_by_id.get(pathology_id)
        if not pat:
            return
        sides = pat.get("стороны", [])
        first_side = sides[0]["id"] if sides else ""
        if not side_id:
            side_id = first_side
        self._pathology_cards.append((pathology_id, side_id))
        self._rebuild_cards()
        self._refresh_texts()

    def _remove_pathology_at(self, index: int):
        if 0 <= index < len(self._pathology_cards):
            self._pathology_cards.pop(index)
            self._rebuild_cards()
            self._refresh_texts()

    def _on_card_side_changed(self, index: int, new_side_id: str):
        if 0 <= index < len(self._pathology_cards):
            pid, _ = self._pathology_cards[index]
            self._pathology_cards[index] = (pid, new_side_id)
            self._refresh_texts()

    def _rebuild_cards(self):
        if not hasattr(self, "_cards_container") or not self._cards_container:
            return
        layout = self._cards_container.layout()
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._card_widgets.clear()
        study = self._get_study()
        if not study:
            return
        pathology_by_id = {p["id"]: p for p in study.get("патологии", [])}
        for i, (pathology_id, side_id) in enumerate(self._pathology_cards):
            pat = pathology_by_id.get(pathology_id)
            if not pat:
                continue
            card = PathologyCard(
                pat,
                side_id,
                on_delete=lambda idx=i: self._remove_pathology_at(idx),
                on_side_changed=lambda sid, idx=i: self._on_card_side_changed(idx, sid),
            )
            self._card_widgets.append((card, pathology_id, side_id))
            layout.addWidget(card)
        layout.addStretch()

    def _refresh_add_pathology_combo(self):
        if not hasattr(self, "_combo_add_pathology"):
            return
        self._combo_add_pathology.blockSignals(True)
        self._combo_add_pathology.clear()
        self._combo_add_pathology.addItem("— Добавить патологию —")
        study = self._get_study()
        if study:
            for p in study.get("патологии", []):
                self._combo_add_pathology.addItem(p.get("название", p.get("id", "")))
        self._combo_add_pathology.setCurrentIndex(0)
        self._combo_add_pathology.blockSignals(False)

    def _on_add_pathology_selected(self, index: int):
        if index <= 0:
            return
        study = self._get_study()
        if not study:
            return
        pathologies = study.get("патологии", [])
        idx = index - 1
        if idx < 0 or idx >= len(pathologies):
            return
        pat = pathologies[idx]
        sides = pat.get("стороны", [])
        first_side = sides[0]["id"] if sides else ""
        self._add_pathology(pat["id"], first_side)
        if hasattr(self, "_combo_add_pathology"):
            self._combo_add_pathology.setCurrentIndex(0)

    def _form_report(self):
        clipboard = QApplication.clipboard()
        if self._copy_step == 0:
            desc = self._build_description()
            header = self._build_header()
            text = f"{header}\n\n{desc}" if header else desc
            clipboard.setText(text)
            self._copy_step = 1
            self._btn_form_report.setText("ОПИСАНИЕ СКОПИРОВАНО")
            self._btn_form_report.setToolTip(
                "Вставьте описание в целевую программу. После вставки нажмите кнопку еще раз для копирования ЗАКЛЮЧЕНИЯ."
            )
        else:
            conc = self._build_conclusion()
            clipboard.setText(conc)
            self._copy_step = 0
            self._btn_form_report.setText("СФОРМИРОВАТЬ ОТЧЕТ")
            self._btn_form_report.setToolTip("")

    def _save_preset(self):
        name, ok = QInputDialog.getText(
            self._right_widget,
            "Сохранить пресет",
            "Название пресета:",
        )
        if not ok or not name.strip():
            return
        preset = {
            "название": name.strip(),
            "исследование_id": self._current_study_id or "",
            "патологии": [{"pathology_id": p, "side_id": s} for p, s in self._pathology_cards],
        }
        self._presets.append(preset)
        if _save_json(self._presets_path, self._presets):
            self._refresh_presets_combo()
            QMessageBox.information(self._right_widget, "Пресет", "Пресет сохранён.")
        else:
            QMessageBox.warning(self._right_widget, "Ошибка", "Не удалось сохранить пресеты.")

    def _load_preset(self, index: int):
        if index < 0 or index >= len(self._presets):
            return
        preset = self._presets[index]
        study_id = preset.get("исследование_id", "")
        studies = self._config.get("исследования", [])
        idx = 0
        for i, s in enumerate(studies):
            if s.get("id") == study_id:
                idx = i
                break
        self._current_study_id = study_id
        self._pathology_cards = [
            (p.get("pathology_id", ""), p.get("side_id", ""))
            for p in preset.get("патологии", [])
        ]
        if hasattr(self, "_combo_study"):
            self._combo_study.blockSignals(True)
            self._combo_study.setCurrentIndex(idx)
            self._combo_study.blockSignals(False)
        self._rebuild_cards()
        self._refresh_texts()

    def _delete_preset(self):
        idx = self._combo_presets.currentIndex()
        if idx < 0 or idx >= len(self._presets):
            return
        self._presets.pop(idx)
        _save_json(self._presets_path, self._presets)
        self._refresh_presets_combo()

    def _refresh_presets_combo(self):
        if not hasattr(self, "_combo_presets"):
            return
        self._combo_presets.blockSignals(True)
        self._combo_presets.clear()
        for p in self._presets:
            self._combo_presets.addItem(p.get("название", ""))
        self._combo_presets.blockSignals(False)

    def _import_config(self):
        path, _ = QFileDialog.getOpenFileName(
            self._right_widget,
            "Импорт конфигурации",
            "",
            "JSON (*.json)",
        )
        if not path:
            return
        data = _load_json(Path(path), None)
        if data is None or "исследования" not in data:
            QMessageBox.warning(self._right_widget, "Ошибка", "Некорректный файл конфигурации.")
            return
        self._config = data
        self._config_path = Path(path)
        studies = self._config.get("исследования", [])
        self._combo_study.clear()
        for s in studies:
            self._combo_study.addItem(s.get("название", s.get("id", "")))
        if studies:
            self._current_study_id = studies[0]["id"]
            self._combo_study.setCurrentIndex(0)
        self._pathology_cards.clear()
        self._rebuild_cards()
        self._refresh_texts()
        QMessageBox.information(self._right_widget, "Импорт", "Конфигурация загружена.")

    def _export_presets(self):
        path, _ = QFileDialog.getSaveFileName(
            self._right_widget,
            "Экспорт пресетов",
            "presets.json",
            "JSON (*.json)",
        )
        if not path:
            return
        if _save_json(Path(path), self._presets):
            QMessageBox.information(self._right_widget, "Экспорт", "Пресеты экспортированы.")
        else:
            QMessageBox.warning(self._right_widget, "Ошибка", "Не удалось сохранить файл.")

    def create_widget(self) -> QWidget:
        root = QWidget()
        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(8, 8, 8, 8)

        studies = self._config.get("исследования", [])
        if studies and not self._current_study_id:
            self._current_study_id = studies[0]["id"]

        # ---- Левая панель: результат ----
        left = QFrame()
        left.setFrameStyle(QFrame.StyledPanel)
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("ОПИСАНИЕ"))
        self._te_description = QTextEdit()
        self._te_description.setReadOnly(True)
        self._te_description.setMinimumHeight(180)
        left_layout.addWidget(self._te_description)
        left_layout.addWidget(QLabel("ЗАКЛЮЧЕНИЕ"))
        self._te_conclusion = QTextEdit()
        self._te_conclusion.setReadOnly(True)
        self._te_conclusion.setMinimumHeight(120)
        left_layout.addWidget(self._te_conclusion)
        main_layout.addWidget(left, 1)

        # ---- Центральная панель: конструктор ----
        self._center_widget = QWidget()
        center_layout = QVBoxLayout(self._center_widget)
        svg_path = PLUGIN_DIR / "body_scheme.svg"
        if svg_path.exists() and QSvgWidget is not None:
            svg = QSvgWidget(str(svg_path))
            svg.setFixedSize(120, 200)
            svg.setCursor(Qt.PointingHandCursor)
            svg.mousePressEvent = lambda e: self._on_scheme_clicked()
            center_layout.addWidget(svg, alignment=Qt.AlignCenter)
        else:
            scheme_label = QLabel("Схема (ОГК)")
            scheme_label.setAlignment(Qt.AlignCenter)
            scheme_label.setFixedSize(120, 200)
            scheme_label.setStyleSheet("border: 1px solid #ccc; background: #f5f5f5;")
            scheme_label.setCursor(Qt.PointingHandCursor)
            scheme_label.mousePressEvent = lambda e: self._on_scheme_clicked()
            center_layout.addWidget(scheme_label, alignment=Qt.AlignCenter)
        self._combo_study = QComboBox()
        for s in studies:
            self._combo_study.addItem(s.get("название", s.get("id", "")))
        self._combo_study.currentIndexChanged.connect(self._on_study_changed)
        center_layout.addWidget(QLabel("ИССЛЕДОВАНИЕ"))
        center_layout.addWidget(self._combo_study)
        center_layout.addWidget(QLabel("ДОБАВИТЬ ПАТОЛОГИЮ"))
        self._combo_add_pathology = QComboBox()
        self._refresh_add_pathology_combo()
        self._combo_add_pathology.currentIndexChanged.connect(self._on_add_pathology_selected)
        center_layout.addWidget(self._combo_add_pathology)
        center_layout.addWidget(QLabel("Патологии:"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._cards_container = QWidget()
        self._cards_container.setLayout(QVBoxLayout())
        scroll.setWidget(self._cards_container)
        center_layout.addWidget(scroll, 1)
        main_layout.addWidget(self._center_widget, 1)

        # ---- Правая панель: управление ----
        self._right_widget = QWidget()
        right_layout = QVBoxLayout(self._right_widget)
        self._btn_form_report = QPushButton("СФОРМИРОВАТЬ ОТЧЕТ")
        self._btn_form_report.setMinimumHeight(44)
        self._btn_form_report.clicked.connect(self._form_report)
        right_layout.addWidget(self._btn_form_report)
        right_layout.addWidget(QLabel("ПРЕСЕТЫ"))
        self._combo_presets = QComboBox()
        self._refresh_presets_combo()
        self._combo_presets.currentIndexChanged.connect(self._load_preset)
        right_layout.addWidget(self._combo_presets)
        row = QHBoxLayout()
        btn_save_preset = QPushButton("Сохранить текущий")
        btn_save_preset.clicked.connect(self._save_preset)
        row.addWidget(btn_save_preset)
        btn_del_preset = QPushButton("Удалить выбранный")
        btn_del_preset.clicked.connect(self._delete_preset)
        row.addWidget(btn_del_preset)
        right_layout.addLayout(row)
        btn_import = QPushButton("ИМПОРТ КОНФИГУРАЦИИ")
        btn_import.clicked.connect(self._import_config)
        right_layout.addWidget(btn_import)
        btn_export = QPushButton("ЭКСПОРТ КОНФИГУРАЦИИ")
        btn_export.clicked.connect(self._export_presets)
        right_layout.addWidget(btn_export)
        right_layout.addStretch()
        main_layout.addWidget(self._right_widget, 0)

        self._on_study_changed(self._combo_study.currentIndex())
        self._refresh_texts()
        return root


Plugin = XrayConstructorPlugin
