from pathlib import Path

import pytest

from promptpilot.schemas import PromptStat
from promptpilot.stores import StatsStore


def test_stats_store_round_trip(tmp_path: Path) -> None:
    store = StatsStore(tmp_path / "stats.jsonl")
    store.record(
        PromptStat(
            model="test-model",
            prompt_chars=5,
            response_chars=10,
            latency_ms=25.5,
        )
    )

    records = store.all()
    assert len(records) == 1
    assert records[0].model == "test-model"
    assert store.summary()["requests"] == 1


def test_clear_removes_file(tmp_path: Path) -> None:
    store = StatsStore(tmp_path / "stats.jsonl")
    store.record(
        PromptStat(
            model="test-model",
            prompt_chars=1,
            response_chars=1,
            latency_ms=1,
        )
    )
    store.clear()
    assert not store.path.exists()


def test_summary_of_empty_store_uses_safe_defaults(tmp_path: Path) -> None:
    store = StatsStore(tmp_path / "stats.jsonl")

    assert store.all() == []
    assert store.summary() == {
        "requests": 0,
        "successful": 0,
        "failed": 0,
        "average_latency_ms": 0.0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "last_model": "none",
    }


def test_summary_aggregates_multiple_records(tmp_path: Path) -> None:
    store = StatsStore(tmp_path / "stats.jsonl")
    store.record(
        PromptStat(
            model="model-a",
            prompt_chars=5,
            response_chars=10,
            prompt_tokens=2,
            completion_tokens=3,
            latency_ms=10.0,
        )
    )
    store.record(
        PromptStat(
            model="model-b",
            prompt_chars=5,
            response_chars=20,
            prompt_tokens=4,
            completion_tokens=6,
            latency_ms=30.0,
            success=False,
        )
    )

    summary = store.summary()

    assert summary["requests"] == 2
    assert summary["successful"] == 1
    assert summary["failed"] == 1
    assert summary["average_latency_ms"] == 20.0
    assert summary["prompt_tokens"] == 6
    assert summary["completion_tokens"] == 9
    assert summary["last_model"] == "model-b"


def test_recent_returns_the_tail_of_the_history(tmp_path: Path) -> None:
    store = StatsStore(tmp_path / "stats.jsonl")
    for index in range(5):
        store.record(
            PromptStat(
                model=f"model-{index}",
                prompt_chars=1,
                response_chars=1,
                latency_ms=1.0,
                )
        )

    recent = store.recent(limit=2)

    assert [record.model for record in recent] == ["model-3", "model-4"]


def test_recent_rejects_a_non_positive_limit(tmp_path: Path) -> None:
    store = StatsStore(tmp_path / "stats.jsonl")

    with pytest.raises(ValueError):
        store.recent(limit=0)


def test_corrupt_line_reports_its_line_number(tmp_path: Path) -> None:
    path = tmp_path / "stats.jsonl"
    path.write_text('{"not": "a stat"}\n', encoding="utf-8")
    store = StatsStore(path)

    with pytest.raises(ValueError, match="line 1"):
        store.all()
