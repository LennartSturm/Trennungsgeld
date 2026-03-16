"""Werkzeuge zum Anpassen eines PCILeech-FPGA-Projekts anhand ausgelesener PCIe-Daten."""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class PciDeviceInfo:
    """Ausgelesene PCIe-Identifikationsdaten eines Geräts."""

    vendor_id: int
    device_id: int
    subsystem_vendor_id: int | None = None
    subsystem_id: int | None = None
    revision_id: int | None = None
    class_code: int | None = None


_HEX_PATTERNS = {
    "vendor_id": re.compile(r"(?:vendor(?:_id)?|vid)\s*[:=]\s*(0x[0-9a-fA-F]{1,4}|[0-9a-fA-F]{1,4})", re.IGNORECASE),
    "device_id": re.compile(r"(?:device(?:_id)?|did)\s*[:=]\s*(0x[0-9a-fA-F]{1,4}|[0-9a-fA-F]{1,4})", re.IGNORECASE),
    "subsystem_vendor_id": re.compile(r"(?:subsystem[_\s-]*vendor(?:_id)?|svid)\s*[:=]\s*(0x[0-9a-fA-F]{1,4}|[0-9a-fA-F]{1,4})", re.IGNORECASE),
    "subsystem_id": re.compile(r"(?:subsystem(?:_id)?|ssid)\s*[:=]\s*(0x[0-9a-fA-F]{1,4}|[0-9a-fA-F]{1,4})", re.IGNORECASE),
    "revision_id": re.compile(r"(?:revision(?:_id)?|rev)\s*[:=]\s*(0x[0-9a-fA-F]{1,2}|[0-9a-fA-F]{1,2})", re.IGNORECASE),
    "class_code": re.compile(r"(?:class(?:_code)?)\s*[:=]\s*(0x[0-9a-fA-F]{1,6}|[0-9a-fA-F]{1,6})", re.IGNORECASE),
}


def _parse_hex(text: str) -> int:
    return int(text, 16)


def parse_device_info(raw_text: str) -> PciDeviceInfo:
    """Extrahiert Geräteinformationen aus Text (z. B. lspci-/PCILeech-Ausgabe)."""

    values: dict[str, int | None] = {
        "vendor_id": None,
        "device_id": None,
        "subsystem_vendor_id": None,
        "subsystem_id": None,
        "revision_id": None,
        "class_code": None,
    }

    normalized = raw_text.strip()
    for key, pattern in _HEX_PATTERNS.items():
        match = pattern.search(normalized)
        if match:
            values[key] = _parse_hex(match.group(1))

    if values["vendor_id"] is None or values["device_id"] is None:
        raise ValueError("Vendor-ID und Device-ID konnten nicht aus den Daten gelesen werden.")

    return PciDeviceInfo(
        vendor_id=values["vendor_id"],
        device_id=values["device_id"],
        subsystem_vendor_id=values["subsystem_vendor_id"],
        subsystem_id=values["subsystem_id"],
        revision_id=values["revision_id"],
        class_code=values["class_code"],
    )


def render_define_block(device: PciDeviceInfo) -> str:
    """Erzeugt einen Define-Block für ein PCILeech-FPGA-Projekt (Verilog Header)."""

    lines = [
        "`define CFG_VENDOR_ID 16'h%04X" % device.vendor_id,
        "`define CFG_DEVICE_ID 16'h%04X" % device.device_id,
    ]

    if device.subsystem_vendor_id is not None:
        lines.append("`define CFG_SUBSYSTEM_VENDOR_ID 16'h%04X" % device.subsystem_vendor_id)
    if device.subsystem_id is not None:
        lines.append("`define CFG_SUBSYSTEM_ID 16'h%04X" % device.subsystem_id)
    if device.revision_id is not None:
        lines.append("`define CFG_REVISION_ID 8'h%02X" % device.revision_id)
    if device.class_code is not None:
        lines.append("`define CFG_CLASS_CODE 24'h%06X" % device.class_code)

    return "\n".join(lines)


def patch_project_template(template: str, device: PciDeviceInfo) -> str:
    """Ersetzt Platzhalter in einer Projektvorlage direkt mit ausgelesenen Werten.

    Unterstützte Platzhalter:
    - {{VENDOR_ID}}
    - {{DEVICE_ID}}
    - {{SUBSYSTEM_VENDOR_ID}}
    - {{SUBSYSTEM_ID}}
    - {{REVISION_ID}}
    - {{CLASS_CODE}}
    - {{DEFINE_BLOCK}}
    """

    replacements = {
        "{{VENDOR_ID}}": f"16'h{device.vendor_id:04X}",
        "{{DEVICE_ID}}": f"16'h{device.device_id:04X}",
        "{{SUBSYSTEM_VENDOR_ID}}": (
            f"16'h{device.subsystem_vendor_id:04X}" if device.subsystem_vendor_id is not None else "16'h0000"
        ),
        "{{SUBSYSTEM_ID}}": f"16'h{device.subsystem_id:04X}" if device.subsystem_id is not None else "16'h0000",
        "{{REVISION_ID}}": f"8'h{device.revision_id:02X}" if device.revision_id is not None else "8'h00",
        "{{CLASS_CODE}}": f"24'h{device.class_code:06X}" if device.class_code is not None else "24'h000000",
        "{{DEFINE_BLOCK}}": render_define_block(device),
    }

    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result


__all__ = [
    "PciDeviceInfo",
    "parse_device_info",
    "render_define_block",
    "patch_project_template",
]
