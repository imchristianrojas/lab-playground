from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_DATA_PATH = Path("data") / "ops_data.json"


@dataclass
class Store:
    path: Path = DEFAULT_DATA_PATH

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "notes": [],
                "todos": [],
                "timer": None,
                "counters": {"note_id": 0, "todo_id": 0},
            }
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_date(date_text: str) -> str:
    return datetime.strptime(date_text, "%Y-%m-%d").date().isoformat()


def timer_end_time(start_iso: str, minutes: int) -> datetime:
    start = datetime.fromisoformat(start_iso)
    return start + timedelta(minutes=minutes)

