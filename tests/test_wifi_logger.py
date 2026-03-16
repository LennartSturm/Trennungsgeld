from __future__ import annotations

import datetime as dt
from pathlib import Path

from trennungsgeld.wifi_logger import collect_snapshot, dbm_to_bars, list_wireless_interfaces


def test_dbm_to_bars_thresholds() -> None:
    assert dbm_to_bars(-95) == 0
    assert dbm_to_bars(-85) == 1
    assert dbm_to_bars(-75) == 2
    assert dbm_to_bars(-65) == 3
    assert dbm_to_bars(-55) == 4


def test_list_wireless_interfaces_parses_iw_dev() -> None:
    def fake_runner(_args: list[str]) -> str:
        return """phy#0
\tInterface wlan0
\t\tifindex 3
phy#1
\tInterface wlp2s0
"""

    assert list_wireless_interfaces(fake_runner) == ["wlan0", "wlp2s0"]


def test_collect_snapshot_reads_link_quality_and_signal(tmp_path: Path) -> None:
    proc_file = tmp_path / "wireless"
    proc_file.write_text(
        "Inter-| sta-|   Quality        |   Discarded packets               | Missed | WE\n"
        " face | tus | link level noise |  nwid  crypt   frag  retry   misc | beacon | 22\n"
        "wlan0: 0000   63.  -47.  -256        0      0      0      0      0        0\n"
    )

    def fake_runner(args: list[str]) -> str:
        if args == ["iw", "dev", "wlan0", "link"]:
            return "Connected to 11:22:33\n\tsignal: -57 dBm\n"
        raise AssertionError(f"Unexpected args: {args}")

    rows = collect_snapshot(
        interfaces=["wlan0"],
        runner=fake_runner,
        proc_path=proc_file,
        timestamp=dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc),
    )

    assert rows == [
        {
            "timestamp": "2024-01-01T00:00:00+00:00",
            "interface": "wlan0",
            "signal_dbm": -57.0,
            "signal_bars": 4,
            "link_quality": 63.0,
        }
    ]
