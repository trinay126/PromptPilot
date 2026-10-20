"""Tests for the interactive model picker."""

import pytest

from promptpilot.picker import filter_models, group_by_owner
from promptpilot.schemas import ModelInfo


def models() -> list[ModelInfo]:
    """Build a small catalog covering several owners."""
    return [
        ModelInfo(id="openai/gpt-oss-120b", owned_by="OpenAI"),
        ModelInfo(id="openai/gpt-oss-20b", owned_by="OpenAI"),
        ModelInfo(id="meta-llama/llama-3.3-70b-versatile", owned_by="Meta"),
        ModelInfo(id="canopylabs/orpheus-v1-english", owned_by="Canopy Labs"),
        ModelInfo(id="qwen/qwen3.8-27b", owned_by="Alibaba Cloud"),
    ]


def test_group_by_owner_sorts_owners_and_models() -> None:
    groups = group_by_owner(models())

    assert [owner for owner, _ in groups] == [
        "Alibaba Cloud",
        "Canopy Labs",
        "Meta",
        "OpenAI",
    ]
    openai = next(group for owner, group in groups if owner == "OpenAI")
    assert [model.id for model in openai] == [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
    ]


def test_group_by_owner_handles_a_missing_owner() -> None:
    groups = group_by_owner([ModelInfo(id="orphan-model")])

    assert groups[0][0] == "unknown"


def test_filter_models_with_an_empty_query_returns_everything() -> None:
    groups = group_by_owner(models())

    assert len(filter_models(groups, "")) == 5
    assert len(filter_models(groups, "   ")) == 5


def test_filter_models_matches_a_substring() -> None:
    groups = group_by_owner(models())

    matches = filter_models(groups, "gpt")

    assert [model.id for model in matches] == [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
    ]


def test_filter_models_is_case_insensitive() -> None:
    groups = group_by_owner(models())

    assert len(filter_models(groups, "GPT-OSS")) == 2


def test_filter_models_requires_every_word() -> None:
    groups = group_by_owner(models())

    assert filter_models(groups, "openai safeguard") == []
    assert len(filter_models(groups, "openai oss")) == 2


def test_filter_models_returns_nothing_for_a_non_match() -> None:
    groups = group_by_owner(models())

    assert filter_models(groups, "definitely-not-a-model") == []


def test_render_shows_every_group_and_the_current_model() -> None:
    from promptpilot.picker import _render

    groups = group_by_owner(models())
    visible = filter_models(groups, "")
    panel = _render(groups, visible, 0, "", "openai/gpt-oss-20b")

    rendered = _flatten(panel)
    assert "Alibaba Cloud" in rendered
    assert "OpenAI" in rendered
    assert "qwen/qwen3.8-27b" in rendered
    assert "current" in rendered


def test_render_reports_when_nothing_matches() -> None:
    from promptpilot.picker import _render

    groups = group_by_owner(models())
    panel = _render(groups, [], 0, "zzz", None)

    assert "No model matches" in _flatten(panel)


def _key_stream(data: bytes):
    """Return a readable file descriptor pre-loaded with `data`.

    A socket pair is used rather than a regular file because `select.select`
    only accepts sockets on Windows.
    """
    import socket

    reader, writer = socket.socketpair()
    writer.sendall(data)
    writer.close()
    return reader


def test_read_key_decodes_plain_characters() -> None:
    from promptpilot.picker import _read_key

    reader = _key_stream(b"x")
    try:
        assert _read_key(reader.fileno()) == "x"
    finally:
        reader.close()


def test_read_key_decodes_arrow_keys() -> None:
    from promptpilot.picker import _read_key

    reader = _key_stream(b"\x1b[A")
    try:
        assert _read_key(reader.fileno()) == "up"
    finally:
        reader.close()


def test_read_key_decodes_backspace_and_enter() -> None:
    from promptpilot.picker import _read_key

    reader = _key_stream(b"\x7f")
    try:
        assert _read_key(reader.fileno()) == "backspace"
    finally:
        reader.close()

    reader = _key_stream(b"\r")
    try:
        assert _read_key(reader.fileno()) == "enter"
    finally:
        reader.close()


