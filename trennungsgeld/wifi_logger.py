"""Live-Erfassung von WLAN-Signalwerten (Bars) und Speicherung in Datei."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import subprocess
import time
from pathlib import Path
from typing import Callable


def dbm_to_bars(signal_dbm: float) -> int:
    """Map dBm-Werte auf eine einfache 0-4 Bars-Skala."""

    if signal_dbm <= -90:
        return 0
    if signal_dbm <= -80:
        return 1
    if signal_dbm <= -70:
        return 2
    if signal_dbm <= -60:
        return 3
    return 4


def _run_command(args: list[str]) -> str:
    completed = subprocess.run(args, capture_output=True, text=True, check=False)
    return completed.stdout


def list_wireless_interfaces(runner: Callable[[list[str]], str] = _run_command) -> list[str]:
    """Liest WLAN-Interfaces über `iw dev` aus."""

    output = runner(["iw", "dev"])
    interfaces: list[str] = []
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("Interface "):
            interfaces.append(stripped.split(maxsplit=1)[1])
    return interfaces


def read_signal_dbm(
    interface: str,
    runner: Callable[[list[str]], str] = _run_command,
) -> float | None:
    """Liest Signalstärke in dBm über `iw dev <iface> link`."""

    output = runner(["iw", "dev", interface, "link"])
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("signal:"):
            # Beispiel: signal: -57 dBm
            parts = stripped.split()
            if len(parts) >= 2:
                try:
                    return float(parts[1])
                except ValueError:
                    return None
    return None


def read_link_quality(proc_path: Path = Path("/proc/net/wireless")) -> dict[str, float]:
    """Liest Link-Qualität je Interface (0..70) aus /proc/net/wireless."""

    if not proc_path.exists():
        return {}

    content = proc_path.read_text(encoding="utf-8", errors="ignore")
    quality: dict[str, float] = {}
    for line in content.splitlines()[2:]:
        if ":" not in line:
            continue
        name, rest = line.split(":", maxsplit=1)
        interface = name.strip()
        fields = rest.split()
        if not fields:
            continue
        if len(fields) < 2:
            continue
        raw_link = fields[1].rstrip(".")
        try:
            quality[interface] = float(raw_link)
        except ValueError:
            continue
    return quality


def collect_snapshot(
    interfaces: list[str] | None = None,
    runner: Callable[[list[str]], str] = _run_command,
    proc_path: Path = Path("/proc/net/wireless"),
    timestamp: dt.datetime | None = None,
) -> list[dict[str, str | float | int | None]]:
    """Sammelt einen Messpunkt pro WLAN-Interface."""

    if interfaces is None:
        interfaces = list_wireless_interfaces(runner)
    qualities = read_link_quality(proc_path)
    now = timestamp or dt.datetime.now(dt.timezone.utc)

    rows: list[dict[str, str | float | int | None]] = []
    for interface in interfaces:
        dbm = read_signal_dbm(interface, runner)
        bars = dbm_to_bars(dbm) if dbm is not None else None
        rows.append(
            {
                "timestamp": now.isoformat(),
                "interface": interface,
                "signal_dbm": dbm,
                "signal_bars": bars,
                "link_quality": qualities.get(interface),
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict[str, str | float | int | None]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    fieldnames = ["timestamp", "interface", "signal_dbm", "signal_bars", "link_quality"]
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_jsonl(path: Path, rows: list[dict[str, str | float | int | None]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wifi-bars",
        description="Liest live WLAN-Barwerte und speichert sie in eine Datei.",
    )
    parser.add_argument(
        "-i",
        "--interface",
        action="append",
        dest="interfaces",
        help="WLAN-Interface (mehrfach möglich). Ohne Angabe werden alle genutzt.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("wifi_signal_log.csv"),
        help="Ausgabedatei (Standard: wifi_signal_log.csv)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "jsonl"],
        default="csv",
        help="Ausgabeformat (csv oder jsonl)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Messintervall in Sekunden (Standard: 1.0)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="Gesamtdauer in Sekunden, 0 = unendlich bis Strg+C",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    start = time.monotonic()

    try:
        while True:
            rows = collect_snapshot(interfaces=args.interfaces)
            if args.format == "csv":
                _write_csv(args.output, rows)
            else:
                _write_jsonl(args.output, rows)

            for row in rows:
                iface = row["interface"]
                dbm = row["signal_dbm"]
                bars = row["signal_bars"]
                print(f"{row['timestamp']} {iface}: {dbm} dBm ({bars} Bars)")

            if args.duration > 0 and (time.monotonic() - start) >= args.duration:
                break
            time.sleep(max(args.interval, 0.1))
    except KeyboardInterrupt:
        print("Messung beendet.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
