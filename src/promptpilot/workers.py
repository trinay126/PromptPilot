"""Thread-pool utilities for I/O-bound demonstrations."""

from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from time import perf_counter
from typing import Callable, TypeVar

T = TypeVar("T")
R = TypeVar("R")

@dataclass(frozen=True, slots=True)
class WorkerResult:
    """Result envelope that records success, error, and duration."""
    item: str
    value: object | None
    error: str | None
    elapsed_ms: float

def run_in_threads(
        items: list[T],
        function: Callable[[T], R],
        max_workers: int = 4,
) -> list[WorkerResult]:
    """Run independent I/O-bound functions concurrently in a thread pool."""
    if max_workers < 1:
        raise ValueError("max_workers must be positive")

    def call_one(item: T) -> WorkerResult:
        started = perf_counter()
        try:
            value = function(item)
            return WorkerResult(str(item), value, None, (perf_counter() - started) * 1000)
        except Exception as error:
            return WorkerResult(str(item), None, str(error), (perf_counter() - started) * 1000)

    results: list[WorkerResult] = []
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="promptpilot") as pool:
        futures = {pool.submit(call_one, item): item for item in items}
        for future in as_completed(futures):
            results.append(future.result)
    return results


            