def test_read_key_raises_on_ctrl_c() -> None:
    import pytest

    from promptpilot.picker import _read_key

    reader = _key_stream(b"\x03")
    try:
        with pytest.raises(KeyboardInterrupt):
            _read_key(reader.fileno())
    finally:
        reader.close()


def test_read_key_treats_a_lone_escape_as_cancel() -> None:
    from promptpilot.picker import _read_key

    reader = _key_stream(b"\x1b")
    try:
        assert _read_key(reader.fileno()) == "escape"
    finally:
        reader.close()


def test_read_key_reports_eof_when_the_stream_closes() -> None:
    from promptpilot.picker import _read_key

    reader = _key_stream(b"")
    try:
        assert _read_key(reader.fileno()) == "eof"
    finally:
        reader.close()


def test_picker_available_is_false_without_a_terminal() -> None:
    from promptpilot.picker import picker_available

    assert picker_available() is False


def _flatten(panel) -> str:
    """Render a panel to plain text for assertions."""
    from rich.console import Console

    console = Console(width=120, force_terminal=False)
    with console.capture() as capture:
        console.print(panel)
    return capture.get()


class _FakeStdin:
    """Minimal stdin double that claims to be a terminal."""

    def isatty(self) -> bool:
        return True

    def fileno(self) -> int:
        return 0


def _drive_picker(monkeypatch, keys, models_list):
    """Run the picker with a scripted key sequence.

    The interactive picker needs a raw terminal, which only Unix-like systems
    provide, so these tests are skipped on Windows. The Windows fallback is
    covered by `test_picker_is_unavailable_without_termios`.
    """
    import io

    termios = pytest.importorskip("termios")
    tty = pytest.importorskip("tty")
    from rich.console import Console

    from promptpilot import picker

    pending = list(keys)
    monkeypatch.setattr(picker, "_read_key", lambda fd: pending.pop(0))
    monkeypatch.setattr(picker.sys, "stdin", _FakeStdin())
    monkeypatch.setattr(termios, "tcgetattr", lambda fd: [0, 0, 0, 0, 0, 0])
    monkeypatch.setattr(termios, "tcsetattr", lambda fd, when, attr: None)
    monkeypatch.setattr(tty, "setraw", lambda fd: None)

    console = Console(file=io.StringIO(), force_terminal=False, width=100)
    return picker.pick_model(console, models_list, active=None)



def test_pick_model_returns_the_highlighted_model(monkeypatch) -> None:
    """The picker returns the model under the cursor when enter is pressed."""
    chosen = _drive_picker(monkeypatch, ["down", "enter"], models())

    # Groups are ordered by owner, so index 1 is the Canopy Labs model.
    assert chosen == "canopylabs/orpheus-v1-english"


def test_pick_model_returns_none_when_cancelled(monkeypatch) -> None:
    assert _drive_picker(monkeypatch, ["escape"], models()) is None


def test_pick_model_filters_as_you_type(monkeypatch) -> None:
    chosen = _drive_picker(monkeypatch, ["g", "p", "t", "enter"], models())

    assert chosen == "openai/gpt-oss-120b"


def test_pick_model_backspace_widens_the_filter(monkeypatch) -> None:
    chosen = _drive_picker(monkeypatch, ["g", "p", "t", "backspace", "enter"], models())

    assert chosen == "openai/gpt-oss-120b"


def test_pick_model_wraps_around_the_list(monkeypatch) -> None:
    chosen = _drive_picker(monkeypatch, ["up", "enter"], models())

    # Moving up from the first item wraps around to the last one.
    assert chosen == "openai/gpt-oss-20b"


def test_pick_model_returns_none_without_a_terminal(monkeypatch) -> None:
    from promptpilot import picker

    class _NoTty:
        def isatty(self) -> bool:
            return False

    monkeypatch.setattr(picker.sys, "stdin", _NoTty())

    import io

    from rich.console import Console

    console = Console(file=io.StringIO(), force_terminal=False, width=100)
    assert picker.pick_model(console, models(), active=None) is None
