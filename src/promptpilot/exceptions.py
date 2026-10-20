"""Domain-specific exceptions used to keep CLI error handling readable."""

RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({408, 429, 500, 502, 503, 504})


class PromptPilotError(Exception):
    """Base class for expected application errors."""


class ConfigurationError(PromptPilotError):
    """Raised when configuration is missing or invalid."""


class QuotaExceededError(PromptPilotError):
    """Raised when the demo prompt allowance has been consumed."""


class GroqAPIError(PromptPilotError):
    """Raised when the remote API rejects a request or returns bad JSON."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code

    @property
    def is_retryable(self) -> bool:
        """Report whether the failure looks transient enough to retry."""
        return self.status_code in RETRYABLE_STATUS_CODES


class SchemaError(PromptPilotError):
    """Raised when a remote response does not match the expected schema."""


__all__ = [
    "RETRYABLE_STATUS_CODES",
    "ConfigurationError",
    "GroqAPIError",
    "PromptPilotError",
    "QuotaExceededError",
    "SchemaError",
]
