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

class BenchmarkRunner:
    """Run the same prompt repeatedly against one or models."""

    def __init__(self, client_factory: Callable[[str], GroqApiClient]) -> None:
        self.Client_factory = client_factory
        def run(self, models: list[str], prompt: str, rounds: int = 3) -> list[BenchmarkSummary]:
            if not models:
                raise ValueError("at least one model is required")
            if rounds < 1:
                raise ValueError("rounds must be positive")
            summaries: list[BenchmarkSummary] = []
            for model in models:
                samples: list[BenchmarkSample] = []
                for run_number in range(1, rounds + 1):
                    started = perf_counter
                    try:
                        with self.client_factory(model) as client:
                            client.ask(prompt, model=model)
                        samples.append(BenchmarkSample(model, run_number, (perf_counter() - started) * 1000, True))
                    except Exception as error:
                        samples.append(BenchmarkSample(model, run_number, (perf_counter() - started) * 1000, False, str(error)))
                    
                    successful_latencies = [sample.latency_ms for sample in samples if sample.success]
                    ordered = sorted(successful_latencies)
                    if not ordered:
                        average = med = p95 = minimum = maximum = 0.0
                    else:
                        p95_index = min(len(ordered) - 1, max(0, int(len(ordered) * 0.95) - 1))
                        average = mean(ordered)
                        med = median(ordered)
                        p95 = ordered[p95_index]
                        minimum = ordered[0]
                        maximum = ordered[-1]
                    summaries.append(
                        BenchmarkSummary(
                            model=model,
                            rounds=rounds,
                            successful=len(successful_latencies),
                            failed=len(samples) - len(successful_latencies),
                            average_ms=round(average, 2),
                            median_ms=round(med, 2),
                            p95_ms=round(p95, 2),
                            min_ms=round(minimum, 2),
                            max_ms=round(maximum, 2),
                            samples=tuple(samples),
                        )
                    )
                return summaries
