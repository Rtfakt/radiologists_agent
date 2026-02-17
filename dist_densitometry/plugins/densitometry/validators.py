"""Валидаторы для полей ввода денситометрии с автоформатированием и строгой проверкой формата."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QValidator, QKeyEvent
from PySide6.QtWidgets import QLineEdit, QToolTip, QApplication
from PySide6.QtCore import QPoint
import re

# Допустимые диапазоны (для подсказки при вставке)
TZ_MIN, TZ_MAX = -5.0, 5.0
DENSITY_MAX = 2.0


# --- Подсказки для пользователя ---
TZ_HINT_VALID = "Формат: X.Y или -X.Y (одна цифра до точки, одна после)"
TZ_HINT_TOO_MANY = "Введите две цифры в формате X.Y (например 1.5 или -1.2)"
DENSITY_HINT_VALID = "Формат: X.YYY (одна цифра до точки, три после)"
DENSITY_HINT_TOO_MANY = "Плотность должна быть в формате X.YYY (максимум 4 цифры)"
FRAX_HINT = "FRAX должен быть целым числом от 0 до 100"


def _show_tooltip_at_widget(widget: QLineEdit, message: str):
    """Показывает подсказку рядом с виджетом."""
    QToolTip.showText(
        widget.mapToGlobal(QPoint(0, widget.height() + 2)),
        message,
        widget,
        msecShowTime=3000,
    )


# ---------------------------------------------------------------------------
# T/Z критерий: X.Y или -X.Y (строго одна цифра до точки, одна после)
# ---------------------------------------------------------------------------

class TZCriteriaValidator(QValidator):
    """Валидатор для T- и Z-критериев. Формат: X.Y или -X.Y."""

    def validate(self, text: str, pos: int) -> tuple[QValidator.State, str, int]:
        if not text:
            return (QValidator.State.Intermediate, text, pos)
        # Допустимы только цифры, точка и минус в начале
        if not re.match(r"^-?[0-9]*\.?[0-9]*$", text):
            return (QValidator.State.Invalid, text, pos)
        if text == "-":
            return (QValidator.State.Intermediate, text, pos)
        # Один минус и одна цифра
        if re.match(r"^-?[0-9]$", text):
            return (QValidator.State.Intermediate, text, pos)
        # Один минус, одна цифра, точка и ровно одна цифра после — допустимо (X.Y или -X.Y)
        if re.match(r"^-?[0-9]\.[0-9]$", text):
            return (QValidator.State.Acceptable, text, pos)
        # Одна цифра и точка без цифры после — промежуточное
        if re.match(r"^-?[0-9]\.$", text):
            return (QValidator.State.Intermediate, text, pos)
        # Две цифры без точки — недопустимо (должно быть 1.2)
        if re.match(r"^-?[0-9]{2}$", text):
            return (QValidator.State.Invalid, text, pos)
        # Больше одной цифры после точки
        if re.match(r"^-?[0-9]\.[0-9]{2,}$", text):
            return (QValidator.State.Invalid, text, pos)
        return (QValidator.State.Invalid, text, pos)

    @staticmethod
    def format_tooltip():
        return TZ_HINT_TOO_MANY


def _parse_and_format_tz_paste(s: str) -> tuple[str | None, str]:
    """Пытается разобрать вставку для T/Z. Возвращает (отформатированную строку или None, сообщение об ошибке)."""
    s = s.strip().replace(",", ".")
    if not s:
        return "", ""
    try:
        v = float(s)
        if v < TZ_MIN or v > TZ_MAX:
            return None, f"Допустимый диапазон T/Z: от {TZ_MIN} до {TZ_MAX}"
        return f"{v:.1f}", ""
    except ValueError:
        return None, TZ_HINT_TOO_MANY


def _parse_and_format_density_paste(s: str) -> tuple[str | None, str]:
    """Пытается разобрать вставку для плотности. Возвращает (отформатированную строку или None, сообщение)."""
    s = s.strip().replace(",", ".")
    if not s:
        return "", ""
    try:
        v = float(s)
        if v < 0 or v > DENSITY_MAX:
            return None, f"Плотность должна быть от 0 до {DENSITY_MAX}"
        return f"{v:.3f}", ""
    except ValueError:
        return None, DENSITY_HINT_TOO_MANY


def _parse_and_format_frax_paste(s: str) -> tuple[str | None, str]:
    """Пытается разобрать вставку для FRAX. Возвращает (строку или None, сообщение)."""
    s = s.strip()
    if not s:
        return "", ""
    try:
        v = int(s)
        if 0 <= v <= 100:
            return str(v), ""
        return None, FRAX_HINT
    except ValueError:
        return None, FRAX_HINT


class TZCriteriaLineEdit(QLineEdit):
    """Поле ввода T/Z с авто-вставкой точки при вводе второй цифры и валидацией."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setValidator(TZCriteriaValidator(self))
        self.setPlaceholderText("0.0 или -1.5")
        self.setToolTip(TZ_HINT_VALID)
        self.setMaxLength(5)  # -X.Y

    def insertFromMimeData(self, source):
        if source.hasText():
            pasted = source.text().strip()
            formatted, err = _parse_and_format_tz_paste(pasted)
            if formatted is not None:
                self.setText(formatted)
                return
            _show_tooltip_at_widget(self, err or TZ_HINT_TOO_MANY)
        super().insertFromMimeData(source)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        text = self.text()
        cursor = self.cursorPosition()
        # Цифра 0-9
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            digit = chr(key)
            # Одна цифра (или минус + одна цифра) без точки — авто-добавляем точку и цифру
            if re.match(r"^-?[0-9]$", text):
                new_text = text + "." + digit
                self.setText(new_text)
                self.setCursorPosition(len(new_text))
                return
            # Уже есть точка и одна цифра после — блокируем третью цифру
            if re.match(r"^-?[0-9]\.[0-9]$", text):
                _show_tooltip_at_widget(self, TZ_HINT_TOO_MANY)
                return
        # Ручной ввод точки разрешён в допустимых местах — обрабатывает валидатор
        super().keyPressEvent(event)

    def value(self) -> float | None:
        """Возвращает числовое значение или None при пустом/некорректном вводе."""
        t = self.text().strip().replace(",", ".")
        if not t or t == "-":
            return None
        try:
            return float(t)
        except ValueError:
            return None

    def setValue(self, val: float):
        if val == 0.0:
            self.setText("")
        else:
            self.setText(f"{val:.1f}")


