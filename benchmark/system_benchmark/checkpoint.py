"""Append-only checkpoint storage for resumable system benchmark runs."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


class BenchmarkCheckpoint:
    """Append-only JSONL checkpoint keyed by benchmark item id."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._records: dict[str, dict[str, Any]] = {}
        self._load_existing()

    def _load_existing(self) -> None:
        if not self.path.exists():
            return
        with self.path.open() as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                item_id = record.get("item_id")
                if item_id:
                    self._records[item_id] = record

    def get(self, item_id: str) -> dict[str, Any] | None:
        record = self._records.get(item_id)
        return dict(record) if record else None

    def save(self, record: dict[str, Any]) -> None:
        item_id = record.get("item_id")
        if not item_id:
            raise ValueError("Checkpoint record requires item_id")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(record)
        line = json.dumps(payload, ensure_ascii=False)
        with self._lock:
            with self.path.open("a") as handle:
                handle.write(line + "\n")
            self._records[item_id] = payload

    def records(self) -> list[dict[str, Any]]:
        return [dict(record) for _, record in sorted(self._records.items())]
