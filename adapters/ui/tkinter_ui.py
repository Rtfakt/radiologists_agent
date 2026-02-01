"""Tkinter UI адаптер"""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Callable, Optional
from ports.ui_port import UIAdapter
from domain.entities import Modality, Report


class TkinterUI(UIAdapter):
    """Реализация UI через Tkinter"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Конструктор рентгеновских заключений")
        self.root.geometry("900x700")
        
        self.process_callback: Optional[Callable[[], None]] = None
        self.template_callback: Optional[Callable[[str], None]] = None
        self.modality_callback: Optional[Callable[[Modality], None]] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        # Верхняя панель: выбор модальности
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Label(top_frame, text="Модальность:").pack(side=tk.LEFT, padx=(0, 5))
        self.modality_var = tk.StringVar(value=Modality.XRAY.value)
        self.modality_combo = ttk.Combobox(
            top_frame,
            textvariable=self.modality_var,
            state="readonly",
            width=20,
            values=[m.value for m in Modality],
        )
        self.modality_combo.pack(side=tk.LEFT, padx=5)
        self.modality_combo.bind("<<ComboboxSelected>>", self._on_modality_selected)

        # Панель модальности: разные кнопки/поля
        self.modality_panel = ttk.LabelFrame(self.root, text="Панель модальности", padding=10)
        self.modality_panel.pack(fill=tk.X, padx=10, pady=5)
        self._rebuild_modality_panel(Modality.XRAY)

        # Фрейм для исходного текста
        original_frame = ttk.LabelFrame(self.root, text="Исходный текст", padding=10)
        original_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.original_text = scrolledtext.ScrolledText(
            original_frame, 
            height=10, 
            wrap=tk.WORD,
            font=("Arial", 11)
        )
        self.original_text.pack(fill=tk.BOTH, expand=True)
        
        # Фрейм для кнопок
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.process_button = ttk.Button(
            button_frame, 
            text="Обработать текст", 
            command=self._on_process_clicked
        )
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        # Выбор шаблона
        ttk.Label(button_frame, text="Шаблон:").pack(side=tk.LEFT, padx=5)
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(
            button_frame, 
            textvariable=self.template_var,
            state="readonly",
            width=20
        )
        self.template_combo.pack(side=tk.LEFT, padx=5)
        self.template_combo.bind("<<ComboboxSelected>>", self._on_template_selected)
        
        # Фрейм для обработанного текста
        processed_frame = ttk.LabelFrame(self.root, text="Обработанный текст", padding=10)
        processed_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.processed_text = scrolledtext.ScrolledText(
            processed_frame, 
            height=10, 
            wrap=tk.WORD,
            font=("Arial", 11),
            state=tk.DISABLED
        )
        self.processed_text.pack(fill=tk.BOTH, expand=True)

    def _clear_frame(self, frame: ttk.Frame):
        for child in frame.winfo_children():
            child.destroy()

    def _rebuild_modality_panel(self, modality: Modality):
        self._clear_frame(self.modality_panel)
        self.modality_panel.configure(text=f"Панель модальности: {modality.value}")

        if modality == Modality.MAMMOGRAPHY:
            ttk.Label(self.modality_panel, text="Плотность (ACR):").pack(side=tk.LEFT, padx=(0, 5))
            self.acr_var = tk.StringVar(value="B")
            acr_combo = ttk.Combobox(
                self.modality_panel,
                textvariable=self.acr_var,
                state="readonly",
                width=5,
                values=["A", "B", "C", "D"],
            )
            acr_combo.pack(side=tk.LEFT, padx=5)

            def insert_birads_1():
                text = self.original_text.get(1.0, tk.END).strip()
                suffix = f"\n\nBI-RADS: 1. Плотность (ACR): {self.acr_var.get()}."
                self.original_text.delete(1.0, tk.END)
                self.original_text.insert(1.0, (text + suffix).strip())

            ttk.Button(self.modality_panel, text="Вставить BI-RADS 1", command=insert_birads_1).pack(
                side=tk.LEFT, padx=10
            )

        elif modality == Modality.DENSITOMETRY:
            ttk.Label(self.modality_panel, text="T-score:").pack(side=tk.LEFT, padx=(0, 5))
            self.tscore_var = tk.StringVar(value="-1.0")
            ttk.Entry(self.modality_panel, textvariable=self.tscore_var, width=8).pack(side=tk.LEFT, padx=5)

            ttk.Label(self.modality_panel, text="Z-score:").pack(side=tk.LEFT, padx=(10, 5))
            self.zscore_var = tk.StringVar(value="-0.5")
            ttk.Entry(self.modality_panel, textvariable=self.zscore_var, width=8).pack(side=tk.LEFT, padx=5)

            def build_dxa_text():
                try:
                    t = float(self.tscore_var.get())
                except ValueError:
                    t = None
                diagnosis = "Н/Д"
                if t is not None:
                    if t <= -2.5:
                        diagnosis = "Остеопороз"
                    elif -2.5 < t < -1.0:
                        diagnosis = "Остеопения"
                    else:
                        diagnosis = "Норма"

                text = (
                    "Денситометрия (DXA).\n"
                    f"T-score: {self.tscore_var.get()}, Z-score: {self.zscore_var.get()}.\n"
                    f"Заключение: {diagnosis}."
                )
                self.original_text.delete(1.0, tk.END)
                self.original_text.insert(1.0, text)

            ttk.Button(self.modality_panel, text="Сформировать DXA текст", command=build_dxa_text).pack(
                side=tk.LEFT, padx=10
            )

        else:
            ttk.Label(self.modality_panel, text="XRAY: используйте шаблоны и кнопку обработки текста.").pack(
                side=tk.LEFT
            )
    
    def _on_process_clicked(self):
        """Обработчик нажатия кнопки"""
        if self.process_callback:
            self.process_callback()
    
    def _on_template_selected(self, event=None):
        """Обработчик выбора шаблона"""
        if self.template_callback:
            template_name = self.template_var.get()
            if template_name:
                self.template_callback(template_name)

    def _on_modality_selected(self, event=None):
        raw = self.modality_var.get()
        modality = Modality(raw)
        self._rebuild_modality_panel(modality)
        if self.modality_callback:
            self.modality_callback(modality)
    
    def show_report(self, report: Report):
        """Показать заключение"""
        # Обновить исходный текст
        self.original_text.delete(1.0, tk.END)
        self.original_text.insert(1.0, report.original_text)
        
        # Обновить обработанный текст
        self.processed_text.config(state=tk.NORMAL)
        self.processed_text.delete(1.0, tk.END)
        processed = report.processed_text or report.original_text
        self.processed_text.insert(1.0, processed)
        self.processed_text.config(state=tk.DISABLED)
    
    def get_original_text(self) -> str:
        """Получить исходный текст от пользователя"""
        return self.original_text.get(1.0, tk.END).strip()
    
    def set_process_callback(self, callback: Callable[[], None]):
        """Установить callback для обработки текста"""
        self.process_callback = callback
    
    def set_template_callback(self, callback: Callable[[str], None]):
        """Установить callback для выбора шаблона"""
        self.template_callback = callback

    def set_modality_callback(self, callback: Callable[[Modality], None]):
        """Установить callback для выбора модальности"""
        self.modality_callback = callback
    
    def update_template_list(self, templates: list):
        """Обновить список шаблонов"""
        template_names = [t.name for t in templates] if templates else []
        self.template_combo['values'] = template_names
        if template_names:
            self.template_var.set(template_names[0])
        else:
            self.template_var.set("")
    
    def run(self):
        """Запустить UI"""
        self.root.mainloop()
