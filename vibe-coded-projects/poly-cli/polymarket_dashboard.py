#!/usr/bin/env python3
"""Polymarket high-volume markets dashboard.

- Terminal table view for top markets by total volume
- Includes 24h volume and 24h price change where available
- Optional watch mode for periodic refresh
- Optional JSON output for pipeline usage
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import ctypes
from datetime import datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://gamma-api.polymarket.com/events"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    WHITE = "\033[97m"


def _enable_windows_ansi() -> None:
    if os.name != "nt":
        return
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        if handle == 0 or handle == -1:
            return
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)) == 0:
            return
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    except Exception:
        return


def _supports_color(no_color: bool) -> bool:
    if no_color or os.getenv("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def _paint(text: str, color: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"{color}{text}{C.RESET}"


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return default
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _format_money(value: float) -> str:
    abs_value = abs(value)
    if abs_value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if abs_value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if abs_value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def _format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


def _normalize_change(raw: Any) -> float | None:
    if raw is None:
        return None
    val = _as_float(raw, default=0.0)
    # Some APIs return decimal fraction (-0.04 == -4%), others return full percent.
    if -1.0 <= val <= 1.0:
        return val * 100
    return val


def _visible_len(text: str) -> int:
    return len(ANSI_RE.sub("", text))


def _truncate_visible(text: str, max_len: int) -> str:
    if max_len <= 0:
        return ""
    if _visible_len(text) <= max_len:
        return text
    plain = ANSI_RE.sub("", text)
    if max_len <= 3:
        return plain[:max_len]
    return plain[: max_len - 3] + "..."


def _pad_visible(text: str, width: int) -> str:
    text = _truncate_visible(text, width)
    padding = width - _visible_len(text)
    if padding > 0:
        return text + (" " * padding)
    return text


def fetch_markets(limit: int, offset: int = 0) -> list[dict[str, Any]]:
    params = {
        "active": "true",
        "closed": "false",
        "order": "volume",
        "ascending": "false",
        "limit": str(limit),
        "offset": str(offset),
    }
    url = f"{BASE_URL}?{urlencode(params)}"
    req = Request(
        url,
        headers={
            "User-Agent": "poly-cli-dashboard/1.0",
            "Accept": "application/json",
        },
    )

    with urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    rows: list[dict[str, Any]] = []
    for event in payload:
        event_title = event.get("title") or event.get("slug") or "Untitled Event"
        event_slug = event.get("slug")
        markets = event.get("markets") or []

        for market in markets:
            title = (
                market.get("question")
                or market.get("title")
                or market.get("slug")
                or event_title
            )
            total_volume = _as_float(
                market.get("volumeNum")
                or market.get("volume")
                or market.get("volumeClob")
                or market.get("volumeAmm")
            )
            volume_24h = _as_float(market.get("volume24hr"))
            change_24h = _normalize_change(
                market.get("oneDayPriceChange") or market.get("oneDayPriceChangePercent")
            )

            rows.append(
                {
                    "event": event_title,
                    "title": title,
                    "slug": market.get("slug") or event_slug,
                    "volume": total_volume,
                    "volume24h": volume_24h,
                    "change24hPct": change_24h,
                    "endDate": market.get("endDateIso") or market.get("endDate"),
                }
            )

    rows.sort(key=lambda x: x["volume"], reverse=True)
    return rows


def render_table(rows: list[dict[str, Any]], top: int, color: bool = True) -> str:
    top_rows = rows[:top]
    headers = ["#", "Market", "Total Volume", "24h Volume", "24h Change", "End"]
    widths = [4, 64, 14, 12, 11, 20]

    lines = []
    lines.append(
        " | ".join(
            _paint(_pad_visible(h, widths[i]), C.BLUE + C.BOLD, color)
            for i, h in enumerate(headers)
        )
    )
    lines.append(_paint("-" * (sum(widths) + (3 * (len(widths) - 1))), C.DIM, color))

    for idx, row in enumerate(top_rows, start=1):
        end_str = ""
        if row["endDate"]:
            end_str = str(row["endDate"])
            try:
                dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                end_str = dt.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                pass

        change_val = row["change24hPct"]
        change_txt = _format_percent(change_val)
        if change_val is None:
            change_txt = _paint(change_txt, C.DIM, color)
        elif change_val > 0:
            change_txt = _paint(f"↑ {change_txt}", C.GREEN + C.BOLD, color)
        elif change_val < 0:
            change_txt = _paint(f"↓ {change_txt}", C.RED + C.BOLD, color)
        else:
            change_txt = _paint(change_txt, C.YELLOW, color)

        rank_txt = _paint(str(idx), C.CYAN + C.BOLD, color)
        market_txt = _paint(str(row["title"]), C.WHITE, color)
        vol_total_txt = _paint(_format_money(row["volume"]), C.CYAN, color)
        vol_24h_txt = _paint(_format_money(row["volume24h"]), C.CYAN, color)
        end_txt = _paint(end_str or "n/a", C.DIM, color)

        cols = [rank_txt, market_txt, vol_total_txt, vol_24h_txt, change_txt, end_txt]
        lines.append(
            " | ".join(_pad_visible(cols[i], widths[i]) for i in range(len(widths)))
        )

    return "\n".join(lines)


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def run(args: argparse.Namespace) -> int:
    _enable_windows_ansi()
    color = _supports_color(args.no_color)

    while True:
        try:
            rows = fetch_markets(limit=max(args.fetch_limit, args.top))
        except Exception as exc:  # pragma: no cover - runtime/network behavior
            print(f"Failed to fetch data: {exc}", file=sys.stderr)
            if args.watch:
                time.sleep(args.interval)
                continue
            return 1

        if args.json:
            print(json.dumps(rows[: args.top], indent=2))
        else:
            clear_screen()
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            title = _paint(f"Polymarket Top {args.top} by Volume", C.BOLD + C.CYAN, color)
            updated = _paint(f"Updated: {now}", C.DIM, color)
            print(f"{title}  |  {updated}")
            print(render_table(rows, top=args.top, color=color))
            print(_paint("\nSource: https://gamma-api.polymarket.com/events", C.DIM, color))

        if not args.watch:
            break
        if args.json:
            break
        time.sleep(args.interval)

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Polymarket dashboard: highest volume markets + 24h change"
    )
    parser.add_argument("--top", type=int, default=20, help="Number of markets to display")
    parser.add_argument(
        "--fetch-limit",
        type=int,
        default=150,
        help="Number of events to fetch from API (higher = broader coverage)",
    )
    parser.add_argument(
        "--watch", action="store_true", help="Continuously refresh the dashboard"
    )
    parser.add_argument(
        "--interval", type=int, default=30, help="Refresh interval seconds in watch mode"
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit top markets as JSON (for pipelines)"
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable ANSI colors in terminal output"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.top < 1:
        print("--top must be >= 1", file=sys.stderr)
        return 2
    if args.fetch_limit < 1:
        print("--fetch-limit must be >= 1", file=sys.stderr)
        return 2
    if args.interval < 2:
        print("--interval must be >= 2", file=sys.stderr)
        return 2
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
