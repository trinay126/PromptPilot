"""Shared pytest fixtures."""

from pathlib import Path

import pytest

from promptpilot.config import ConfigStore
from promptpilot.schemas import AppConfig
from promptpilot.services import PromptPilotService
from promptpilot.stores import StatsStore


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove inherited Groq keys so tests never touch a real account."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("PROMPTPILOT_DEMO_API_KEY", raising=False)


@pytest.fixture
def config_store(tmp_path: Path) -> ConfigStore:
    """Use an isolated JSON config for every test."""
    return ConfigStore(tmp_path / "config.json")


@pytest.fixture
def stats_store(tmp_path: Path) -> StatsStore:
    """Use an isolated JSONL statistics file for every test."""
    return StatsStore(tmp_path / "stats.jsonl")


@pytest.fixture
def service(tmp_path: Path, config_store: ConfigStore, stats_store: StatsStore) -> PromptPilotService:
    """Build a service whose config and JSONL stats stay under pytest's temp path."""
    config_store.save(AppConfig(model="test-model", demo_limit=10))
    return PromptPilotService(config_store, stats_store)
