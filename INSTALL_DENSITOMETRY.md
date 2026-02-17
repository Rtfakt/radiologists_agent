# Установочный файл только для плагина «Денситометрия»

Чтобы собрать версию приложения **только с плагином Денситометрия** и установить её на любой компьютер, используйте один из способов ниже.

---

## Способ 1: Архив (ZIP) — установка на компьютер с Python

Подходит, если на целевом компьютере можно установить Python.

### Шаг 1: Собрать дистрибутив на своей машине

В корне проекта выполните:

```bash
python build_densitometry_only.py
```

Будет создана папка **`dist_densitometry`** с приложением и только плагином «Денситометрия».

### Шаг 2: Упаковать в ZIP

- Заархивируйте папку `dist_densitometry` в один ZIP-файл, например:  
  `radiologists_densitometry.zip`

### Шаг 3: Установка на любом компьютере

1. Скачайте и установите **Python 3.10 или 3.11** с [python.org](https://www.python.org/downloads/).
2. Распакуйте `radiologists_densitometry.zip` в любую папку.
3. Откройте терминал (командную строку) **в этой папке**.
4. Выполните:

   **Windows:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```

   **macOS / Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python main.py
   ```

После этого приложение будет запускаться командой **`python main.py`** (с активированным venv).

---

## Способ 2: Один исполняемый файл (PyInstaller) — без установки Python

Подходит, когда на целевом компьютере **не должен** стоять Python — нужен один .exe (Windows) или приложение (macOS).

### Шаг 1: Установить PyInstaller

```bash
pip install pyinstaller
```

### Шаг 2: Собрать дистрибутив только с денситометрией

Сначала создайте папку с приложением «только денситометрия»:

```bash
python build_densitometry_only.py
```

### Шаг 3: Собрать исполняемый файл из папки dist_densitometry

Перейдите в собранную папку и запустите PyInstaller (папку `plugins` нужно передать в сборку, иначе плагин не найдётся):

**macOS / Linux:**
```bash
cd dist_densitometry
pyinstaller --name "Денситометрия" --windowed --onefile --add-data "plugins:plugins" main.py
```

**Windows** (в `--add-data` используется `;` вместо `:`):
```cmd
cd dist_densitometry
pyinstaller --name "Денситометрия" --windowed --onefile --add-data "plugins;plugins" main.py
```

Опции:
- `--windowed` — без консоли (только окно приложения).
- `--onefile` — один файл .exe / приложение.

Исполняемый файл появится в `dist_densitometry/dist/`:
- **Windows:** `Денситометрия.exe`
- **macOS:** приложение `Денситометрия.app`

### Шаг 4: Установка на любом компьютере

- **Windows:** скопируйте `Денситометрия.exe` на компьютер и запустите.
- **macOS:** скопируйте `Денситометрия.app` в папку «Программы» (или любую другую) и запустите.

Python на целевом компьютере не нужен.

---

## Что входит в дистрибутив «только Денситометрия»

- Ядро приложения: `main.py`, `core/`, `ui/`, `adapters/`, `domain/`, `ports/`
- Только плагин: **`plugins/densitometry/`** (плагины «Рентген» и «Маммография» не включаются)
- Файл зависимостей: `requirements.txt` (PySide6, pynput)

Внутри архива или папки также есть **`КАК_УСТАНОВИТЬ.txt`** с краткой инструкцией для пользователя.
