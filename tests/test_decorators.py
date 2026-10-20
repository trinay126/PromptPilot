from promptpilot.decorators import timed


def test_timed_preserves_result_and_records_duration() -> None:
    @timed
    def add(left: int, right: int) -> int:
        return left + right

    assert add(2, 3) == 5
    assert add.last_duration_ms >= 0
