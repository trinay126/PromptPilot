"""Shared pytest fixtures."""

from pathlib import Path

import pytest

from promptpilot.config import ConfigStore
from promptpilot.schemas import AppConfig
from promptpilot.services import PromptPilotService
from promptpilot.stores import StatsStore

# The real implementation, captured before the autouse fixture replaces it.
REAL_DEFAULT_PATH = ConfigStore.default_path


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove inherited Groq keys so tests never touch a real account."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def isolated_config(
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Keep every test away from the real user configuration.

    Without this, a test that builds a service without injecting a config
    store would read (and write) the key and statistics of whoever is running
    the suite, and could send real requests to Groq.
    """
    sandbox = tmp_path_factory.mktemp("user-config")
    monkeypatch.setattr(
        ConfigStore,
        "default_path",
        staticmethod(lambda: sandbox / "config.json"),
    )
    return sandbox


@pytest.fixture(autouse=True)
def no_outbound_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail loudly if a test ever tries to reach the real Groq API.

    The suite is meant to be hermetic: it mocks the HTTPX transport. A test
    that slipped past that would spend the developer's own quota, so make it
    an error rather than a silent request.
    """
    import socket

    def blocked(self, address):
        raise AssertionError(
            f"A test tried to open a network connection to {address!r}. "
            "Mock the transport with respx instead."
        )

    # respx answers requests without ever opening a socket, so guarding the
    # socket layer catches real network traffic without interfering with it.
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)


@pytest.fixture
def real_default_path():
    """The unpatched `ConfigStore.default_path`, for platform tests."""
    return REAL_DEFAULT_PATH


@pytest.fixture
def config_store(tmp_path: Path) -> ConfigStore:
    """Use an isolated JSON config for every test."""
    return ConfigStore(tmp_path / "config.json")


@pytest.fixture
def stats_store(tmp_path: Path) -> StatsStore:
    """Use an isolated JSONL statistics file for every test."""
    return StatsStore(tmp_path / "stats.jsonl")


@pytest.fixture
def service(
    tmp_path: Path, config_store: ConfigStore, stats_store: StatsStore
) -> PromptPilotService:
    """Build a service whose config and JSONL stats stay under pytest's temp path."""
    config_store.save(AppConfig(model="test-model"))
    return PromptPilotService(config_store, stats_store)
