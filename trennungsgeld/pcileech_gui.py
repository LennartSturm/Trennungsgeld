"""Tkinter GUI zum direkten Anpassen eines PCILeech FPGA Projekts."""
from __future__ import annotations

from pathlib import Path

from .pcileech import parse_device_info, patch_project_template, render_define_block


class PciLeechAdapterGUI:
    """Einfache Oberfläche: Rohdaten + Vorlage rein, Ergebnis raus."""

    def __init__(self, root, tk_module, ttk_module, messagebox_module, filedialog_module, scrolledtext_cls) -> None:
        self.root = root
        self.tk = tk_module
        self.ttk = ttk_module
        self.messagebox = messagebox_module
        self.filedialog = filedialog_module
        self.scrolledtext_cls = scrolledtext_cls

        self._build_layout()

    def _build_layout(self) -> None:
        self.root.title("PCILeech FPGA Adapter")
        self.root.minsize(900, 620)
        main = self.ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)
        main.rowconfigure(3, weight=1)

        self.ttk.Label(main, text="Ausgelesene PCIe-Daten").grid(row=0, column=0, sticky="w")
        self.ttk.Label(main, text="Projektvorlage (optional)").grid(row=0, column=1, sticky="w")

        self.raw_input = self.scrolledtext_cls(main, wrap="word", height=14)
        self.raw_input.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=(4, 8))

        self.template_input = self.scrolledtext_cls(main, wrap="word", height=14)
        self.template_input.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=(4, 8))

        button_row = self.ttk.Frame(main)
        button_row.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        button_row.columnconfigure(0, weight=1)

        self.ttk.Button(button_row, text="Rohdaten laden", command=self._load_raw).grid(row=0, column=0, sticky="w")
        self.ttk.Button(button_row, text="Vorlage laden", command=self._load_template).grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.ttk.Button(button_row, text="Anpassen", command=self._adapt).grid(row=0, column=2, sticky="e", padx=(8, 0))
        self.ttk.Button(button_row, text="Ergebnis speichern", command=self._save_result).grid(row=0, column=3, sticky="e", padx=(8, 0))

        self.ttk.Label(main, text="Ergebnis").grid(row=3, column=0, columnspan=2, sticky="w")
        self.output = self.scrolledtext_cls(main, wrap="word", height=16)
        self.output.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(4, 0))
        main.rowconfigure(4, weight=1)

    def _set_text(self, widget, value: str) -> None:
        widget.delete("1.0", "end")
        widget.insert("1.0", value)

    def _load_raw(self) -> None:
        path = self.filedialog.askopenfilename(title="PCIe-Rohdaten öffnen")
        if not path:
            return
        self._set_text(self.raw_input, Path(path).read_text(encoding="utf-8"))

    def _load_template(self) -> None:
        path = self.filedialog.askopenfilename(title="Vorlage öffnen")
        if not path:
            return
        self._set_text(self.template_input, Path(path).read_text(encoding="utf-8"))

    def _adapt(self) -> None:
        try:
            raw = self.raw_input.get("1.0", "end")
            device = parse_device_info(raw)
            template = self.template_input.get("1.0", "end").strip()
            if template:
                result = patch_project_template(template, device)
            else:
                result = render_define_block(device)
            self._set_text(self.output, result)
        except ValueError as exc:
            self.messagebox.showerror("Fehler", str(exc))

    def _save_result(self) -> None:
        content = self.output.get("1.0", "end").strip()
        if not content:
            self.messagebox.showwarning("Hinweis", "Kein Ergebnis zum Speichern vorhanden.")
            return
        path = self.filedialog.asksaveasfilename(title="Ergebnis speichern")
        if not path:
            return
        Path(path).write_text(content + "\n", encoding="utf-8")


def launch_gui() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk

    root = tk.Tk()
    PciLeechAdapterGUI(root, tk, ttk, messagebox, filedialog, scrolledtext.ScrolledText)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
