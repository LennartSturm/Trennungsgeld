from __future__ import annotations

from trennungsgeld.pcileech import parse_device_info, patch_project_template, render_define_block


def test_parse_device_info_and_define_rendering() -> None:
    raw = """
    Vendor: 10ec
    Device: 8168
    Subsystem Vendor: 1043
    Subsystem: 8677
    Revision: 15
    Class: 020000
    """
    info = parse_device_info(raw)

    assert info.vendor_id == 0x10EC
    assert info.device_id == 0x8168
    define_block = render_define_block(info)
    assert "`define CFG_VENDOR_ID 16'h10EC" in define_block
    assert "`define CFG_CLASS_CODE 24'h020000" in define_block


def test_patch_project_template() -> None:
    raw = "vendor=8086 device=100e"
    info = parse_device_info(raw)
    template = "VID={{VENDOR_ID}} DID={{DEVICE_ID}}\n{{DEFINE_BLOCK}}\n"

    patched = patch_project_template(template, info)

    assert "VID=16'h8086" in patched
    assert "DID=16'h100E" in patched
    assert "`define CFG_DEVICE_ID 16'h100E" in patched
