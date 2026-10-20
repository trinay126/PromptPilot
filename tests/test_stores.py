from pathlib import Path

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
            source="user",
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
            source="demo",
        )
    )
    store.clear()
    assert not store.path.exists()
