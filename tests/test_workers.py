"""Tests for the thread-pool worker helpers."""

import pytest

from promptpilot.workers import WorkerResult, run_in_threads


def test_run_in_threads_returns_one_result_per_item() -> None:
    results = run_in_threads(["a", "b", "c"], lambda item: item.upper())

    assert len(results) == 3
    assert {result.item for result in results} == {"a", "b", "c"}
    assert all(result.succeeded for result in results)
    assert {str(result.value) for result in results} == {"A", "B", "C"}


def test_run_in_threads_keeps_a_failing_worker_alive() -> None:
    def explode(item: str) -> str:
        if item == "bad":
            raise RuntimeError("worker failed")
        return item

    results = run_in_threads(["good", "bad"], explode)
    by_item = {result.item: result for result in results}

    assert by_item["good"].succeeded is True
    assert by_item["bad"].succeeded is False
    assert "worker failed" in (by_item["bad"].error or "")


def test_run_in_threads_records_a_duration() -> None:
    results = run_in_threads(["a"], lambda item: item)

    assert results[0].elapsed_ms >= 0


def test_run_in_threads_requires_a_positive_worker_count() -> None:
    with pytest.raises(ValueError):
        run_in_threads(["a"], lambda item: item, max_workers=0)


def test_worker_result_reports_success() -> None:
    assert WorkerResult("item", "value", None, 1.0).succeeded is True
    assert WorkerResult("item", None, "failed", 1.0).succeeded is False
