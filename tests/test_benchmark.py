from promptpilot.benchmark import BenchmarkRunner


class FakeClient:
    def __init__(self, model: str) -> None:
        self.model = model

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def ask(self, prompt: str, model: str):
        return object()


def test_benchmark_collects_successful_rounds() -> None:
    result = BenchmarkRunner(lambda model: FakeClient(model)).run(["a"], "ok", rounds=2)
    assert result[0].successful == 2
    assert result[0].failed == 0
    assert len(result[0].samples) == 2
