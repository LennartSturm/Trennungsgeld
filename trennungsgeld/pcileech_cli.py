"""CLI zum Anpassen eines PCILeech-FPGA-Projekts aus ausgelesenen Daten."""
from __future__ import annotations

import argparse
from pathlib import Path

from .pcileech import parse_device_info, patch_project_template, render_define_block


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Passt ein PCILeech-FPGA-Projekt anhand ausgelesener PCIe-Daten an."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Textdatei mit ausgelesenen PCIe-Daten (z. B. PCILeech/lspci Ausgabe)",
    )
    parser.add_argument(
        "--template",
        type=Path,
        help="Optionale Projektvorlage mit Platzhaltern",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Ausgabedatei für die gepatchte Vorlage; ohne Angabe Ausgabe auf stdout",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw = args.input.read_text(encoding="utf-8")
    device = parse_device_info(raw)

    if args.template:
        template = args.template.read_text(encoding="utf-8")
        content = patch_project_template(template, device)
    else:
        content = render_define_block(device)

    if args.output:
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content)


if __name__ == "__main__":
    main()
