"""Tests for the configuration store."""

import json
from pathlib import Path

import pytest

from promptpilot.config import ConfigStore
from promptpilot.exceptions import ConfigurationError
from promptpilot.schemas import AppConfig


def test_default_path_targets_a_per_user_directory() -> None:
    path = ConfigStore.default_path()

    assert path.name == "config.json"
    assert path.parent.name == "promptpilot"


def test_load_returns_defaults_when_the_file_is_missing(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")

    config = store.load()

    assert config.model
    assert config.demo_limit == 10


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
    monkeypatch.setenv("PROMPTPILOT_DEMO_LIMIT", "3")

    config = ConfigStore.default_config()

    assert config.model == "env-model"
    assert config.timeout_seconds == 12
    assert config.demo_limit == 3


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


def test_demo_api_key_reads_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROMPTPILOT_DEMO_API_KEY", "demo-key")

    assert ConfigStore.demo_api_key() == "demo-key"


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
    ConfigStore(path).save(AppConfig(model="round-trip", demo_limit=7))

    reloaded = ConfigStore(path).load()

    assert reloaded.model == "round-trip"
    assert reloaded.demo_limit == 7
