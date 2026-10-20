import asyncio

import pytest

from promptpilot.decorators import (
    async_retry_on_api_error,
    retry_on_api_error,
    timed,
)
from promptpilot.exceptions import GroqAPIError


def test_timed_preserves_result_and_records_duration() -> None:
    @timed
    def add(left: int, right: int) -> int:
        return left + right

    assert add(2, 3) == 5
    assert add.last_duration_ms >= 0


def test_timed_records_duration_even_when_the_call_raises() -> None:
    @timed
    def boom() -> None:
        raise RuntimeError("failed")

    with pytest.raises(RuntimeError):
        boom()

    assert boom.last_duration_ms >= 0


def test_timed_preserves_the_function_metadata() -> None:
    @timed
    def documented() -> None:
        """A helpful docstring."""

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "A helpful docstring."


def test_retry_retries_a_transient_failure_then_succeeds() -> None:
    calls = {"count": 0}

    @retry_on_api_error(attempts=3, delay_seconds=0)
    def flaky() -> str:
        calls["count"] += 1
        if calls["count"] < 3:
            raise GroqAPIError("rate limited", status_code=429)
        return "ok"

    assert flaky() == "ok"
    assert calls["count"] == 3


def test_retry_does_not_retry_a_permanent_failure() -> None:
    calls = {"count": 0}

    @retry_on_api_error(attempts=3, delay_seconds=0)
    def unauthorized() -> None:
        calls["count"] += 1
        raise GroqAPIError("bad key", status_code=401)

    with pytest.raises(GroqAPIError):
        unauthorized()

    assert calls["count"] == 1


def test_retry_raises_the_last_error_after_the_attempts_are_exhausted() -> None:
    @retry_on_api_error(attempts=2, delay_seconds=0)
    def always_failing() -> None:
        raise GroqAPIError("server error", status_code=503)

    with pytest.raises(GroqAPIError, match="server error"):
        always_failing()


def test_retry_requires_at_least_one_attempt() -> None:
    with pytest.raises(ValueError):
        retry_on_api_error(attempts=0)


def test_async_retry_retries_a_transient_failure_then_succeeds() -> None:
    calls = {"count": 0}

    @async_retry_on_api_error(attempts=3, delay_seconds=0)
    async def flaky() -> str:
        calls["count"] += 1
        if calls["count"] < 2:
            raise GroqAPIError("rate limited", status_code=429)
        return "ok"

    assert asyncio.run(flaky()) == "ok"
    assert calls["count"] == 2


def test_async_retry_does_not_retry_a_permanent_failure() -> None:
    calls = {"count": 0}

    @async_retry_on_api_error(attempts=3, delay_seconds=0)
    async def unauthorized() -> None:
        calls["count"] += 1
        raise GroqAPIError("bad key", status_code=401)

    with pytest.raises(GroqAPIError):
        asyncio.run(unauthorized())

    assert calls["count"] == 1
