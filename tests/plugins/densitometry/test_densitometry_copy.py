"""Unit-тесты для методов копирования описания/заключения позвоночника и бедра в плагине денситометрии."""

import sys
from pathlib import Path

# Корень проекта в path для импорта plugins
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
import unittest


def get_app():
    """Возвращает экземпляр QApplication (создаёт при необходимости)."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestDensitometryCopyMethods(unittest.TestCase):
    """Тесты для _copy_spine_description, _copy_spine_conclusion, _copy_femur_description, _copy_femur_conclusion."""

    @classmethod
    def setUpClass(cls):
        get_app()

    def setUp(self):
        from plugins.densitometry.plugin import DensitometryPlugin
        self.plugin = DensitometryPlugin()
        self.widget = self.plugin.create_widget()

    # --- _copy_spine_description ---

    def test_copy_spine_description_empty_field(self):
        """Пустое текстовое поле позвоночника → показывается ошибка, в буфер ничего не копируется."""
        self.plugin.spine_text_edit.setPlainText("")
        self.plugin._copy_spine_description()
        self.assertEqual(
            self.plugin.spine_copy_desc_btn.toolTip(),
            "Текстовое поле позвоночника пустое",
        )

    def test_copy_spine_description_only_description(self):
        """Текст без маркера «Заключение» → в буфер копируется весь текст как описание."""
        text = "Только описание без заключения."
        self.plugin.spine_text_edit.setPlainText(text)
        self.plugin._copy_spine_description()
        self.assertEqual(QApplication.clipboard().text(), text)

    def test_copy_spine_description_full_text(self):
        """Полный текст с маркером «Заключение.» → в буфер копируется только описание."""
        description = "Описание позвоночника."
        conclusion = "Заключение. Позвоночник - Норма"
        full = f"{description}\n\n{conclusion}"
        self.plugin.spine_text_edit.setPlainText(full)
        self.plugin._copy_spine_description()
        self.assertEqual(QApplication.clipboard().text(), description)

    # --- _copy_spine_conclusion ---

    def test_copy_spine_conclusion_empty_field(self):
        """Пустое поле позвоночника → при копировании заключения показывается ошибка."""
        self.plugin.spine_text_edit.setPlainText("")
        self.plugin._copy_spine_conclusion()
        self.assertEqual(
            self.plugin.spine_copy_conc_btn.toolTip(),
            "Текстовое поле позвоночника пустое",
        )

    def test_copy_spine_conclusion_only_description(self):
        """Текст без маркера «Заключение» → заключение пустое, в буфер копируется пустая строка."""
        text = "Только описание."
        self.plugin.spine_text_edit.setPlainText(text)
        self.plugin._copy_spine_conclusion()
        self.assertEqual(QApplication.clipboard().text(), "")

    def test_copy_spine_conclusion_full_text(self):
        """Полный текст с «Заключение.» → в буфер копируется только заключение."""
        description = "Описание."
        conclusion = "Заключение. Позвоночник - Норма"
        full = f"{description}\n\n{conclusion}"
        self.plugin.spine_text_edit.setPlainText(full)
        self.plugin._copy_spine_conclusion()
        self.assertEqual(QApplication.clipboard().text(), conclusion)

    # --- _copy_femur_description ---

    def test_copy_femur_description_empty_field(self):
        """Пустое поле бедра → при копировании описания показывается ошибка."""
        self.plugin.femur_text_edit.setPlainText("")
        self.plugin._copy_femur_description()
        self.assertEqual(
            self.plugin.femur_copy_desc_btn.toolTip(),
            "Текстовое поле бедра пустое",
        )

    def test_copy_femur_description_only_description(self):
        """Текст без маркера «Заключение» → в буфер копируется весь текст как описание."""
        text = "Описание бедра без заключения."
        self.plugin.femur_text_edit.setPlainText(text)
        self.plugin._copy_femur_description()
        self.assertEqual(QApplication.clipboard().text(), text)

    def test_copy_femur_description_full_text(self):
        """Полный текст с «Заключение:» → в буфер копируется только описание."""
        description = "Описание бедра."
        conclusion = "Заключение: Проксимальный отдел бедра."
        full = f"{description}\n\n{conclusion}"
        self.plugin.femur_text_edit.setPlainText(full)
        self.plugin._copy_femur_description()
        self.assertEqual(QApplication.clipboard().text(), description)

    # --- _copy_femur_conclusion ---

    def test_copy_femur_conclusion_empty_field(self):
        """Пустое поле бедра → при копировании заключения показывается ошибка."""
        self.plugin.femur_text_edit.setPlainText("")
        self.plugin._copy_femur_conclusion()
        self.assertEqual(
            self.plugin.femur_copy_conc_btn.toolTip(),
            "Текстовое поле бедра пустое",
        )

    def test_copy_femur_conclusion_only_description(self):
        """Текст без маркера «Заключение» → заключение пустое."""
        text = "Только описание бедра."
        self.plugin.femur_text_edit.setPlainText(text)
        self.plugin._copy_femur_conclusion()
        self.assertEqual(QApplication.clipboard().text(), "")

    def test_copy_femur_conclusion_full_text(self):
        """Полный текст с «Заключение:» → в буфер копируется только заключение."""
        description = "Описание."
        conclusion = "Заключение: Проксимальный отдел бедра в целом: Норма."
        full = f"{description}\n\n{conclusion}"
        self.plugin.femur_text_edit.setPlainText(full)
        self.plugin._copy_femur_conclusion()
        self.assertEqual(QApplication.clipboard().text(), conclusion)


if __name__ == "__main__":
    unittest.main()
