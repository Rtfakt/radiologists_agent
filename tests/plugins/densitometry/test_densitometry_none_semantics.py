"""Тесты для семантики None в значениях полей денситометрии."""

import sys
from pathlib import Path
import unittest

from PySide6.QtWidgets import QApplication

# Корень проекта в path для импорта plugins
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def get_app():
    """Возвращает экземпляр QApplication (создаёт при необходимости)."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestDensitometryNoneSemantics(unittest.TestCase):
    """Проверки семантики None для value() и валидации."""

    @classmethod
    def setUpClass(cls):
        get_app()

    def setUp(self):
        from plugins.densitometry.plugin import DensitometryPlugin
        self.plugin = DensitometryPlugin()
        self.widget = self.plugin.create_widget()

    def test_tz_value_none_when_empty(self):
        self.plugin.spine_t_score.setText("")
        self.assertIsNone(self.plugin.spine_t_score.value())

    def test_tz_value_zero_is_valid(self):
        self.plugin.spine_t_score.setText("0.0")
        self.assertEqual(self.plugin.spine_t_score.value(), 0.0)

    def test_density_value_none_when_empty(self):
        self.plugin.spine_bmd.setText("")
        self.assertIsNone(self.plugin.spine_bmd.value())

    def test_density_value_zero_is_valid(self):
        self.plugin.spine_bmd.setText("0.000")
        self.assertEqual(self.plugin.spine_bmd.value(), 0.0)

    def test_frax_value_none_when_empty(self):
        self.plugin.femur_frax.setText("")
        self.assertIsNone(self.plugin.femur_frax.value())

    def test_frax_value_zero_is_valid(self):
        self.plugin.femur_frax.setText("0")
        self.assertEqual(self.plugin.femur_frax.value(), 0.0)

    def test_validate_spine_allows_zero_values(self):
        self.plugin.spine_bmd.setText("0.000")
        self.plugin.spine_t_score.setText("0.0")
        self.plugin.spine_z_score.setText("")
        self.assertIsNone(self.plugin._validate_spine())

    def test_validate_spine_requires_any_criterion(self):
        self.plugin.spine_bmd.setText("1.000")
        self.plugin.spine_t_score.setText("")
        self.plugin.spine_z_score.setText("")
        self.assertIsNotNone(self.plugin._validate_spine())

    def test_validate_femur_allows_zero_values(self):
        self.plugin.femur_bmd.setText("0.000")
        self.plugin.femur_t_score.setText("0.0")
        self.plugin.femur_z_score.setText("")
        self.plugin.femur_frax.setText("0")
        self.plugin.total_hip_bmd.setText("0.000")
        self.plugin.total_hip_t_score.setText("0.0")
        self.plugin.total_hip_z_score.setText("")
        self.assertIsNone(self.plugin._validate_femur())

    def test_validate_femur_requires_frax(self):
        self.plugin.femur_bmd.setText("1.000")
        self.plugin.femur_t_score.setText("0.0")
        self.plugin.femur_z_score.setText("")
        self.plugin.femur_frax.setText("")
        self.plugin.total_hip_bmd.setText("1.000")
        self.plugin.total_hip_t_score.setText("0.0")
        self.plugin.total_hip_z_score.setText("")
        self.assertIsNotNone(self.plugin._validate_femur())


if __name__ == "__main__":
    unittest.main()
