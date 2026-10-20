"""Application constants and safe defaults."""

from typing import Final

APP_NAME: Final[str] = "PromptPilot"
APP_TAGLINE: Final[str] = "Groq AI command-line workbench"
DEFAULT_MODEL: Final[str] = "llama-3.1-8b-instant"
DEFAULT_TIMEOUT_SECONDS: Final[float] = 45.0
GROQ_BASE_URL: Final[str] = "https://api.groq.com/openai/v1"

# Request defaults shared by the sync client, the async client, and the CLI.
DEFAULT_SYSTEM_PROMPT: Final[str] = "You are PromptPilot, a concise and helpful assistant."
DEFAULT_TEMPERATURE: Final[float] = 0.2
DEFAULT_MAX_COMPLETION_TOKENS: Final[int] = 512

# These are selectable defaults, not a guarantee that every account has access
# to every model. The `models` command always asks the API for the live catalog.

DEFAULT_MODELS: Final[tuple[str, ...]] = (
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "groq/compound-mini",
)

# Environment variable names read by the configuration layer.
ENV_API_KEY: Final[str] = "GROQ_API_KEY"
ENV_MODEL: Final[str] = "PROMPTPILOT_MODEL"
ENV_TIMEOUT_SECONDS: Final[str] = "PROMPTPILOT_TIMEOUT_SECONDS"

# Shell completion support.
COMPLETE_ENV_VAR: Final[str] = "_PROMPTPILOT_COMPLETE"
SUPPORTED_SHELLS: Final[tuple[str, ...]] = ("bash", "zsh", "fish")

__all__ = [
    "APP_NAME",
    "APP_TAGLINE",
    "COMPLETE_ENV_VAR",
    "DEFAULT_MAX_COMPLETION_TOKENS",
    "DEFAULT_MODEL",
    "DEFAULT_MODELS",
    "DEFAULT_SYSTEM_PROMPT",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_TIMEOUT_SECONDS",
    "ENV_API_KEY",
    "ENV_MODEL",
    "ENV_TIMEOUT_SECONDS",
    "GROQ_BASE_URL",
    "SUPPORTED_SHELLS",
]
