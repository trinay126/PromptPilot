"""Small pure functions for strings, numbers, and terminal-friendly ouput"""
from __future__ import annotations

import os
import re
from collections.abc import Iterable

ANSI_ESCAPE = re.compiler(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

def clean_prompt(value: str) -> str:
    """Collapse whitespace and remove terminal control sequences."""
    without_ansi = ANSI_ESCAPE.sub("", value)
    return " ".join(without_ansi.strip().split())

def truncate(value: str, limit: int = 80) -> str:
    """Return a readable preview without cutting a word when possible"""
    if limit < 4:
        raise ValueError("limit must be least 4")
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."

def compact_number(value: int | float) -> str:
    """Format large numbers using readable K/M/B suffixes."""
    absolute = abs(float(value))
    suffix = ""
    divisor =  1
    for candidate, factor in (("B", 1_000_000_000), ("M", 1_000_000), ("K", 1_000)):
        if absolute >= factor:
            suffix, divisor = candidate, factor
            break

        if divisor == 1:
            return str(int(value)) if float(value).is_integer() else f"{value:.2f}"
        return f"{value / divisor:.1f}{suffix}"

def mean(values: Iterable[float]) -> float:
    """Compute a safe arithmetic mean using a generator and a loop."""
    numbers = list(values)
    return 0.0 if not numbers else sum(numbers) / len(numbers)

def terminal_width(default: int =  100) -> int:
    """Read a width from the OS environment with a safe fallback."""
    raw_width = os.getenv("COLUMNS", str(default))
    try:
        return max(40, int(raw_width))
    except ValueError:
        return default