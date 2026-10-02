"""Repeatable model-latency benchmark primitives"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean, median
from time import perf_counter
from typing import Callable

from promptpilot.clients import GroqApiClient

@dataclass(frozen=True, slots=True)
class BenchmarkSample:
    """One model request measurement."""

    model: str
    run: int
    latency_ms: float
    success: bool
    error: str | None = None

@dataclass(frozen=True, slots=True)
class BenchmarkSummary:
    """Aggregated model measurements suitable for tables or JSON."""

    model: str
    rounds: int
    successful: int
    failed: int
    average_ms: float
    median_ms: float
    p95_ms: float
    min_ms: float
    max_ms: float
    samples: tuple[BenchmarkSample, ...]

    def to_dict(self) -> dict[str, object]:
        """Convert the frozen dataclss graphto JSON-compatible dictionaries."""
        result = asdict(self)
        result["samples"] = [asdict(sample) for sample in self.samples]
        return result
    