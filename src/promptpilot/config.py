"""Cross-platform configuration and file-path management."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from promptpilot.constants import (
    APP_NAME,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT_SECONDS,
    ENV_API_KEY,
    ENV_MODEL,
    ENV_TIMEOUT_SECONDS,
)
from promptpilot.exceptions import ConfigurationError
from promptpilot.schemas import AppConfig


class ConfigStore:
    """Read and write application configuration as a JSON file."""

    def __init__(self, path: Path | None = None) -> None:
        load_dotenv()
        self.path = path or self.default_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def default_path() -> Path:
        """Choose an OS-appropriate per-user application directory."""
        if sys.platform == "win32":
            root = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif sys.platform == "darwin":
            root = Path.home() / "Library" / "Application Support"
        else:
            root = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
        return root / APP_NAME.lower() / "config.json"

    def stats_path(self) -> Path:
        """Return the JSONL statistics file that lives beside the config file."""
        return self.path.with_name("stats.jsonl")

    def load(self) -> AppConfig:
        """Load valid JSON, or create a default configuration."""
        if not self.path.exists():
            return self.default_config()
        try:
            with self.path.open("r", encoding="utf-8") as file:
                return AppConfig.model_validate_json(file.read())
        except (OSError, json.JSONDecodeError, ValueError) as error:
            raise ConfigurationError(f"could not read {self.path}: {error}") from error

    def save(self, config: AppConfig) -> AppConfig:
        """Persist configuration through a file object."""
        try:
            with self.path.open("w", encoding="utf-8") as file:
                file.write(config.model_dump_json(indent=2))
                file.write("\n")
        except OSError as error:
            raise ConfigurationError(f"could not write {self.path}: {error}") from error
        return config

    @staticmethod
    def default_config() -> AppConfig:
        """Build a configuration from environment variables and defaults."""
        raw_timeout = os.getenv(ENV_TIMEOUT_SECONDS, str(DEFAULT_TIMEOUT_SECONDS))
        try:
            timeout = float(raw_timeout)
        except ValueError as error:
            raise ConfigurationError("timeout must be numeric") from error
        return AppConfig(
            model=os.getenv(ENV_MODEL, DEFAULT_MODEL),
            timeout_seconds=timeout,
        )

    def user_api_key(self) -> str | None:
        """Return a user key from the saved config or the environment."""
        config = self.load()
        return config.api_key or os.getenv(ENV_API_KEY)

    def api_key_source(self) -> str:
        """Describe where the active API key comes from."""
        if self.load().api_key:
            return "config file"
        if os.getenv(ENV_API_KEY):
            return f"environment ({ENV_API_KEY})"
        return "not configured"

    def has_api_key(self) -> bool:
        """Report whether a usable API key is available."""
        return bool(self.user_api_key())


__all__ = ["ConfigStore"]
