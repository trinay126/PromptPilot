"""Resuable decorators for timing and bounded retry behaviour."""

from __future__ import annotations

import asyncio
import functools
import time
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from promptpilot.exceptions import GroqAPIError

P = ParamSpec("P")
R = TypeVar("R")

def timed(function: Callable[P, R]) -> Callable[P, R]:
    """Attach the most recent duration to a callable without changing its API."""

    @functools.wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        started = time.perf_counter()
        try:
            return function(*args, **kwargs)
        finally:
            elapsed_ms = (time.perf_counter()- started) * 1000
            setattr(wrapper, "last_duration_ms", round(elapsed_ms, 2))

    setattr(wrapper, "last_duration_ms", 0.0)
    return wrapper

def retry_on_api_error(attempts: int = 3, delay_seconds: float = 0.5) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Retry transient API errors while preserving the final exception."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    def decorator(function: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_error: GroqAPIError | None = None
            for attempt in range(attempts):
                try:
                    return function(*args, **kwargs)
                except GroqAPIError as error:
                    last_error = error
                    if error.status_code not in {408, 429, 500, 502, 503, 504}:
                        raise
                    if attempt + 1 < attempts:
                        time.sleep(delay_seconds * (attempt + 1))

            assert last_error is not None
            raise last_error
        return wrapper
    return decorator


