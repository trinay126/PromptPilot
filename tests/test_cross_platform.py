"""Tests that guard Linux, macOS, and Windows behaviour."""

import sys
from pathlib import Path

import pytest

from promptpilot.config import ConfigStore
from promptpilot.schemas import AppConfig


def test_windows_config_path_uses_appdata(
    monkeypatch: pytest.MonkeyPatch, real_default_path
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", r"C:\Users\trinay\AppData\Roaming")

    path = real_default_path()

    assert path.name == "config.json"
    assert path.parent.name == "promptpilot"
    assert "AppData" in str(path)


def test_macos_config_path_uses_application_support(
    monkeypatch: pytest.MonkeyPatch, real_default_path
) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")

    path = real_default_path()

    assert path.parent.name == "promptpilot"
    assert "Application Support" in str(path)


def test_linux_config_path_follows_xdg(
    monkeypatch: pytest.MonkeyPatch, real_default_path
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/xdg-config")

    path = real_default_path()

    assert path == Path("/tmp/xdg-config/promptpilot/config.json")


def test_linux_config_path_defaults_to_dot_config(
    monkeypatch: pytest.MonkeyPatch, real_default_path
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    path = real_default_path()

    assert path.parent.parent.name == ".config"
    assert path.parent.name == "promptpilot"


def test_picker_is_unavailable_without_termios(monkeypatch: pytest.MonkeyPatch) -> None:
    """Windows has no termios, so the picker must report itself unavailable."""
    import builtins

    from promptpilot import picker

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in {"termios", "tty"}:
            raise ImportError(f"No module named {name!r}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    assert picker.picker_available() is False


def test_api_key_persists_across_store_instances(tmp_path: Path) -> None:
    """A key written once is still there for the next process."""
    path = tmp_path / "config.json"
    ConfigStore(path).save(AppConfig(api_key="gsk_persisted_key"))

    reloaded = ConfigStore(path).load()

    assert reloaded.api_key == "gsk_persisted_key"
    assert reloaded.has_api_key is True


def test_saved_key_wins_over_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "key-from-environment")
    store = ConfigStore(tmp_path / "config.json")
    store.save(AppConfig(api_key="key-from-config"))

    assert store.user_api_key() == "key-from-config"
    assert store.api_key_source() == "config file"


def test_environment_key_is_used_when_nothing_is_saved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "key-from-environment")
    store = ConfigStore(tmp_path / "config.json")

    assert store.user_api_key() == "key-from-environment"
    assert store.api_key_source() == "environment (GROQ_API_KEY)"


def test_config_file_is_written_as_readable_json(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    ConfigStore(path).save(AppConfig(model="saved-model", api_key="gsk_key"))

    raw = path.read_text(encoding="utf-8")

    assert raw.endswith("\n")
    assert '"model": "saved-model"' in raw


def test_config_directory_is_created(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "deeper" / "config.json"

    ConfigStore(path)

    assert path.parent.is_dir()


def test_running_with_no_arguments_shows_help_and_succeeds() -> None:
    from typer.testing import CliRunner

    from promptpilot.cli import app

    result = CliRunner().invoke(app, [])

    assert result.exit_code == 0
    assert "Usage" in result.output
