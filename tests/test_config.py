"""Tests for the configuration store."""

import json
from pathlib import Path

import pytest

from promptpilot.config import ConfigStore
from promptpilot.exceptions import ConfigurationError
from promptpilot.schemas import AppConfig


def test_default_path_targets_a_per_user_directory(real_default_path) -> None:
    path = real_default_path()

    assert path.name == "config.json"
    assert path.parent.name == "promptpilot"


def test_load_returns_defaults_when_the_file_is_missing(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")

    config = store.load()

    assert config.model
    assert config.timeout_seconds > 0
    assert config.api_key is None


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    store.save(AppConfig(model="saved-model", api_key="gsk_live_key_value"))

    loaded = ConfigStore(tmp_path / "config.json").load()

    assert loaded.model == "saved-model"
    assert loaded.api_key == "gsk_live_key_value"


def test_save_writes_readable_json(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    ConfigStore(path).save(AppConfig(model="saved-model"))

    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["model"] == "saved-model"


def test_load_rejects_a_corrupt_file(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(ConfigurationError):
        ConfigStore(path).load()


def test_default_config_reads_environment_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROMPTPILOT_MODEL", "env-model")
    monkeypatch.setenv("PROMPTPILOT_TIMEOUT_SECONDS", "12")

    config = ConfigStore.default_config()

    assert config.model == "env-model"
    assert config.timeout_seconds == 12


def test_default_config_rejects_a_non_numeric_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROMPTPILOT_TIMEOUT_SECONDS", "soon")

    with pytest.raises(ConfigurationError):
        ConfigStore.default_config()


def test_user_api_key_prefers_the_saved_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "env-key")
    store = ConfigStore(tmp_path / "config.json")
    store.save(AppConfig(api_key="saved-key"))

    assert store.user_api_key() == "saved-key"


def test_user_api_key_falls_back_to_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "env-key")
    store = ConfigStore(tmp_path / "config.json")

    assert store.user_api_key() == "env-key"


def test_api_key_source_reports_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "env-key")
    store = ConfigStore(tmp_path / "config.json")

    assert store.api_key_source() == "environment (GROQ_API_KEY)"
    assert store.has_api_key() is True


def test_api_key_source_reports_a_missing_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    store = ConfigStore(tmp_path / "config.json")

    assert store.api_key_source() == "not configured"
    assert store.has_api_key() is False


def test_stats_path_sits_beside_the_config_file(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")

    assert store.stats_path() == tmp_path / "stats.jsonl"


def test_store_creates_the_parent_directory(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "deeper" / "config.json"

    ConfigStore(path)

    assert path.parent.is_dir()


def test_load_rejects_a_file_with_the_wrong_shape(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text('{"timeout_seconds": "soon"}', encoding="utf-8")

    with pytest.raises(ConfigurationError):
        ConfigStore(path).load()


def test_saved_config_round_trips_through_a_new_store(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    ConfigStore(path).save(AppConfig(model="round-trip", timeout_seconds=7.0))

    reloaded = ConfigStore(path).load()

    assert reloaded.model == "round-trip"
    assert reloaded.timeout_seconds == 7.0


def test_dotenv_file_is_loaded_from_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A .env in the current directory is honoured, as a user would expect."""
    (tmp_path / ".env").write_text(
        "GROQ_API_KEY=gsk_from_dotenv_file\nPROMPTPILOT_MODEL=env-file-model\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    store = ConfigStore(tmp_path / "config.json")

    assert store.user_api_key() == "gsk_from_dotenv_file"
    assert store.load().model == "env-file-model"
