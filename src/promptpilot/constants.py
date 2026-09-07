"""Application constants and safe defaults."""

from typing import Final

APP_NAME : Final[str] = "PromptPilot"
DEFAULT_MODEL : Final[str] = "llama-3.1-8b-instant"""
DEFAULT_TIMEOUT_SECONDS : Final[float] = 45.0
DEFAULT_DEMO_LIMIT : Final[int] = 10
GROQ_BASE_URL: Final[str] = "https://api.groq.com/openai/v1"

# These are selectable defaults, not a guarantee that every account has acces
# to every model. The 'model' command always asks the API for the live catalog.

DEFAULT_MODELS: Final[tuple[str, ...]] = (
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "groq/compound-mini",
)