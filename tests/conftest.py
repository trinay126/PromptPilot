"""Shared pytest fixtures."""

from pathlib import Path

import pytest

from promptpilot.config import ConfigStore
from promptpilot.schemas import AppConfig
from promptpilot.services import PromptPilotService
from promptpilot.stores import StatsStore


@pytest.fixture
def config_store(tmp_path: Path) -> ConfigStore:
    """Use an isolated JSON config for every test."""
    return ConfigStore(tmp_path / "config.json")


@pytest.fixture
def service(tmp_path: Path) -> PromptPilotService:
    """Build a service whose config and JSONL stats stay under pytest's temp path."""
    config_path = tmp_path / "config.json"
    store = ConfigStore(config_path)
    store.save(AppConfig(model="test-model", demo_limit=10))
    return PromptPilotService(store, StatsStore(tmp_path / "stats.jsonl"))
