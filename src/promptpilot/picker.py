"""Interactive terminal picker for choosing a model from the live catalog."""

from __future__ import annotations

import os
import select
import sys
from collections.abc import Sequence

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from promptpilot.schemas import ModelInfo

KEY_UP = "up"
KEY_DOWN = "down"
KEY_ENTER = "enter"
KEY_BACKSPACE = "backspace"
KEY_ESCAPE = "escape"
KEY_IGNORE = "ignore"

_ESCAPE = "\x1b"
_ARROW_UP = "[A"
_ARROW_DOWN = "[B"
_CTRL_C = "\x03"
_CTRL_D = "\x04"
_BACKSPACE = ("\x7f", "\b")
_ENTER = ("\r", "\n")

MAX_VISIBLE = 14


def group_by_owner(models: Sequence[ModelInfo]) -> list[tuple[str, list[ModelInfo]]]:
    """Group models by their owner, keeping the groups in alphabetical order."""
    grouped: dict[str, list[ModelInfo]] = {}
    for model in models:
        owner = model.owned_by or "unknown"
        grouped.setdefault(owner, []).append(model)
    return [(owner, sorted(grouped[owner], key=lambda item: item.id)) for owner in sorted(grouped)]


def filter_models(
    groups: Sequence[tuple[str, list[ModelInfo]]], query: str
) -> list[ModelInfo]:
    """Return the models whose id contains every word of the query."""
    words = [word.lower() for word in query.split() if word]
    if not words:
        return [model for _, group in groups for model in group]
    matches = []
    for _, group in groups:
        for model in group:
            haystack = model.id.lower()
            if all(word in haystack for word in words):
                matches.append(model)
    return matches


def _read_key(fd: int) -> str:
    """Read a single key press, decoding arrow-key escape sequences."""
    try:
        char = os.read(fd, 1).decode("utf-8", "replace")
    except OSError:
        return KEY_IGNORE

    if char == _ESCAPE:
        sequence = ""
        while len(sequence) < 2 and select.select([fd], [], [], 0.05)[0]:
            sequence += os.read(fd, 1).decode("utf-8", "replace")
        if sequence == _ARROW_UP:
            return KEY_UP
        if sequence == _ARROW_DOWN:
            return KEY_DOWN
        return KEY_ESCAPE
    if char in _BACKSPACE:
        return KEY_BACKSPACE
    if char in _ENTER:
        return KEY_ENTER
    if char == _CTRL_C:
        raise KeyboardInterrupt
    if char == _CTRL_D:
        return KEY_ESCAPE
    if char.isprintable():
        return char
    return KEY_IGNORE


def _render(
    groups: Sequence[tuple[str, list[ModelInfo]]],
    visible: Sequence[ModelInfo],
    selected: int,
    query: str,
    active: str | None,
) -> Panel:
    """Build the picker panel for the current state."""
    table = Table.grid(padding=(0, 1))
    table.add_column(width=1, no_wrap=True)
    table.add_column(overflow="ellipsis")
    table.add_column(justify="right", no_wrap=True)

    visible_ids = {model.id for model in visible}
    for owner, group in groups:
        owned = [model for model in group if model.id in visible_ids]
        if not owned:
            continue
        table.add_row(Text(""), Text(owner, style="bold cyan"), Text(""))
        for model in owned:
            index = visible.index(model)
            is_cursor = index == selected
            is_active = model.id == active
            cursor = Text("▸", style="bold green") if is_cursor else Text(" ")
            label = Text(f"  {model.id}", style="bold white" if is_cursor else "white")
            marker = Text("current", style="dim green") if is_active else Text("")
            table.add_row(cursor, label, marker)

    if not visible:
        table.add_row(Text(" "), Text(f"No model matches {query!r}", style="dim red"), Text(""))

    body = Text()
    body.append("  Search: ", style="dim")
    body.append(query if query else "type to filter")
    body.append("   ")
    body.append(f"{len(visible)} shown", style="dim")
    body.append("\n")
    body.append(
        "  ↑/↓ move   enter select   esc cancel   backspace delete",
        style="dim",
    )

    content = Table.grid()
    content.add_row(body)
    content.add_row(Text())
    content.add_row(table)
    return Panel(
        content,
        title="[bold cyan]Select a model[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    )


def picker_available() -> bool:
    """Report whether this terminal can drive the interactive picker."""
    try:
        import termios  # noqa: F401
        import tty  # noqa: F401
    except ImportError:  # pragma: no cover - Windows has no termios
        return False
    return bool(sys.stdin.isatty())


def pick_model(
    console: Console,
    models: Sequence[ModelInfo],
    active: str | None = None,
) -> str | None:
    """Open the interactive picker and return the chosen model id.

    Returns ``None`` when the user cancels. Check :func:`picker_available`
    first to decide whether the interactive picker can be used at all.
    """
    try:
        import termios
        import tty
    except ImportError:  # pragma: no cover - Windows has no termios
        return None

    if not sys.stdin.isatty():
        return None

    groups = group_by_owner(models)
    visible = filter_models(groups, "")
    query = ""
    selected = 0

    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        with Live(console=console, auto_refresh=False, transient=True) as live:
            while True:
                live.update(_render(groups, visible, selected, query, active))
                live.refresh()
                key = _read_key(fd)

                if key == KEY_UP:
                    if visible:
                        selected = (selected - 1) % len(visible)
                elif key == KEY_DOWN:
                    if visible:
                        selected = (selected + 1) % len(visible)
                elif key == KEY_BACKSPACE:
                    query = query[:-1]
                    visible = filter_models(groups, query)
                    selected = 0
                elif key == KEY_ESCAPE:
                    return None
                elif key == KEY_ENTER:
                    if visible:
                        return visible[selected].id
                    return None
                elif key != KEY_IGNORE:
                    query += key
                    visible = filter_models(groups, query)
                    selected = 0
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)
    return None


__all__ = [
    "KEY_BACKSPACE",
    "KEY_DOWN",
    "KEY_ENTER",
    "KEY_ESCAPE",
    "KEY_IGNORE",
    "KEY_UP",
    "filter_models",
    "group_by_owner",
    "pick_model",
    "picker_available",
]