# ---------------------------------------------------------------------------
# Плотность: X.YYY (строго 1 цифра до точки, 3 после)
# ---------------------------------------------------------------------------

class DensityValidator(QValidator):
    """Валидатор для плотности (BMD). Формат: X.YYY."""

    def validate(self, text: str, pos: int) -> tuple[QValidator.State, str, int]:
        if not text:
            return (QValidator.State.Intermediate, text, pos)
        if not re.match(r"^[0-9]*\.?[0-9]*$", text):
            return (QValidator.State.Invalid, text, pos)
        # Одна цифра
        if re.match(r"^[0-9]$", text):
            return (QValidator.State.Intermediate, text, pos)
        # Одна цифра и точка
        if re.match(r"^[0-9]\.$", text):
            return (QValidator.State.Intermediate, text, pos)
        # X.Y, X.YY
        if re.match(r"^[0-9]\.[0-9]{1,2}$", text):
            return (QValidator.State.Intermediate, text, pos)
        # X.YYY — допустимо
        if re.match(r"^[0-9]\.[0-9]{3}$", text):
            return (QValidator.State.Acceptable, text, pos)
        # Больше 3 цифр после точки
        if re.match(r"^[0-9]\.[0-9]{4,}$", text):
            return (QValidator.State.Invalid, text, pos)
        # Две цифры до точки
        if re.match(r"^[0-9]{2,}\.?", text):
            return (QValidator.State.Invalid, text, pos)
        return (QValidator.State.Invalid, text, pos)

    @staticmethod
    def format_tooltip():
        return DENSITY_HINT_TOO_MANY


