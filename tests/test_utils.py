"""Tests for the small pure helper functions."""

import pytest

from promptpilot.utils import (
    clean_prompt,
    compact_number,
    format_latency,
    mask_secret,
    mean,
    terminal_width,
    truncate,
)


def test_clean_prompt_collapses_whitespace() -> None:
    assert clean_prompt("  hello   \n  world  ") == "hello world"


def test_clean_prompt_removes_terminal_control_sequences() -> None:
    assert clean_prompt("\x1b[31mred\x1b[0m text") == "red text"


def test_truncate_keeps_short_values_intact() -> None:
    assert truncate("short", limit=80) == "short"


def test_truncate_adds_an_ellipsis() -> None:
    assert truncate("a" * 100, limit=10) == "aaaaaaa..."


def test_truncate_requires_a_sensible_limit() -> None:
    with pytest.raises(ValueError):
        truncate("value", limit=3)


def test_mask_secret_hides_the_middle_of_a_key() -> None:
    assert mask_secret("gsk_abcdefghijklmnop") == "gsk_...mnop"


def test_mask_secret_masks_short_values_completely() -> None:
    assert mask_secret("short") == "*****"


def test_mask_secret_reports_a_missing_key() -> None:
    assert mask_secret(None) == "not configured"
    assert mask_secret("") == "not configured"


def test_compact_number_uses_suffixes() -> None:
    assert compact_number(999) == "999"
    assert compact_number(1_500) == "1.5K"
    assert compact_number(2_000_000) == "2.0M"
    assert compact_number(3_000_000_000) == "3.0B"


def test_compact_number_handles_fractions() -> None:
    assert compact_number(12.5) == "12.50"


def test_mean_of_an_empty_iterable_is_zero() -> None:
    assert mean([]) == 0.0


def test_mean_computes_the_arithmetic_average() -> None:
    assert mean([1, 2, 3, 4]) == 2.5


def test_mean_accepts_a_generator() -> None:
    assert mean(value for value in (2, 4)) == 3.0


def test_terminal_width_uses_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLUMNS", "120")

    assert terminal_width() == 120


def test_terminal_width_falls_back_when_the_value_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COLUMNS", "wide")

    assert terminal_width(default=90) == 90


def test_terminal_width_never_goes_below_forty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLUMNS", "10")

    assert terminal_width() == 40


def test_format_latency_renders_milliseconds() -> None:
    assert format_latency(12.345) == "12.35 ms"
