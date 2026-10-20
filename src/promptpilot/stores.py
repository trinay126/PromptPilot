"""Persistent JSONL statistics store."""

from __future__ import annotations

from pathlib import Path
from threading import Lock

from promptpilot.schemas import PromptStat
from promptpilot.utils import mean


class StatsStore:
    """Append one validated JSON object per line and calculate summaries."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def record(self, stat: PromptStat) -> None:
        """Append a stat while preventing interleaved writes from threads."""
        line = stat.model_dump_json()
        with self._lock, self.path.open("a", encoding="utf-8") as file:
            file.write(line + "\n")

    def all(self) -> list[PromptStat]:
        """Read all valid records; skip blank lines but fail on corrupt data."""
        if not self.path.exists():
            return []
        records: list[PromptStat] = []
        with self.path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    continue
                try:
                    records.append(PromptStat.model_validate_json(line))
                except ValueError as error:
                    raise ValueError(f"invalid statistics at line {line_number}") from error
        return records

    def recent(self, limit: int = 10) -> list[PromptStat]:
        """Return the most recent records, newest last."""
        if limit < 1:
            raise ValueError("limit must be at least 1")
        records = self.all()
        return records[-limit:]

    def summary(self) -> dict[str, int | float | str]:
        """Return useful aggregate values for the dashboard."""
        records = self.all()
        if not records:
            return {
                "requests": 0,
                "successful": 0,
                "failed": 0,
                "average_latency_ms": 0.0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "last_model": "none",
            }
        successful = sum(1 for record in records if record.success)
        return {
            "requests": len(records),
            "successful": successful,
            "failed": len(records) - successful,
            "average_latency_ms": round(mean(record.latency_ms for record in records), 2),
            "prompt_tokens": sum(record.prompt_tokens for record in records),
            "completion_tokens": sum(record.completion_tokens for record in records),
            "last_model": records[-1].model,
        }

    def clear(self) -> None:
        """Delete the JSONL file if it exists."""
        with self._lock:
            if self.path.exists():
                self.path.unlink()


__all__ = ["StatsStore"]
