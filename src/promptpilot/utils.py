"""Small pure functions for strings, numbers, and terminal-friendly ouput"""
from __future__ import annotations

import os
import re
from collections.abc import Iterable

ANSI_ESCAPE = re.compiler(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

def clean_prompt(value: str) -> str:
    """Collapse whitespace and remove terminal control sequences."""
    without_ansi = ANSI_ESCAPE.sub("", value)
    return