"""Graphische Benutzeroberfläche für den Trennungsgeldrechner."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Sequence

from .calculator import (
    AllowanceInput,
    TrennungsgeldCalculator,
    TravelCostInput,
    format_breakdown,
)


NumberParser = Callable[[str, str], int | float | None]


def parse_int(value: str, label: str) -> int:
    """Parse an integer value from a text field."""

    text = value.strip()
    if not text:
        return 0
    try:
        return int(text)
    except ValueError as exc:  # pragma: no cover - defensive programming
        raise ValueError(f"{label}: Bitte eine ganze Zahl eingeben.") from exc


def parse_float(value: str, label: str) -> float:
    """Parse a float value from a text field."""

    text = value.strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError as exc:  # pragma: no cover - defensive programming
        raise ValueError(f"{label}: Bitte eine Zahl eingeben.") from exc


def parse_optional_float(value: str, label: str) -> Optional[float]:
    """Parse an optional float, allowing empty strings."""

    text = value.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError as exc:  # pragma: no cover - defensive programming
        raise ValueError(
            f"{label}: Bitte eine Zahl eingeben oder das Feld leer lassen."
        ) from exc


@dataclass(frozen=True)
class FieldSpec:
    """Configuration for a single input field."""

    key: str
    label: str
    parser: NumberParser
    default: str = "0"


MEAL_FIELDS: Sequence[FieldSpec] = (
    FieldSpec("full_days", "Volle Abwesenheitstage", parse_int),
    FieldSpec("arrival_departure_days", "An- oder Abreisetage", parse_int),
    FieldSpec("partial_days", "Weitere Tage (>8h)", parse_int),
    FieldSpec(
        "overnight_stays_with_receipts",
        "Übernachtungen mit Beleg",
        parse_int,
    ),
    FieldSpec(
        "overnight_costs_total",
        "Summe belegter Übernachtungskosten",
        parse_float,
        "0.0",
    ),
    FieldSpec(
        "overnight_stays_without_receipts",
        "Übernachtungen ohne Beleg",
        parse_int,
    ),
)


TRAVEL_FIELDS: Sequence[FieldSpec] = (
    FieldSpec("initial_trip_distance_km", "Anreise (km)", parse_float, "0.0"),
    FieldSpec(
        "initial_trip_actual_cost",
        "Anreise tatsächliche Kosten",
        parse_optional_float,
        "",
    ),
    FieldSpec("return_trip_distance_km", "Rückreise (km)", parse_float, "0.0"),
    FieldSpec(
        "return_trip_actual_cost",
        "Rückreise tatsächliche Kosten",
        parse_optional_float,
        "",
    ),
    FieldSpec("weekly_home_trips", "Genehmigte Heimfahrten", parse_int),
    FieldSpec("home_trip_distance_km", "Heimfahrt (km)", parse_float, "0.0"),
    FieldSpec(
        "home_trip_actual_cost",
        "Heimfahrt tatsächliche Kosten",
        parse_optional_float,
        "",
    ),
    FieldSpec("commuting_days", "Pendeltage", parse_int),
    FieldSpec("commuting_distance_km", "Pendelstrecke (km)", parse_float, "0.0"),
    FieldSpec(
        "commuting_actual_cost_per_day",
        "Pendelkosten pro Tag",
        parse_optional_float,
        "",
    ),
    FieldSpec("additional_costs", "Weitere Kosten", parse_float, "0.0"),
)


class CalculatorGUI:
    """Encapsulates the Tkinter based graphical user interface."""

    def __init__(
        self,
        root,
        tk_module,
        ttk_module,
        messagebox_module,
        scrolledtext_cls,
    ) -> None:
        self.root = root
        self.tk = tk_module
        self.ttk = ttk_module
        self.messagebox = messagebox_module
        self.scrolledtext_cls = scrolledtext_cls

        self.calculator = TrennungsgeldCalculator()
        self.vars: Dict[str, "tk_module.StringVar"] = {}
        self.vehicle_var = tk_module.StringVar(value="car")
        self.total_var = tk_module.StringVar(value="0.00 EUR")
        self.meal_var = tk_module.StringVar(value="0.00 EUR")
        self.travel_var = tk_module.StringVar(value="0.00 EUR")

        self._build_layout()

    def _build_layout(self) -> None:
        root = self.root
        root.title("Trennungsgeldrechner")
        root.minsize(720, 540)

        main = self.ttk.Frame(root, padding=12)
        main.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(2, weight=1)

        meal_frame = self.ttk.LabelFrame(main, text="Verpflegung & Übernachtung")
        meal_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        self._build_fields(meal_frame, MEAL_FIELDS)

        travel_frame = self.ttk.LabelFrame(main, text="Reisekosten")
        travel_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))
        self._build_fields(travel_frame, TRAVEL_FIELDS)
        self._build_vehicle_selector(travel_frame)

        button_frame = self.ttk.Frame(main)
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        button_frame.columnconfigure(0, weight=1)

        calculate_btn = self.ttk.Button(
            button_frame,
            text="Berechnen",
            command=self._on_calculate,
        )
        calculate_btn.grid(row=0, column=0, sticky="e")

        totals = self.ttk.Frame(main)
        totals.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        totals.columnconfigure(1, weight=1)
        totals.columnconfigure(3, weight=1)

        self.ttk.Label(totals, text="Gesamt:").grid(row=0, column=0, sticky="w")
        self.ttk.Label(totals, textvariable=self.total_var).grid(
            row=0, column=1, sticky="w"
        )
        self.ttk.Label(totals, text="Verpflegung:").grid(row=0, column=2, sticky="w")
        self.ttk.Label(totals, textvariable=self.meal_var).grid(
            row=0, column=3, sticky="w"
        )
        self.ttk.Label(totals, text="Reisekosten:").grid(row=0, column=4, sticky="w")
        self.ttk.Label(totals, textvariable=self.travel_var).grid(
            row=0, column=5, sticky="w"
        )

        output_frame = self.ttk.LabelFrame(main, text="Berechnungsübersicht")
        output_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")
        main.rowconfigure(3, weight=1)
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)

        self.output = self.scrolledtext_cls(output_frame, wrap="word", height=10)
        self.output.grid(row=0, column=0, sticky="nsew")
        self._set_output_text(
            "Bitte Werte eingeben und auf 'Berechnen' klicken, um eine Prognose zu erhalten."
        )

    def _build_fields(self, parent, specs: Sequence[FieldSpec]) -> None:
        for row, spec in enumerate(specs):
            self.ttk.Label(parent, text=spec.label).grid(
                row=row, column=0, sticky="w", padx=4, pady=2
            )
            var = self.tk.StringVar(value=spec.default)
            entry = self.ttk.Entry(parent, textvariable=var, width=18)
            entry.grid(row=row, column=1, sticky="ew", padx=4, pady=2)
            parent.columnconfigure(1, weight=1)
            self.vars[spec.key] = var

    def _build_vehicle_selector(self, parent) -> None:
        row = len(TRAVEL_FIELDS)
        self.ttk.Label(parent, text="Fahrzeug").grid(
            row=row, column=0, sticky="w", padx=4, pady=2
        )
        option = self.ttk.OptionMenu(
            parent,
            self.vehicle_var,
            self.vehicle_var.get(),
            "car",
            "motorcycle",
            "bike",
        )
        option.grid(row=row, column=1, sticky="ew", padx=4, pady=2)

    def _collect_values(self, specs: Sequence[FieldSpec]) -> Dict[str, int | float | None]:
        values: Dict[str, int | float | None] = {}
        errors = []
        for spec in specs:
            try:
                values[spec.key] = spec.parser(self.vars[spec.key].get(), spec.label)
            except ValueError as exc:
                errors.append(str(exc))
        if errors:
            raise ValueError("\n".join(errors))
        return values

    def _on_calculate(self) -> None:
        try:
            allowance_kwargs = self._collect_values(MEAL_FIELDS)
            travel_kwargs = self._collect_values(TRAVEL_FIELDS)
            travel_kwargs["vehicle"] = self.vehicle_var.get()

            allowance = AllowanceInput(**allowance_kwargs)  # type: ignore[arg-type]
            travel = TravelCostInput(**travel_kwargs)  # type: ignore[arg-type]

            result = self.calculator.calculate(allowance, travel)
        except ValueError as exc:
            self.messagebox.showerror("Eingabefehler", str(exc))
            return

        self.total_var.set(f"{result.total_allowance:.2f} EUR")
        self.meal_var.set(f"{result.meal_allowance:.2f} EUR")
        self.travel_var.set(f"{result.travel_costs:.2f} EUR")
        self._set_output_text("\n".join(format_breakdown(result)))

    def _set_output_text(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")


def launch_gui() -> None:
    """Startet die Tkinter-Oberfläche."""

    import tkinter as tk  # Imported lazily to avoid dependency during tests
    from tkinter import messagebox, ttk
    from tkinter import scrolledtext

    root = tk.Tk()
    CalculatorGUI(root, tk, ttk, messagebox, scrolledtext.ScrolledText)
    root.mainloop()


if __name__ == "__main__":  # pragma: no cover - manual start
    launch_gui()


__all__ = [
    "launch_gui",
    "parse_int",
    "parse_float",
    "parse_optional_float",
]
