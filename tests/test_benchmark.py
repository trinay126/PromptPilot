import pytest

from promptpilot.benchmark import BenchmarkRunner, fastest_summary


class FakeClient:
    def __init__(self, model: str) -> None:
        self.model = model

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def ask(self, prompt: str, model: str):
        return object()


class FailingClient:
    def __init__(self, model: str) -> None:
        self.model = model

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def ask(self, prompt: str, model: str):
        raise RuntimeError("model unavailable")


def test_benchmark_collects_successful_rounds() -> None:
    result = BenchmarkRunner(lambda model: FakeClient(model)).run(["a"], "ok", rounds=2)
    assert result[0].successful == 2
    assert result[0].failed == 0
    assert len(result[0].samples) == 2


def test_benchmark_records_failures_without_raising() -> None:
    result = BenchmarkRunner(lambda model: FailingClient(model)).run(["a"], "ok", rounds=2)

    assert result[0].successful == 0
    assert result[0].failed == 2
    assert result[0].average_ms == 0.0
    assert "model unavailable" in (result[0].samples[0].error or "")


def test_benchmark_requires_at_least_one_model() -> None:
    with pytest.raises(ValueError):
        BenchmarkRunner(lambda model: FakeClient(model)).run([], "ok")


def test_benchmark_requires_at_least_one_round() -> None:
    with pytest.raises(ValueError):
        BenchmarkRunner(lambda model: FakeClient(model)).run(["a"], "ok", rounds=0)


def test_benchmark_summary_serializes_to_json_ready_dictionaries() -> None:
    result = BenchmarkRunner(lambda model: FakeClient(model)).run(["a"], "ok", rounds=1)
    payload = result[0].to_dict()

    assert payload["model"] == "a"
    assert payload["rounds"] == 1
    assert isinstance(payload["samples"], list)
    assert payload["samples"][0]["model"] == "a"


def test_fastest_summary_picks_the_lowest_average_latency() -> None:
    result = BenchmarkRunner(lambda model: FakeClient(model)).run(["a", "b"], "ok", rounds=1)

    fastest = fastest_summary(result)

    assert fastest is not None
    assert fastest.model in {"a", "b"}


def test_fastest_summary_returns_none_when_every_model_failed() -> None:
    result = BenchmarkRunner(lambda model: FailingClient(model)).run(["a"], "ok", rounds=1)

    assert fastest_summary(result) is None