class DensityLineEdit(QLineEdit):
    """Поле ввода плотности с авто-точкой после первой цифры и форматом X.YYY."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setValidator(DensityValidator(self))
        self.setPlaceholderText("0.000 или 1.234")
        self.setToolTip(DENSITY_HINT_VALID)
        self.setMaxLength(5)  # X.YYY

    def insertFromMimeData(self, source):
        if source.hasText():
            pasted = source.text().strip()
            formatted, err = _parse_and_format_density_paste(pasted)
            if formatted is not None:
                self.setText(formatted)
                return
            _show_tooltip_at_widget(self, err or DENSITY_HINT_TOO_MANY)
        super().insertFromMimeData(source)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        text = self.text()
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            digit = chr(key)
            # Пусто — вводим первую цифру и сразу ставим точку
            if not text:
                self.setText(digit + ".")
                self.setCursorPosition(len(digit) + 1)
                return
            # Одна цифра без точки (не должно быть при нашем авто-формате, но на случай вставки)
            if re.match(r"^[0-9]$", text):
                self.setText(text + "." + digit)
                self.setCursorPosition(len(text) + 1 + len(digit))
                return
            # Уже X.YYY — блокируем пятую цифру
            if re.match(r"^[0-9]\.[0-9]{3}$", text):
                _show_tooltip_at_widget(self, DENSITY_HINT_TOO_MANY)
                return
        super().keyPressEvent(event)

    def value(self) -> float | None:
        """Возвращает числовое значение или None при пустом/некорректном вводе."""
        t = self.text().strip().replace(",", ".")
        if not t or t == ".":
            return None
        try:
            return float(t)
        except ValueError:
            return None

    def setValue(self, val: float):
        if val == 0.0:
            self.setText("")
        else:
            self.setText(f"{val:.3f}")


# ---------------------------------------------------------------------------
# FRAX: целое 0–100
# ---------------------------------------------------------------------------

class FRAXValidator(QValidator):
    """Валидатор для FRAX. Целое число от 0 до 100."""

    def validate(self, text: str, pos: int) -> tuple[QValidator.State, str, int]:
        if not text:
            return (QValidator.State.Intermediate, text, pos)
        if not text.isdigit():
            return (QValidator.State.Invalid, text, pos)
        num = int(text)
        if 0 <= num <= 100:
            return (QValidator.State.Acceptable, text, pos)
        return (QValidator.State.Invalid, text, pos)

    @staticmethod
    def format_tooltip():
        return FRAX_HINT


class FRAXLineEdit(QLineEdit):
    """Поле ввода FRAX (целое 0–100)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setValidator(FRAXValidator(self))
        self.setPlaceholderText("0–100")
        self.setToolTip(FRAX_HINT)
        self.setMaxLength(3)

    def insertFromMimeData(self, source):
        if source.hasText():
            pasted = source.text().strip()
            formatted, err = _parse_and_format_frax_paste(pasted)
            if formatted is not None:
                self.setText(formatted)
                return
            _show_tooltip_at_widget(self, err or FRAX_HINT)
        super().insertFromMimeData(source)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        text = self.text()
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            # Проверяем, не выйдем ли за 100
            new_val = (text + chr(key)).lstrip("0") or "0"
            try:
                if int(new_val) > 100:
                    _show_tooltip_at_widget(self, FRAX_HINT)
                    return
            except ValueError:
                pass
        super().keyPressEvent(event)

    def value(self) -> float | None:
        """Возвращает значение от 0 до 100 или None при пустом/некорректном вводе."""
        t = self.text().strip()
        if not t:
            return None
        try:
            v = int(t)
            return float(max(0, min(100, v)))
        except ValueError:
            return None

    def setValue(self, val: int):
        self.setText(str(max(0, min(100, int(val)))))
